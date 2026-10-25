"""CrewAI tools for Callin.io. Install with: pip install "callin[crewai]"."""
from __future__ import annotations

import json
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .client import Callin


class _PlaceCallInput(BaseModel):
    to: str = Field(..., description="Phone number in E.164 format, e.g. +390111234567")
    objective: str = Field(..., description="What the call must achieve, in plain language")
    context: str = Field("", description="Facts the caller may share")
    language: str = Field("", description='Language code for the call, e.g. "it", "es", "pt", "en"')


class CallinPlaceCallTool(BaseTool):
    name: str = "callin_place_call"
    description: str = ("Place a real phone call with an AI voice agent that discloses it is an AI. "
                        "Returns campaign_id; use callin_get_call_result to read the outcome.")
    args_schema: Type[BaseModel] = _PlaceCallInput
    client: Optional[Callin] = None

    model_config = {"arbitrary_types_allowed": True}

    def _run(self, to: str, objective: str, context: str = "", language: str = "") -> str:
        c = self.client or Callin()
        return json.dumps(c.place_call(to=to, objective=objective, context=context, language=language).to_dict())


class _ResultInput(BaseModel):
    campaign_id: str = Field(..., description="campaign_id returned by callin_place_call")


class CallinGetCallResultTool(BaseTool):
    name: str = "callin_get_call_result"
    description: str = "Get the status, summary and transcript of a call placed with callin_place_call."
    args_schema: Type[BaseModel] = _ResultInput
    client: Optional[Callin] = None

    model_config = {"arbitrary_types_allowed": True}

    def _run(self, campaign_id: str) -> str:
        c = self.client or Callin()
        return json.dumps(c.get_call_result(campaign_id).to_dict())
