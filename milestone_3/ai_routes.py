from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from milestone_3.auth import get_current_user
from milestone_3.rag import rag_pipeline
from milestone_3.rbac import RBAC_RULES
from milestone_3.logs import log_access

router = APIRouter()


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    role = current_user["role"].lower()
    username = current_user["username"]

    # RBAC: check role exists
    if role not in RBAC_RULES:
        raise HTTPException(status_code=403, detail="Role not allowed")

    # Call RAG
    result = rag_pipeline(request.query, role)

    # STEP 7: Proper AI logging
    log_access(
        username=username,
        role=role,
        query=request.query,
        confidence=result["confidence"]
    )

    return {
        "answer": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"],
        "role": role,
        "department": role
    }
