# langchain-callin

LangChain integration for [Callin.io](https://callin.io): give your agent a real phone line.
The agent places a call with an AI voice agent that pursues an objective (book a table,
confirm an appointment, ask a supplier for a quote), then reads the summary and transcript.

```bash
pip install langchain-callin
export CALLIN_API_KEY=...      # app.callin.io > Settings > API
export CALLIN_AGENT_ID=...     # the outbound voice agent that makes the calls
```

```python
from langchain_callin import CallinToolkit

tools = CallinToolkit().get_tools()
# callin_place_call, callin_get_call_result, callin_list_recent_calls
```

Or a single tool:

```python
from langchain_callin import CallinPlaceCall
CallinPlaceCall().invoke({"to": "+390111234567", "objective": "Book a table for 2 tomorrow at 20:30 under the name Rossi", "language": "it"})
```

Calls are asynchronous: `callin_place_call` returns a `campaign_id`, then `callin_get_call_result`
returns status, summary and transcript once the call ends. The voice agent always tells the
person it is an AI assistant. Use it only for calls the person would expect (no cold calling).

Built on the [`callin`](https://pypi.org/project/callin/) Python SDK. MIT license.
