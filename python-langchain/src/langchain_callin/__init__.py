"""LangChain integration for Callin.io phone calls."""
from __future__ import annotations

import json
from typing import Any, List, Optional, Type

from callin import Callin
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["CallinPlaceCall", "CallinGetCallResult", "CallinListRecentCalls", "CallinToolkit"]


class _PlaceCallInput(BaseModel):
    to: str = Field(description="Phone number in E.164 format, e.g. +390111234567.")
    objective: str = Field(description="What the call must achieve, e.g. 'Book a table for 2 tomorrow at 20:30 under the name Rossi'.")
    context: str = Field(default="", description="Facts the caller may share: names, order numbers, callback number.")
    language: str = Field(default="", description="Language code for the call, e.g. 'it', 'es', 'pt', 'en'.")


class _CampaignInput(BaseModel):
    campaign_id: str = Field(description="The campaign_id returned by callin_place_call.")


class _ListInput(BaseModel):
    limit: int = Field(default=10, description="How many recent calls to return.")


class _CallinTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: Optional[Any] = None  # a callin.Callin instance

    def _c(self) -> Callin:
        if self.client is None:
            self.client = Callin()  # reads CALLIN_API_KEY and CALLIN_AGENT_ID
        return self.client


class CallinPlaceCall(_CallinTool):
    """Place a real outbound phone call with a Callin.io AI voice agent."""

    name: str = "callin_place_call"
    description: str = (
        "Place a real phone call with an AI voice agent that pursues an objective "
        "(book, confirm, ask, remind). Asynchronous: returns JSON with campaign_id; "
        "then use callin_get_call_result. The voice agent always discloses it is an AI."
    )
    args_schema: Type[BaseModel] = _PlaceCallInput

    def _run(self, to: str, objective: str, context: str = "", language: str = "", run_manager=None) -> str:
        return json.dumps(self._c().place_call(to=to, objective=objective, context=context, language=language).to_dict())


class CallinGetCallResult(_CallinTool):
    """Read status, summary and transcript of a call placed with CallinPlaceCall."""

    name: str = "callin_get_call_result"
    description: str = "Get the status of a call placed with callin_place_call and, once finished, its summary and transcript (JSON)."
    args_schema: Type[BaseModel] = _CampaignInput

    def _run(self, campaign_id: str, run_manager=None) -> str:
        return json.dumps(self._c().get_call_result(campaign_id).to_dict())


class CallinListRecentCalls(_CallinTool):
    """List recent calls handled by your Callin.io voice agents."""

    name: str = "callin_list_recent_calls"
    description: str = "List recent calls handled by your Callin.io voice agents, with summaries (JSON)."
    args_schema: Type[BaseModel] = _ListInput

    def _run(self, limit: int = 10, run_manager=None) -> str:
        return json.dumps(self._c().list_conversations(page_size=limit))


class CallinToolkit(BaseToolkit):
    """All Callin.io tools in one toolkit."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: Optional[Any] = None  # a callin.Callin instance

    def get_tools(self) -> List[BaseTool]:
        return [CallinPlaceCall(client=self.client), CallinGetCallResult(client=self.client), CallinListRecentCalls(client=self.client)]
