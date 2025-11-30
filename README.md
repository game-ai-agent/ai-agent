# 게임 추천 AI Agent

Bedrock Knowledge Base + DynamoDB 기반 Hybrid 게임 추천 시스템

## 아키텍처

```
사용자 질의
    ↓
Agent (Nova Lite)
    ├─ retrieve (Bedrock KB - Vector DB) → 의미 기반 검색
    └─ filter_games (DynamoDB) → 정확한 필터링 (가격, 장르)
    ↓
하이브리드 추천 결과
```

## 데이터 소스

### 1. Bedrock Knowledge Base (이미 구축됨 ✅)
- **용도**: 의미 기반 검색
- **도구**: `retrieve` tool
- **검색**: "커플 게임", "힐링 게임", "협동 퍼즐"

### 2. DynamoDB (새로 구축)
- **용도**: 정확한 필터링
- **테이블**: `GameMetadata`
- **필터**: 가격, 장르, 멀티플레이어 여부

## 프로젝트 구조

```
game-agent/
├── game_agent.py              # Main agent
├── tools/
│   ├── __init__.py
│   └── metadata_filter.py     # DynamoDB 필터링 tool
├── data/
│   └── load_to_dynamodb.py    # Kaggle → DynamoDB 로더
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 설치 및 설정

### 1. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 실제 credential 입력
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_REGION
# - KNOWLEDGE_BASE_ID
```

### 4. Kaggle 데이터 다운로드

1. [Kaggle Steam Games Dataset](https://www.kaggle.com/datasets/trolukovich/steam-games-complete-dataset) 다운로드
2. `games.json` 파일을 `data/` 디렉토리에 배치

### 5. DynamoDB 테이블 생성 및 데이터 로드

```bash
python data/load_to_dynamodb.py
```

실행 결과:
```
============================================================
Steam 게임 데이터 → DynamoDB 로더
============================================================
테이블 'GameMetadata' 생성 중...
✅ 테이블 'GameMetadata' 생성 완료!

데이터 파일 'data/games.json' 로드 중...
✅ 27075 개 게임 데이터 로드 완료!

DynamoDB에 데이터 업로드 중...
  진행: 100/27075 게임 업로드 완료...
  진행: 200/27075 게임 업로드 완료...
  ...
✅ 업로드 완료!
   성공: 27075 개
   실패: 0 개
```

## 실행 방법

### 대화형 모드

```bash
python game_agent.py
```

```
============================================================
🎮 게임 추천 AI Agent
============================================================
종료하려면 'exit' 또는 'quit'를 입력하세요.

예시 질문:
  - "커플이랑 할 게임 추천해줘"
  - "2만원 이하 퍼즐 게임"
  - "멀티플레이어 캐주얼 게임"

질문:
```

### 단일 쿼리 모드

```bash
python game_agent.py "커플이랑 할 퍼즐 게임 2만원 이하"
```

## 사용 예시

### 예시 1: 기본 추천

```
질문: 커플이랑 할 게임 추천해줘

🎮 추천 게임:

1. It Takes Two
   - 가격: $39.99 (약 52,000원)
   - 플레이어: 2 (협동 전용)
   - 장르: Cooperative, Action, Adventure
   - 추천 이유: 커플 전용 협동 게임으로 스토리와 퍼즐이 훌륭합니다

2. Overcooked! 2
   - 가격: $24.99 (약 32,500원)
   - 플레이어: 1-4 (협동)
   - 장르: Cooperative, Party, Simulation
   - 추천 이유: 재미있는 요리 협동 게임으로 커플에게 인기

3. Stardew Valley
   - 가격: $14.99 (약 19,500원)
   - 플레이어: 1-4 (협동)
   - 장르: Simulation, RPG
   - 추천 이유: 힐링 농장 게임으로 커플 협동 플레이 가능

💡 더 정확한 추천을 원하시면:
- 예산 범위를 알려주세요
- 선호하는 장르를 알려주세요 (예: 퍼즐, 액션, 협동 등)
- 게임 난이도를 알려주세요 (초급/중급/상급)
```

### 예시 2: 조건 추가 (가격 + 장르)

```
질문: 2만원 이하 퍼즐 게임

🎮 추천 게임:

1. Portal 2
   - 가격: $9.99 (약 13,000원)
   - 플레이어: 1-2 (협동)
   - 장르: Puzzle, Action
   - 추천 이유: 최고의 퍼즐 게임 중 하나

2. The Witness
   - 가격: $19.99 (약 26,000원)
   - 플레이어: 1
   - 장르: Puzzle, Adventure
   - 추천 이유: 아름다운 그래픽과 어려운 퍼즐

3. Baba Is You
   - 가격: $14.99 (약 19,500원)
   - 플레이어: 1
   - 장르: Puzzle, Indie
   - 추천 이유: 독창적인 퍼즐 메커니즘
```

## 하이브리드 추천 방식

### 작동 흐름

```
사용자: "커플이랑 할 퍼즐 게임 2만원 이하"
    ↓
1. Agent가 조건 분석
   - 키워드: 커플, 협동, 퍼즐
   - 가격: ≤ $15 (약 2만원)
   - 장르: Puzzle
    ↓
2. retrieve("커플 협동 퍼즐 게임")
   → Vector DB에서 의미 기반 검색
   → app_id 리스트 추출
    ↓
3. filter_games(
      app_ids=[...],
      max_price=15.0,
      genres=["Puzzle"],
      must_have_multiplayer=True
   )
   → DynamoDB에서 정확한 조건 필터링
    ↓
4. 결과 종합 및 추천 이유 생성
```

### 장점

- ✅ **의미 기반 검색**: "커플 게임"이라는 자연어로 검색
- ✅ **정확한 필터링**: 가격, 장르 등 명확한 조건 적용
- ✅ **빠른 추천**: 조건 부족해도 일단 추천 제공
- ✅ **추가 정제**: 사용자가 조건 추가하면 더 정확한 추천

## DynamoDB 스키마

```python
{
  "app_id": "20200",           # Partition Key (String)
  "name": "Galactic Bowling",
  "price": 19.99,              # USD
  "genres": ["Casual", "Indie", "Sports"],
  "categories": ["Single-player", "Multi-player"],
  "tags": ["Indie", "Casual", "Sports", "Bowling"],
  "positive_reviews": 6,
  "negative_reviews": 11
}
```

## 트러블슈팅

### 1. DynamoDB 연결 오류

```
❌ 오류: Unable to locate credentials
```

**해결**: `.env` 파일에 AWS credential이 올바르게 설정되었는지 확인

### 2. Knowledge Base ID 오류

```
⚠️  경고: KNOWLEDGE_BASE_ID 환경 변수가 설정되지 않았습니다
```

**해결**: `.env` 파일에 `KNOWLEDGE_BASE_ID` 추가

### 3. 패키지 설치 오류 (macOS)

```
error: externally-managed-environment
```

**해결**: 가상환경 사용
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 개발 계획

- [ ] 가격 범위 필터링 UI 개선
- [ ] Steam API 연동 (실시간 가격)
- [ ] 리뷰 점수 기반 정렬
- [ ] 대화 기록 저장 및 개인화 추천

## 라이센스

MIT

## 기여

이슈 및 PR 환영합니다!
