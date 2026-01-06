# app/ai/tools/hello_tool.py
from langchain.tools import tool

@tool("hello_user", description="Say hello to the user with a personalized greeting.")
def hello_user(name: str) -> str:
    return f"Hello {name}, I'm your AI assistant."
