"""
게임 추천 AI Agent (Hybrid 방식)

아키텍처:
- Bedrock Knowledge Base (Vector DB): 의미 기반 검색
- DynamoDB: 정확한 필터링 (가격, 장르, 멀티플레이어)
- Hybrid: retrieve로 후보 찾고 → filter_games로 정확한 조건 필터링
"""
from strands import Agent
from strands_tools import http_request, retrieve
from tools.metadata_filter import filter_games, get_game_by_id
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


# ============================================================================
# 시스템 프롬프트: 하이브리드 추천 방식
# ============================================================================

GAME_AGENT_PROMPT = """당신은 게임 추천 전문가입니다.

## 사용 가능한 도구들:

1. **retrieve** - Bedrock Knowledge Base (Vector DB)에서 의미 기반 검색
   - 사용자의 취향, 상황에 맞는 게임 찾기
   - 예: "커플 게임", "힐링 게임", "협동 퍼즐"

2. **filter_games** - DynamoDB에서 정확한 조건 필터링
   - 가격, 장르, 멀티플레이어 등 명확한 조건으로 필터링
   - 인자: max_price, min_price, genres, must_have_multiplayer
   - 예: filter_games(max_price=20.0, genres=["Puzzle"])

3. **get_game_by_id** - 특정 게임의 상세 정보 조회
   - app_id로 게임 정보 가져오기

4. **http_request** - 최신 뉴스, 리뷰 검색 (필요시)

## 추천 프로세스 (하이브리드 방식):

### 1단계: 사용자 질의 분석
- 조건 추출: 가격, 장르, 플레이어 수, 난이도 등
- 예: "커플이랑 할 퍼즐 게임 2만원 이하"
  → 조건: 협동/2인 게임, 퍼즐 장르, 가격 ≤ $20

### 2단계: Bedrock KB 검색 (의미 기반)
- retrieve 도구로 관련 게임 검색
- 사용자의 상황, 취향을 자연어로 검색
- 예: retrieve("커플 협동 퍼즐 게임")

### 3단계: DynamoDB 필터링 (정확한 조건)
- filter_games로 정확한 조건 필터링
- 가격, 장르 등 구체적인 조건 적용
- 예: filter_games(max_price=20.0, genres=["Puzzle"], must_have_multiplayer=True)

### 4단계: 추천 결과 생성

**출력 형식**:
```
🎮 추천 게임:

1. [게임 제목]
   - 가격: $[가격] (약 [원화]원)
   - 플레이어: [인원]
   - 장르: [장르]
   - 추천 이유: [상황에 맞는 이유]

2. [게임 제목]
   ...

3. [게임 제목]
   ...

💡 더 정확한 추천을 원하시면:
- 예산 범위를 알려주세요
- 선호하는 장르를 알려주세요 (예: 퍼즐, 액션, 협동 등)
- 게임 난이도를 알려주세요 (초급/중급/상급)
```

## 중요 규칙:

1. **조건 부족해도 일단 추천** (빠른 만족감)
   - 완벽한 정보가 없어도 최선의 추천 제공
   - "💡 더 정확한 추천" 섹션으로 추가 정보 요청

2. **가격 변환**
   - DB는 USD 기준 → 원화로 변환 (1 USD = 약 1,300원)
   - 사용자가 "2만원"이라고 하면 max_price=15.38 ($20 정도)

3. **장르 매칭**
   - 한글 장르 → 영어 장르로 변환
   - 퍼즐 → Puzzle, 액션 → Action, 협동 → Cooperative

4. **상위 3-5개 추천**
   - 가성비 좋은 게임 우선
   - 리뷰 평가 고려 (positive_reviews / negative_reviews)

주어진 도구들을 적극 활용하여 최선의 추천을 제공하세요!
"""


# ============================================================================
# 유틸리티 함수
# ============================================================================

def safe_input(prompt: str) -> str:
    """UTF-8 인코딩 오류를 안전하게 처리하는 입력 함수"""
    try:
        return input(prompt).strip()
    except UnicodeDecodeError:
        import io
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = io.TextIOWrapper(
                sys.stdin.buffer,
                encoding='utf-8',
                errors='replace'
            )
        return input(prompt).strip()


# ============================================================================
# 메인 실행 함수
# ============================================================================

def create_agent():
    """게임 추천 Agent 생성 및 반환"""
    # 환경 변수 확인
    kb_id = os.getenv("KNOWLEDGE_BASE_ID")
    use_kb = False

    if not kb_id:
        print("  Knowledge Base ID가 설정되지 않았습니다")
        print("   DynamoDB만 사용하여 추천합니다 (Vector DB 없이)")
    else:
        use_kb = True
        print(f" Knowledge Base 연결: {kb_id}")

    # Agent 초기화
    print("\n게임 추천 Agent 초기화 중...")

    # 서울 리전에서 사용 가능한 모델
    # Claude 3 Haiku: 가장 빠르고 저렴
    # Claude 3.5 Sonnet: 더 강력하지만 비쌈
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    # Knowledge Base 사용 가능 여부에 따라 도구 선택
    if use_kb:
        tools = [retrieve, filter_games, get_game_by_id, http_request]
        print("   모드: Hybrid (Vector DB + DynamoDB)")
    else:
        tools = [filter_games, get_game_by_id, http_request]
        print("   모드: DynamoDB 전용")

    agent = Agent(
        model=model_id,
        system_prompt=GAME_AGENT_PROMPT,
        tools=tools
    )
    print(" 초기화 완료!\n")
    return agent

def main():
    """게임 추천 Agent 실행"""
    agent = create_agent()

    # 단일 쿼리 모드 (커맨드 라인 인자 사용)
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        try:
            print(f"질문: {query}\n")
            response = agent(query)
            print("="*60)
            print(response)
            print("="*60)
        except Exception as e:
            print(f" 오류: {e}")
        return

    # 대화형 모드
    print("="*60)
    print("🎮 게임 추천 AI Agent")
    print("="*60)
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    print("예시 질문:")
    print('  - "커플이랑 할 게임 추천해줘"')
    print('  - "2만원 이하 퍼즐 게임"')
    print('  - "멀티플레이어 캐주얼 게임"\n')

    while True:
        try:
            query = safe_input("질문: ")

            if query.lower() in ['exit', 'quit', 'q', '종료']:
                print("Agent를 종료합니다. 안녕히 가세요!")
                break

            if not query:
                print("질문을 입력해주세요.\n")
                continue

            try:
                print()  # 빈 줄
                response = agent(query)
                print("="*60)
                print(response)
                print("="*60)
                print()  # 빈 줄
            except Exception as e:
                print(f"\n 오류: {e}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\nAgent를 종료합니다. 안녕히 가세요!")
            break


if __name__ == "__main__":
    main()
