from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.schemas import ChatRequest, HistoryResponse, ChatMessage
from services.agent import run_agent_stream
from db.database import get_db, ChatMessage as ChatMessageDB

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    user_msg = ChatMessageDB(
        session_id=request.session_id,
        doc_id=request.doc_id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)
    await db.commit()

    full_response = []
    tool_used = None

    async def event_generator():
        nonlocal tool_used
        async for chunk in run_agent_stream(
            query=request.query,
            doc_id=request.doc_id,
            history=request.history,
        ):
            if chunk.startswith("data: [TOOL:"):
                tool_used = chunk.replace("data: [TOOL:", "").replace("]\n\n", "")
                yield chunk
            elif chunk == "data: [DONE]\n\n":
                assistant_msg = ChatMessageDB(
                    session_id=request.session_id,
                    doc_id=request.doc_id,
                    role="assistant",
                    content="".join(full_response),
                    tool_used=tool_used,
                )
                db.add(assistant_msg)
                await db.commit()
                yield chunk
            else:
                token = chunk.replace("data: ", "").replace("\n\n", "")
                full_response.append(token)
                yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessageDB)
        .where(ChatMessageDB.session_id == session_id)
        .order_by(ChatMessageDB.created_at)
    )
    messages = result.scalars().all()
    return HistoryResponse(
        session_id=session_id,
        messages=[
            ChatMessage(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_used=m.tool_used,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/chat/history/{session_id}")
async def clear_history(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessageDB).where(ChatMessageDB.session_id == session_id)
    )
    messages = result.scalars().all()
    for m in messages:
        await db.delete(m)
    await db.commit()
    return {"message": f"Cleared {len(messages)} messages for session {session_id}"}