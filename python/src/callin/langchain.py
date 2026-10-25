"""LangChain tools for Callin.io. Install with: pip install "callin[langchain]"."""
from __future__ import annotations

import json
from typing import List, Optional

from langchain_core.tools import BaseTool, tool

from .client import Callin


def get_callin_tools(client: Optional[Callin] = None) -> List[BaseTool]:
    """Return LangChain tools that let an agent place phone calls and read results."""
    c = client or Callin()

    @tool("callin_place_call")
    def place_call(to: str, objective: str, context: str = "", language: str = "") -> str:
        """Place a real phone call with an AI voice agent.

        Args:
            to: Phone number in E.164 format, e.g. +390111234567.
            objective: What the call must achieve, in plain language
                (e.g. "Book a table for 2 tomorrow at 20:30 under the name Rossi").
            context: Facts the caller may share (names, order numbers, callback number).
            language: Language code for the call, e.g. "it", "es", "pt", "en".
        Returns a JSON string with campaign_id and status. The call is asynchronous:
        use callin_get_call_result with the campaign_id to read the outcome.
        The voice agent always discloses that it is an AI assistant.
        """
        r = c.place_call(to=to, objective=objective, context=context, language=language)
        return json.dumps(r.to_dict())

    @tool("callin_get_call_result")
    def get_call_result(campaign_id: str) -> str:
        """Get the status of a phone call placed with callin_place_call and, when it has
        finished, its summary and transcript. Returns a JSON string."""
        return json.dumps(c.get_call_result(campaign_id).to_dict())

    @tool("callin_list_recent_calls")
    def list_recent_calls(limit: int = 10) -> str:
        """List recent calls handled by your Callin.io voice agents, with summaries. Returns JSON."""
        return json.dumps(c.list_conversations(page_size=limit))

    return [place_call, get_call_result, list_recent_calls]
