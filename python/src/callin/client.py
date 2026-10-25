"""Minimal client for the Callin.io public API (https://support.callin.io/api-reference/introduction).

Phone calls are placed through a Callin.io voice agent that has a phone number.
`place_call` creates a one-contact campaign for that agent and passes the call goal
as dynamic variables (`objective`, `context`, ...), which the agent's prompt uses.
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_BASE_URL = "https://api.callin.io/api"
FINAL_STATUSES = {"completed", "done", "ended", "failed", "no-answer", "no_answer", "busy", "voicemail", "canceled", "cancelled", "error"}


class CallinError(RuntimeError):
    """Raised when the Callin.io API returns an error."""

    def __init__(self, message: str, status: Optional[int] = None, details: Any = None):
        super().__init__(message)
        self.status = status
        self.details = details


@dataclass
class CallResult:
    """Outcome of a phone call placed with `Callin.place_call`."""

    campaign_id: str
    status: str
    finished: bool
    to: str
    call_id: Optional[str] = None
    conversation_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    voicemail: Optional[bool] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items() if k != "raw"}
        return d


class Callin:
    """Client for the Callin.io public API.

    Args:
        api_key: Callin.io API key. Defaults to the ``CALLIN_API_KEY`` environment variable.
        agent_id: Default voice agent used by :meth:`place_call`. Defaults to ``CALLIN_AGENT_ID``.
        base_url: API base URL.
    """

    def __init__(self, api_key: Optional[str] = None, agent_id: Optional[str] = None,
                 base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("CALLIN_API_KEY")
        if not self.api_key:
            raise CallinError("Missing API key: pass api_key= or set CALLIN_API_KEY")
        self.agent_id = agent_id or os.environ.get("CALLIN_AGENT_ID")
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout,
                                  headers={"x-api-key": self.api_key, "user-agent": "callin-python/0.1.0"})

    # ---- low level -------------------------------------------------------
    def _request(self, method: str, path: str, **kw) -> Any:
        r = self._http.request(method, path, **kw)
        try:
            body = r.json()
        except ValueError:
            raise CallinError(f"HTTP {r.status_code}: {r.text[:200]}", r.status_code)
        if r.status_code >= 400 or body.get("success") is False:
            err = body.get("error") or {}
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise CallinError(msg or f"HTTP {r.status_code}", r.status_code, body)
        return body.get("data", body)

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- account & agents ------------------------------------------------
    def me(self) -> Dict[str, Any]:
        """Return the user id and email of the API key's account."""
        return self._request("GET", "/public/v1/me")

    def list_agents(self, search: Optional[str] = None, page_size: int = 20) -> List[Dict[str, Any]]:
        params = {"pageSize": page_size}
        if search:
            params["search"] = search
        return self._request("GET", "/public/v1/agents", params=params)

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/public/v1/agents/{agent_id}")

    # ---- conversations ---------------------------------------------------
    def list_conversations(self, agent_id: Optional[str] = None, page_size: int = 20,
                           start_after_unix: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"pageSize": page_size}
        if agent_id:
            params["agentId"] = agent_id
        if start_after_unix:
            params["startAfterUnix"] = start_after_unix
        if status:
            params["status"] = status
        return self._request("GET", "/public/v1/conversations", params=params)

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/public/v1/conversations/{conversation_id}")

    # ---- phone calls -----------------------------------------------------
    def place_call(self, to: str, objective: str, *, context: str = "", language: str = "",
                   agent_id: Optional[str] = None, contact_name: str = "",
                   variables: Optional[Dict[str, Any]] = None, wait: bool = False,
                   timeout_seconds: int = 600, poll_seconds: int = 10) -> CallResult:
        """Place a phone call to ``to`` (E.164, e.g. "+390111234567") with a goal.

        The goal and context are passed to the voice agent as dynamic variables
        ``objective``, ``context`` and ``language``. Use an agent whose prompt
        includes ``{{objective}}`` and ``{{context}}`` (see the "Task Caller" template).

        With ``wait=True`` the method blocks until the call ends and returns the
        summary and transcript; otherwise call :meth:`get_call_result` later.
        """
        agent = agent_id or self.agent_id
        if not agent:
            raise CallinError("Missing agent: pass agent_id= or set CALLIN_AGENT_ID")
        if not to.startswith("+"):
            raise CallinError("Phone number must be in E.164 format, e.g. +390111234567")
        contact: Dict[str, Any] = {"phoneNumber": to, "objective": objective}
        if contact_name:
            contact["name"] = contact_name
        if context:
            contact["context"] = context
        if language:
            contact["language"] = language
        for k, v in (variables or {}).items():
            contact[k] = v
        name = f"agent-call {time.strftime('%Y-%m-%d %H:%M:%S')} {uuid.uuid4().hex[:6]}"
        camp = self._request("POST", "/public/v1/campaigns",
                             json={"name": name, "agentId": agent, "contacts": [contact], "launch": True})
        result = CallResult(campaign_id=camp.get("campaignId"), status=camp.get("status") or "queued",
                            finished=False, to=to, raw={"campaign": camp})
        if wait:
            return self.wait_for_call(result.campaign_id, timeout_seconds=timeout_seconds, poll_seconds=poll_seconds)
        return result

    def get_call_result(self, campaign_id: str) -> CallResult:
        """Return the current status and, once finished, the summary and transcript of a call."""
        camp = self._request("GET", f"/public/v1/campaigns/{campaign_id}")
        calls = self._request("GET", f"/public/v1/campaigns/{campaign_id}/calls", params={"pageSize": 5})
        to = ""
        contacts = camp.get("contacts") or []
        if contacts:
            to = contacts[0].get("phoneNumber", "")
        if not calls:
            cstatus = (camp.get("status") or "queued").lower()
            res = CallResult(campaign_id=campaign_id, status=cstatus, finished=cstatus in FINAL_STATUSES,
                             to=to, raw={"campaign": camp})
            if res.finished:
                created = (camp.get("metadata") or {}).get("createdAt")
                conv = self._find_conversation(camp.get("agentId"), {"contactNumber": to, "startedAt": created})
                if conv:
                    self._fill(res, conv)
            return res
        call = calls[0]
        status = (call.get("status") or "").lower() or "in_progress"
        res = CallResult(campaign_id=campaign_id, status=status, finished=status in FINAL_STATUSES, to=to,
                         call_id=call.get("callId"), duration_seconds=call.get("durationSeconds"),
                         error=call.get("errorMessage") or None, raw={"campaign": camp, "call": call})
        if res.finished:
            conv = self._find_conversation(camp.get("agentId"), call)
            if conv:
                self._fill(res, conv)
        return res

    @staticmethod
    def _fill(res: "CallResult", conv: Dict[str, Any]) -> None:
        res.conversation_id = conv.get("conversationId")
        res.summary = conv.get("summary")
        res.transcript = conv.get("transcript")
        res.voicemail = conv.get("voiceMailDetected")
        res.duration_seconds = res.duration_seconds or conv.get("conversationDuration")
        res.raw["conversation"] = conv

    def wait_for_call(self, campaign_id: str, timeout_seconds: int = 600, poll_seconds: int = 10) -> CallResult:
        deadline = time.time() + timeout_seconds
        res = self.get_call_result(campaign_id)
        while not res.finished and time.time() < deadline:
            time.sleep(poll_seconds)
            res = self.get_call_result(campaign_id)
        return res

    def _find_conversation(self, agent_id: Optional[str], call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        call_id = call.get("callId")
        if call_id:
            try:
                return self.get_conversation(call_id)
            except CallinError:
                pass
        started = call.get("startedAt")
        after = None
        if started:
            try:
                from datetime import datetime
                after = int(datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()) - 120
            except ValueError:
                after = None
        number = (call.get("contactNumber") or "").replace(" ", "")
        convs = self.list_conversations(agent_id=agent_id, page_size=20, start_after_unix=after)
        match = None
        if number:
            match = next((c for c in convs if number in (c.get("contactNumber") or "") or number in (c.get("callerNumber") or "")), None)
        if match is None and after:
            # A dedicated "task caller" agent places one call per campaign: take the first outbound call after launch.
            outbound = [c for c in convs if (c.get("direction") or "outbound") == "outbound" and (c.get("startTimeUnix") or 0) >= after]
            outbound.sort(key=lambda c: c.get("startTimeUnix") or 0)
            match = outbound[0] if outbound else None
        if match is None:
            return None
        try:
            return self.get_conversation(match["conversationId"])
        except CallinError:
            return match
