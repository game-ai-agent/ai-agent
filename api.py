from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from game_agent import create_agent
import os
from typing import Dict, Optional
import uuid

# FastAPI 앱 초기화
app = FastAPI(
    title="Game Recommendation API",
    description="AI Agent 기반 게임 추천 API (세션별 메모리 지원)",
    version="2.0.0"
)

# CORS 설정 (모든 출처 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션별 Agent 저장소 (메모리)
# 실제 프로덕션에서는 Redis나 DynamoDB 사용 권장
session_agents: Dict[str, any] = {}

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # 세션 ID (없으면 새 세션 생성)

class QueryResponse(BaseModel):
    response: str
    session_id: str  # 사용된 세션 ID 반환

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Game Recommendation API is running"}

@app.post("/recommend", response_model=QueryResponse)
def recommend_game(request: QueryRequest):
    try:
        # 세션 ID 처리: 없으면 새로 생성
        session_id = request.session_id or str(uuid.uuid4())

        # 해당 세션의 Agent 가져오기 (없으면 새로 생성)
        if session_id not in session_agents:
            print(f"Creating new agent for session: {session_id}")
            session_agents[session_id] = create_agent()

        agent = session_agents[session_id]

        # Agent 호출 (내부적으로 대화 히스토리 유지)
        response = agent(request.query)

        return QueryResponse(
            response=str(response),
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """특정 세션 삭제 (메모리 정리)"""
    if session_id in session_agents:
        del session_agents[session_id]
        return {"status": "success", "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
def list_sessions():
    """현재 활성화된 세션 목록"""
    return {
        "total_sessions": len(session_agents),
        "session_ids": list(session_agents.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
