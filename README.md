# Callin.io for AI agents

**Give your AI agent a real phone line.** Callin.io places phone calls with an AI voice agent and returns what happened: status, summary and transcript. Calls in Italian, Spanish, Portuguese, English, French, German, Dutch and Hindi, GDPR compliant, and every call discloses that it is an AI.

| Use it from | How |
|---|---|
| Claude, ChatGPT, Cursor, VS Code, OpenAI Agents SDK | MCP server `https://claude-mcp.callin.io/mcp` (OAuth) — registry name `io.callin/callin` |
| Python | `pip install callin` |
| LangChain | `pip install langchain-callin` → `from langchain_callin import CallinToolkit` (or `callin[langchain]`) |
| CrewAI | `pip install "callin[crewai]"` → `from callin.crewai import CallinPlaceCallTool` |
| Node.js | `npm i callin-sdk` |
| OpenClaw / Claude skills | [`skills/callin-phone/SKILL.md`](skills/callin-phone/SKILL.md) |
| n8n | community node `n8n-nodes-callin` |
| REST | [API reference](https://support.callin.io/api-reference/introduction) · [OpenAPI](https://support.callin.io/openapi.json) |
| Open voice-AI benchmark (IT/ES/PT) | [`benchmark/`](benchmark/) — method, scenarios, measurement scripts |

## Quickstart (Python)

```python
from callin import Callin  # env: CALLIN_API_KEY, CALLIN_AGENT_ID

result = Callin().place_call(
    "+390111234567",
    objective="Book a table for 2 tomorrow at 20:30 under the name Rossi",
    language="it",
    wait=True,
)
print(result.status, result.summary)
```

## Quickstart (Node)

```js
import { Callin } from "callin-sdk";
const callin = new Callin(); // env: CALLIN_API_KEY, CALLIN_AGENT_ID
const { campaignId } = await callin.placeCall({ to: "+34911234567", objective: "Ask for the first free appointment next week", language: "es" });
console.log(await callin.waitForCall(campaignId));
```

## How it works
1. Create a voice agent in [app.callin.io](https://app.callin.io) with a phone number, using the [Task Caller template](task-caller-agent/prompt.md). Its id is `CALLIN_AGENT_ID`.
2. `place_call` starts a one-contact campaign for that agent and passes `objective`, `context` and `language` as dynamic variables.
3. `get_call_result` / `wait_for_call` returns status, summary and transcript when the call ends.
   Summary and transcript are attached only when the conversation is linked to the call with certainty
   (`match`: `call_id`, or `contact_number` when exactly one outbound conversation of the agent reached that
   number after the launch). If the link is uncertain they stay empty rather than risk showing another call.
   When many end users share your integration, give each user their own agent.

## Responsible use
Call only when your user asks you to, and only numbers they give you or public business numbers. No unsolicited marketing, no emergency numbers, no payment card data over the phone. The agent always states that it is an AI.

## Pricing
$0.16 per minute, all inclusive (telephony, language model and voice), no monthly fee. See [callin.io/pricing](https://callin.io/pricing).

MIT licensed. © Replacing Humans LLC — Callin.io.
