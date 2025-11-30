# 게임 추천 AI Agent

OpenAI 기반 LLM + DynamoDB + Vector DB를 사용한 하이브리드 게임 추천 시스템

## 아키텍처

```
사용자 질의
    ↓
Agent (OpenAI GPT-4o 등)
    ├─ retrieve (Vector DB) → 의미 기반 검색
    └─ filter_games (DynamoDB) → 가격/장르 기반 필터링
    ↓
추천 결과 생성
```

## 데이터 소스

### 1. Vector DB (Knowledge Base)

* 의미 기반 검색
* `retrieve` tool 사용
* 예: "커플 게임", "퍼즐 협동 게임"

### 2. DynamoDB

* 정확한 조건 필터링
* 테이블: `GameMetadata`
* 필터: 가격, 장르, 멀티플레이어 여부

## 프로젝트 구조

```
ai-agent/
├── game_agent.py              # CLI 인터페이스
├── api.py                     # FastAPI 서버
├── tools/
│   ├── __init__.py
│   └── metadata_filter.py     # DynamoDB 필터링
├── data/
│   └── load_to_dynamodb.py    # Kaggle JSON → DynamoDB 업로드
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 설치 및 설정

### 1. 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (.env)

```
OPENAI_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_key
AWS_REGION=ap-northeast-2
KNOWLEDGE_BASE_ID=your_kb_id
```

### 4. Kaggle 데이터 준비

1. Kaggle에서 Steam Games Dataset 다운로드
   [https://www.kaggle.com/datasets/trolukovich/steam-games-complete-dataset](https://www.kaggle.com/datasets/trolukovich/steam-games-complete-dataset)
2. `games.json` 파일을 `data/` 폴더에 위치

### 5. DynamoDB 데이터 업로드

```bash
python data/load_to_dynamodb.py
```

## FastAPI 서버 실행

아래 명령어로 서버를 실행한다:

```bash
uvicorn api:app --reload --port 8000
```

서버는 다음 엔드포인트를 제공한다:

```
POST /recommend
{
  "query": "커플이랑 할 퍼즐 게임 추천해줘"
}
```

## CLI 모드 실행

### 대화형

```bash
python game_agent.py
```

### 단일 쿼리

```bash
python game_agent.py "2만원 이하 퍼즐 협동 게임"
```

## DynamoDB 스키마 예시

```json
{
  "app_id": "20200",
  "name": "Galactic Bowling",
  "price": 19.99,
  "genres": ["Casual", "Indie", "Sports"],
  "categories": ["Single-player", "Multi-player"],
  "tags": ["Indie", "Casual", "Sports"],
  "positive_reviews": 6,
  "negative_reviews": 11
}
```

## 트러블슈팅

### 1. 포트 8000 점유 오류

```
Address already in use
```

해결:

```bash
lsof -i :8000
kill -9 <PID>
```

### 2. AWS credential 오류

```
Unable to locate credentials
```

해결: `.env` 파일 확인

### 3. macOS 패키지 설치 오류

```
externally-managed-environment
```

해결: 가상환경 사용

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 개발 계획

* 가격 범위 필터링 정확도 향상
* Steam API 연동
* 개인화 추천 강화
* 웹 프론트엔드(React) 연동

## 라이선스

MIT
