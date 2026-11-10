# backend.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage,ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
import sqlite3
import requests
import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

os.environ['LANGCHAIN_PROJECT']="chatbot-mcp-client-demo"
load_dotenv()

#LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SERVERS = { 
    "SimpleCalculatorServer":{ # local mcp
        "transport":"stdio",
        "command":"/home/navsingh3211/anaconda3/bin/uv",
        "args":[
            "run",
            "fastmcp",
            "run",
            "/usr/local/src/myWork/AGENTIC_AI_STUDY/deploy-mcp-on-remote-server/main.py"
        ]
    },
    "expenseTrackerMcpServer":{ #remote deployed mcp 
        "transport":"streamable_http",
        "url":"https://navsingh3211-expense-tracker.fastmcp.app/mcp",
        "headers": {
            "Authorization": f"Bearer {os.getenv('FASTMCP_AUTH_TOKEN')}"
        }
    }
}

# MCP client for local fastmcp server
client = MultiServerMCPClient(SERVERS)

# State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def build_graph():

    tools = await client.get_tools()
    # print(tools)

    llm_with_tools = llm.bind_tools(tools)

    async def chat_node(state: ChatState):
        """LLM node that may answer or request a tool call."""
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")

    graph.add_conditional_edges("chat_node",tools_condition)
    graph.add_edge('tools', 'chat_node')
    chatbot = graph.compile()
    return chatbot

async def main():
    chatbot= await build_graph()

    #running the graph
    CONFIG = {'configurable': {'thread_id': 'thread-1'}}
    out= await chatbot.ainvoke({'messages': [HumanMessage(content="Add expense - Rs 800 for movie ramayna on 4th nov")]}, config=CONFIG,debug=True)
    print(out['messages'][-1].content)

    # for message in out["messages"]:
    #     # print("\nMessage Type:", type(message).__name__)
    #     print("Content:", message.content)

    #     if hasattr(message, "tool_calls") and message.tool_calls:
    #         print("Tool Calls:", message.tool_calls)


if __name__ == "__main__":
    asyncio.run(main())