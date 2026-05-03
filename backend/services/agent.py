import os
from typing import AsyncIterator, List, Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from tools.agent_tools import make_tools

SYSTEM_PROMPT = """You are Wise, the intelligent assistant for DocWise AI.
You help users understand their documents by answering questions, summarizing content,
creating notes, generating quizzes, and searching the web when needed.

You have access to these tools:
- search_pdf: search the user's uploaded document
- web_search: search the internet for current or external information
- summarize: summarize a specific section or chapter
- generate_quiz: create quiz questions and flashcards
- direct_answer: answer simple questions directly

Always cite the page number when referencing document content.
Be concise, clear, and helpful. If you are unsure, say so."""


def get_agent(doc_id: str):
    llm = ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        streaming=True,
    )
    tools = make_tools(doc_id)
    agent = create_react_agent(llm, tools)
    return agent


async def run_agent_stream(
    query: str,
    doc_id: str,
    history: List[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    agent = get_agent(doc_id)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if history:
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    tool_used = None

    async for event in agent.astream_events(
        {"messages": messages},
        version="v2",
    ):
        kind = event.get("event")

        if kind == "on_tool_start":
            tool_used = event.get("name", "unknown")
            yield f"data: [TOOL:{tool_used}]\n\n"

        elif kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield f"data: {chunk.content}\n\n"

    yield "data: [DONE]\n\n"