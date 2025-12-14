# 게임 추천 AI Agent

OpenAI GPT + AWS Bedrock Knowledge Base(Vector DB) + DynamoDB 기반 하이브리드 게임 추천 시스템

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/c6d6b279-9f6e-4e3e-9b03-2c4597201893" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/044a7382-f784-4133-9bf7-0f548bce828e" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/04a0cdac-f631-46fd-a5d4-d0838a938adf" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/b55b23d9-b3bc-4fbe-a6f7-c4284bb642c7" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/8b859b17-e6c7-4129-b7ba-28e67fe6a7d9" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/49a335f8-b8c5-488e-8946-b259cedb96be" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/eadc4a78-7db1-4bf0-86f7-cfc03cd5e448" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/a97b07ce-169d-4314-badd-c67ccbf94428" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/41a4831f-fd34-467b-9d30-7d4fce0c2840" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/172379b2-d801-49d9-a568-bbf49b32bdf1" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/be3b05fd-114e-47b8-8e95-e721700d27db" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/11deb9fa-50cf-4ea2-8c94-fecdb713bf30" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/17a96aba-2210-4707-a255-05dc8e514608" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/32a747e2-0d82-4273-a9df-304a9311ce18" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/4a90c2cc-c7b3-45cc-9498-badc54377fe5" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/62f7abba-4f46-4a24-a800-5e47fbd834e3" />

<img width="2880" height="1621" alt="image" src="https://github.com/user-attachments/assets/f98cc049-3765-4943-8059-8da3853ab24f" />


## 아키텍처

```
사용자 질의
    ↓
Agent (OpenAI GPT-4o 등)
    ├─ retrieve (Bedrock Knowledge Base - Vector DB) → 의미 기반 검색
    └─ filter_games (DynamoDB) → 가격·장르 기반 필터링
    ↓
최종 추천 결과 생성
```

## 데이터 소스

### 1. AWS Bedrock Knowledge Base (Vector DB)

* 역할: 의미 기반 검색 (semantic search)
* 사용: `retrieve("커플 게임")`, `"힐링 RPG"`, `"협동 퍼즐"`
* 구성:

  * Embedding 모델: Titan Text Embedding
  * Vector Index: Bedrock Knowledge Base
  * GameMetadata / Steam 게임 정보가 벡터화되어 저장된 DB

### 2. DynamoDB

* 역할: 정확한 조건 필터링
* 테이블: `GameMetadata`
* 필터 요소:

  * 가격 범위
  * 장르
  * 멀티플레이 여부
  * 태그 기반 검색
* Vector DB 결과를 기반으로 **후처리 필터링** 수행

---

## 프로젝트 구조

```
ai-agent/
├── api.py                     # FastAPI 서버
├── game_agent.py              # CLI 모드
├── tools/
│   ├── metadata_filter.py     # DynamoDB 필터
│   └── __init__.py
├── data/
│   └── load_to_dynamodb.py    # Kaggle JSON → DynamoDB 적재
├── requirements.txt
├── .env.example
└── README.md
```

---

## 설치 및 설정

### 1. 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. .env 설정

```
OPENAI_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_key
AWS_REGION=ap-northeast-2

# Bedrock Knowledge Base (Vector DB)
KNOWLEDGE_BASE_ID=kb-xxxx
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

### 4. Kaggle 데이터 준비

`games.json`을 `data/`에 배치

### 5. DynamoDB 업로드

```bash
python data/load_to_dynamodb.py
```

---

## FastAPI 서버 실행

```bash
uvicorn api:app --reload --port 8000
```

---

## CLI 실행

```bash
python game_agent.py
```

---

## Bedrock Knowledge Base 사용 방식 (중요)

현재 Agent는 자동으로 다음 작업을 수행한다:

1. 입력 자연어 → OpenAI LLM 분석
2. Vector DB 검색 호출 (Bedrock Knowledge Base)

   ```
   retrieve("커플 협동 퍼즐 게임")
   ```
3. DynamoDB 필터 적용

   ```
   filter_games(max_price=20.0, genres=["Puzzle"])
   ```
4. 결과 결합 및 추천 생성

이 과정은 **OpenAI 모델을 쓰더라도 유지됨**
→ 벡터 검색은 Bedrock KB, 자연어 판단/추천 문장은 GPT-4o가 생성.

---

## 트러블슈팅

### Knowledge Base 오류

```
ResourceNotFoundException: Knowledge Base does not exist
```

필요 조치:

* Bedrock 콘솔 → Knowledge Base 생성
* 데이터 소스 S3 연결 확인
* Ingestion 수행 후 `ACTIVE` 상태인지 확인
* `.env`의 `KNOWLEDGE_BASE_ID` 수정

---
