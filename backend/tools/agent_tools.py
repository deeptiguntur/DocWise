import os
from langchain.tools import tool
from langchain_ollama import ChatOllama
from services.vector_store import search_chunks


def get_llm():
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    )


def make_tools(doc_id: str):

    @tool
    def search_pdf(query: str) -> str:
        """Search the uploaded PDF document using semantic similarity.
        Use this when the user asks about specific content, facts, definitions,
        or any information that would be found inside their uploaded document.
        Do NOT use for questions about current events or information not in the doc."""
        chunks = search_chunks(query, doc_id, top_k=int(os.getenv("TOP_K_RESULTS", 5)))
        if not chunks:
            return "No relevant content found in the document for this query."
        output = []
        for i, c in enumerate(chunks, 1):
            output.append(f"[Source: Page {c['page_number']}]\n{c['text']}")
        return "\n\n---\n\n".join(output)

    @tool
    def web_search(query: str) -> str:
        """Search the web for current information, recent events, or facts not found in the document.
        Use this when the user asks about something that requires up-to-date information,
        or when the document doesn't contain enough context to answer the question."""
        try:
            from duckduckgo_search import DDGS
            results = DDGS().text(query, max_results=4)
            if not results:
                return "No web results found."
            output = []
            for r in results:
                output.append(f"[{r['title']}]\n{r['body']}\nSource: {r['href']}")
            return "\n\n---\n\n".join(output)
        except Exception as e:
            return f"Web search unavailable: {str(e)}"

    @tool
    def summarize(section: str) -> str:
        """Summarize a specific chapter, section, or page range from the document.
        Use this when the user asks for a summary, overview, or brief of a specific part.
        Pass the section name or page range as input (e.g. 'chapter 2' or 'pages 5-10')."""
        chunks = search_chunks(section, doc_id, top_k=8)
        if not chunks:
            return "Could not find that section in the document."
        combined = "\n\n".join(c["text"] for c in chunks)
        response = get_llm().invoke(
            f"Summarize the following document excerpt clearly and concisely:\n\n{combined}"
        )
        return response.content

    @tool
    def generate_quiz(topic: str) -> str:
        """Generate quiz questions or flashcards from the document on a given topic.
        Use this when the user asks to be quizzed, wants flashcards, or wants to test their knowledge.
        Returns structured questions with answers."""
        chunks = search_chunks(topic, doc_id, top_k=6)
        if not chunks:
            return "Could not find enough content on that topic to generate a quiz."
        combined = "\n\n".join(c["text"] for c in chunks)
        prompt = (
            f"Based on this content, generate 5 quiz questions with answers. "
            f"Format each as:\nQ: [question]\nA: [answer]\n\nContent:\n{combined}"
        )
        response = get_llm().invoke(prompt)
        return response.content

    @tool
    def direct_answer(question: str) -> str:
        """Answer a general knowledge question directly without searching the document or web.
        Use this ONLY for simple factual questions, greetings, or questions about DocWise AI itself
        that don't require document or web lookup."""
        response = get_llm().invoke(question)
        return response.content

    return [search_pdf, web_search, summarize, generate_quiz, direct_answer]