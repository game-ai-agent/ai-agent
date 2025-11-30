from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from game_agent import create_agent
import os

# FastAPI 앱 초기화
app = FastAPI(
    title="Game Recommendation API",
    description="AI Agent 기반 게임 추천 API",
    version="1.0.0"
)

# Agent 초기화 (앱 시작 시 한 번만 실행)
print("Initializing Game Agent...")
try:
    agent = create_agent()
except Exception as e:
    print(f"Failed to initialize agent: {e}")
    agent = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Game Recommendation API is running"}

@app.post("/recommend", response_model=QueryResponse)
def recommend_game(request: QueryRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = agent(request.query)
        return QueryResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
