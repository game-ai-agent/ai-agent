from strands import Agent, tool
from strands_tools import http_request, retrieve
import sys
import os
import io
import json
from typing import List, Dict, Any


# ============================================================================
# WORKER AGENTS - 각 분야를 전문적으로 처리하는 작업자 에이전트들
# ============================================================================

class GameInfoWorker:
    """게임 메타데이터 검색을 전문으로 하는 워커"""

    def __init__(self):
        # 게임 메타데이터 전문가 프롬프트: 로컬 데이터베이스에서 게임 정보 검색
        self.prompt = """당신은 게임 메타데이터 전문가입니다.
로컬 데이터베이스에서 게임 정보를 검색하고 제공하는 것이 당신의 임무입니다.
게임의 제목, 개발사, 출시년도, 장르, 플랫폼 등 상세한 메타데이터를 제공하세요.
"""
        self.agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=self.prompt,
            tools=[self._get_game_info_tool()]
        )

    @staticmethod
    def _get_game_info_tool():
        @tool
        def get_game_info(keyword: str) -> dict:
            """키워드나 제목으로 게임 메타데이터 검색"""
            # 로컬 게임 데이터베이스 (실제 환경에서는 API나 DB로 대체)
            game_database = {
                "zelda": {
                    "title": "The Legend of Zelda: Breath of the Wild",
                    "developer": "Nintendo",
                    "year": 2017,
                    "genre": ["Action", "Adventure"],
                    "platform": ["Switch", "Wii U"]
                },
                "elden ring": {
                    "title": "Elden Ring",
                    "developer": "FromSoftware",
                    "year": 2022,
                    "genre": ["Action RPG"],
                    "platform": ["PC", "PS5", "Xbox"]
                }
            }
            keyword_lower = keyword.lower()
            for key, game in game_database.items():
                if key in keyword_lower:
                    return game
            return {"error": f"'{keyword}'에 해당하는 게임을 찾을 수 없습니다"}
        return get_game_info

    def execute(self, task: str) -> str:
        """워커에게 할당된 작업 실행"""
        return self.agent(task)


class KnowledgeBaseWorker:
    """Knowledge Base 검색을 전문으로 하는 워커"""

    def __init__(self):
        # Knowledge Base 검색 전문가 프롬프트: AWS에 저장된 게임 정보 검색
        self.prompt = """당신은 Knowledge Base 검색 전문가입니다.
Knowledge Base에서 포괄적인 게임 정보를 검색하는 것이 당신의 임무입니다.
retrieve 도구를 사용하여 Knowledge Base에서 상세한 정보를 찾아주세요.
"""
        self.agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=self.prompt,
            tools=[retrieve]
        )

    def execute(self, task: str) -> str:
        """워커에게 할당된 작업 실행"""
        return self.agent(task)


class WebSearchWorker:
    """웹 검색을 전문으로 하는 워커"""

    def __init__(self):
        # 웹 검색 전문가 프롬프트: 인터넷에서 최신 게임 정보 수집
        self.prompt = """당신은 웹 검색 전문가입니다.
인터넷에서 최신 게임 정보, 뉴스, 리뷰를 검색하는 것이 당신의 임무입니다.
http_request 도구를 사용하여 웹에서 정보를 가져오세요.
"""
        self.agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=self.prompt,
            tools=[http_request]
        )

    def execute(self, task: str) -> str:
        """워커에게 할당된 작업 실행"""
        return self.agent(task)


# ============================================================================
# ORCHESTRATOR - 사용자 쿼리를 분석하고 워커들에게 작업 분배
# ============================================================================

class Orchestrator:
    """워커들에게 작업을 분배하는 오케스트레이터"""

    def __init__(self):
        # 오케스트레이터 프롬프트: 사용자 질문을 분석하여 적절한 워커에게 작업 할당
        self.prompt = """당신은 사용자 질문을 분석하고 어떤 워커에게 작업을 할당할지 결정하는 오케스트레이터입니다.

사용 가능한 워커들:
1. GameInfoWorker - 게임 메타데이터 검색 (제목, 개발사, 출시년도, 장르, 플랫폼)
2. KnowledgeBaseWorker - Knowledge Base에서 포괄적인 게임 정보 검색
3. WebSearchWorker - 최신 뉴스, 리뷰, 웹 정보 검색

사용자 질문을 분석하고 다음 구조의 JSON 객체를 반환하세요:
{
    "workers": ["worker_name1", "worker_name2"],
    "tasks": {
        "worker_name1": "워커1을 위한 구체적인 작업",
        "worker_name2": "워커2를 위한 구체적인 작업"
    }
}

가이드라인:
- 기본 게임 정보 질문: GameInfoWorker 사용
- 상세한 게임 정보: KnowledgeBaseWorker 사용
- 최신 뉴스/리뷰: WebSearchWorker 사용
- 필요시 여러 워커 동시 할당 가능
- 작업 설명은 구체적으로 작성

JSON 객체만 반환하고 다른 텍스트는 포함하지 마세요.
"""
        self.agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=self.prompt,
            tools=[]
        )

    def plan(self, query: str) -> Dict[str, Any]:
        """쿼리 분석 및 실행 계획 생성"""
        try:
            response = self.agent(f"사용자 질문: {query}")
            # 응답에서 JSON 추출
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                plan = json.loads(json_str)
                return plan
            else:
                # JSON 파싱 실패 시 기본 계획 사용
                return {
                    "workers": ["KnowledgeBaseWorker"],
                    "tasks": {"KnowledgeBaseWorker": query}
                }
        except Exception as e:
            print(f"Orchestrator 계획 수립 오류: {e}")
            # 에러 발생 시 기본 계획 사용
            return {
                "workers": ["KnowledgeBaseWorker"],
                "tasks": {"KnowledgeBaseWorker": query}
            }


# ============================================================================
# SYNTHESIZER - 워커들의 결과를 종합하여 최종 답변 생성
# ============================================================================

class Synthesizer:
    """여러 워커의 결과를 하나의 일관된 답변으로 통합하는 신시사이저"""

    def __init__(self):
        # 신시사이저 프롬프트: 여러 소스의 정보를 통합하여 최종 답변 생성
        self.prompt = """당신은 여러 출처의 정보를 결합하는 신시사이저입니다.

당신의 임무:
1. 여러 워커의 결과를 분석
2. 상호 보완적인 정보를 결합
3. 충돌하는 정보가 있다면 해결
4. 일관되고 포괄적인 최종 답변 생성

사용 가능한 모든 정보를 통합하여 잘 구조화된 답변을 제공하세요.
"""
        self.agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=self.prompt,
            tools=[]
        )

    def synthesize(self, query: str, results: Dict[str, str]) -> str:
        """워커 결과들을 최종 답변으로 통합"""
        # 신시사이저를 위한 결과 요약 준비
        results_text = "\n\n".join([
            f"=== {worker} 결과 ===\n{result}"
            for worker, result in results.items()
        ])

        synthesis_query = f"""사용자 질문: {query}

워커들의 결과:
{results_text}

이 결과들을 종합하여 포괄적인 답변을 작성해주세요.
"""
        return self.agent(synthesis_query)


# ============================================================================
# ORCHESTRATOR-WORKERS SYSTEM - 전체 시스템 통합
# ============================================================================

class OrchestratorWorkersSystem:
    """Orchestrator, Workers, Synthesizer를 조율하는 메인 시스템"""

    def __init__(self):
        # 전문 워커들 초기화
        self.workers = {
            "GameInfoWorker": GameInfoWorker(),
            "KnowledgeBaseWorker": KnowledgeBaseWorker(),
            "WebSearchWorker": WebSearchWorker()
        }

        # Orchestrator와 Synthesizer 초기화
        self.orchestrator = Orchestrator()
        self.synthesizer = Synthesizer()

    def process(self, query: str) -> str:
        """Orchestrator-Workers 파이프라인을 통해 사용자 질문 처리"""
        print("\n[Orchestrator] 질문 분석 및 실행 계획 수립 중...")

        # Step 1: Orchestrator가 실행 계획 생성
        plan = self.orchestrator.plan(query)
        print(f"[Orchestrator] 계획: {json.dumps(plan, indent=2, ensure_ascii=False)}\n")

        # Step 2: 할당된 워커들이 작업 실행
        results = {}
        for worker_name in plan.get("workers", []):
            if worker_name in self.workers:
                task = plan["tasks"].get(worker_name, query)
                print(f"[{worker_name}] 작업 실행 중...")
                try:
                    result = self.workers[worker_name].execute(task)
                    results[worker_name] = result
                    print(f"[{worker_name}] 작업 완료.\n")
                except Exception as e:
                    print(f"[{worker_name}] 오류: {e}\n")
                    results[worker_name] = f"오류: {e}"

        # Step 3: Synthesizer가 결과 통합
        if results:
            print("[Synthesizer] 결과 통합 중...")
            final_answer = self.synthesizer.synthesize(query, results)
            print("[Synthesizer] 통합 완료.\n")
            return final_answer
        else:
            return "워커들로부터 결과를 생성하지 못했습니다."


# ============================================================================
# 유틸리티 함수
# ============================================================================

def safe_input(prompt: str) -> str:
    """UTF-8 인코딩 오류를 안전하게 처리하는 입력 함수"""
    try:
        return input(prompt).strip()
    except UnicodeDecodeError:
        try:
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = io.TextIOWrapper(
                    sys.stdin.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
            return input(prompt).strip()
        except (UnicodeDecodeError, UnicodeError):
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                line = sys.stdin.buffer.readline()
                return line.decode('utf-8', errors='replace').strip()
            except Exception:
                raise


# ============================================================================
# 메인 실행 함수
# ============================================================================

def main():
    """Orchestrator-Workers 게임 정보 시스템 실행"""
    # 환경 변수에서 Knowledge Base ID 설정
    kb_id = os.environ.get("KNOWLEDGE_BASE_ID")
    if not kb_id:
        print("경고: KNOWLEDGE_BASE_ID 환경 변수가 설정되지 않았습니다")
        kb_id = input("Knowledge Base ID를 입력하세요 (건너뛰려면 Enter): ").strip()
        if kb_id:
            os.environ["KNOWLEDGE_BASE_ID"] = kb_id

    # Orchestrator-Workers 시스템 초기화
    system = OrchestratorWorkersSystem()

    # 단일 쿼리 모드 (커맨드 라인 인자 사용)
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        try:
            response = system.process(query)
            print("="*60)
            print("최종 답변:")
            print("="*60)
            print(response)
        except Exception as e:
            print(f"오류: {e}")
        return

    # 대화형 모드
    print("="*60)
    print("Orchestrator-Workers 게임 정보 시스템")
    print("="*60)
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")

    while True:
        try:
            query = safe_input("게임에 대해 질문하세요: ")

            if query.lower() in ['exit', 'quit', 'q']:
                print("시스템을 종료합니다.")
                break

            if not query:
                print("질문을 입력해주세요.\n")
                continue

            try:
                response = system.process(query)
                print("="*60)
                print("최종 답변:")
                print("="*60)
                print(f"{response}\n")
            except Exception as e:
                print(f"\n오류: {e}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\n시스템을 종료합니다.")
            break


if __name__ == "__main__":
    main()