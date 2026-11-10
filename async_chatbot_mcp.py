# backend.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from dotenv import load_dotenv
import sqlite3
import requests
import os
import asyncio

os.environ['LANGCHAIN_PROJECT']="chatbot-mcp-client-demo"
load_dotenv()

#LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# Tools
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


tools = [calculator]
llm_with_tools = llm.bind_tools(tools)

# State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_graph():

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
    chatbot= build_graph()

    #running the graph
    CONFIG = {'configurable': {'thread_id': 'thread-1'}}
    out= await chatbot.ainvoke({'messages': [HumanMessage(content="Add two number 23 and 11")]}, config=CONFIG,debug=True)
    # print(out['messages'][-1].content)

    for message in out["messages"]:
        # print("\nMessage Type:", type(message).__name__)
        print("Content:", message.content)

        if hasattr(message, "tool_calls") and message.tool_calls:
            print("Tool Calls:", message.tool_calls)


if __name__ == "__main__":
    asyncio.run(main())