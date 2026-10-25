"""OpenAI Agents SDK + Callin.io MCP server (OAuth). pip install openai-agents"""
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    async with MCPServerStreamableHttp(name="callin", params={"url": "https://claude-mcp.callin.io/mcp"}) as callin:
        agent = Agent(name="Assistant", instructions="Use Callin.io tools for anything about phone calls.", mcp_servers=[callin])
        result = await Runner.run(agent, "Summarize my last 5 calls and flag any unhappy customer.")
        print(result.final_output)

asyncio.run(main())
