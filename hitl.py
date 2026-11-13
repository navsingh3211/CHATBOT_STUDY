
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import BaseMessage, AIMessage

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):

    print("Inside chat node")

    decision = interrupt({
        "question": state["messages"][-1].content,
        "instruction": "Approve? yes/no"
    })

    print("Decision received:", decision)

    if decision["approved"] == "no":
        return {
            "messages": [AIMessage(content="Request rejected!")]
        }

    return {
        "messages": [AIMessage(content="Request approved!")]
    }

builder = StateGraph(ChatState)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

app = builder.compile(checkpointer=MemorySaver())

config = {
    "configurable": {
        "thread_id": "ubuntu_test_001"
    }
}

# First execution
result = app.invoke(
    {"messages": [("user", "Explain gradient descent")]},
    config=config
)

# print("Interrupt:", result.get("__interrupt__"))
result = app.invoke(
    Command(resume={"approved": "no"}),
    config=config
)

print(result["messages"][-1].content)

config = {
    "configurable": {
        "thread_id": "ubuntu_test_002"
    }
}

result = app.invoke(
    {"messages": [("user", "Explain gradient descent")]},
    config=config
)

# Approve the request
result = app.invoke(
    Command(resume={"approved": "yes"}),
    config=config
)

print(result["messages"][-1].content)