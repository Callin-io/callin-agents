"""LangChain agent that can place phone calls. pip install "callin[langchain]" langchain langchain-openai
Env: CALLIN_API_KEY, CALLIN_AGENT_ID, OPENAI_API_KEY"""
from langchain.agents import create_agent  # LangChain 1.x
from callin.langchain import get_callin_tools

agent = create_agent(model="openai:gpt-4.1-mini", tools=get_callin_tools(),
                     system_prompt="You can place phone calls with Callin.io. Confirm the number and goal with the user first.")
print(agent.invoke({"messages": [{"role": "user", "content":
    "Call +390111234567 and ask if they have a table for 2 tomorrow at 20:30 under Rossi."}]}))
