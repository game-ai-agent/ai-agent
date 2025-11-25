from strands import Agent
import sys
import os
import io

# Define a paper analysis system prompt
PAPER_AGENT_PROMPT = """당신은 게임 정보 도우미입니다. 질문에 답변해주세요."""

def safe_input(prompt: str) -> str:
    """UTF-8 인코딩 오류를 안전하게 처리하는 input 함수."""
    try:
        # 먼저 일반 input 시도
        return input(prompt).strip()
    except UnicodeDecodeError:
        # 인코딩 오류 발생 시 재시도
        try:
            # stdin을 UTF-8로 재설정
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
            return input(prompt).strip()
        except (UnicodeDecodeError, UnicodeError):
            # 그래도 실패하면 raw bytes로 읽기
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                line = sys.stdin.buffer.readline()
                return line.decode('utf-8', errors='replace').strip()
            except Exception:
                raise


def main():
    """Main function to run the game analysis agent as a script."""
    
    paper_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=PAPER_AGENT_PROMPT,
        tools=[]
    )

    # Command line argument이 있으면 한 번만 실행하고 종료
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        response = paper_agent(prompt)
        print(response)
        return

    # 대화형 모드: 사용자가 "종료" 또는 "exit"를 입력할 때까지 계속 실행
    print("게임 정보 분석 에이전트를 시작합니다. 종료하려면 '종료' 또는 'exit'를 입력하세요.\n")

    # while 문으로 계속 돌음
    while True:
        try:
            prompt = safe_input("질문: ")

            # 종료 조건 확인
            if prompt.lower() in ['종료', 'exit', 'quit', 'q']:
                print("게임 정보 분석 에이전트를 종료합니다.")
                break

            # 빈 입력 처리
            if not prompt:
                print("질문을 입력해주세요.\n")
                continue

            # 에이전트 실행
            try:
                response = paper_agent(prompt)
                print(f"\n답변: {response}\n")
            except Exception as e:
                print(f"\n오류가 발생했습니다: {e}\n")

        except KeyboardInterrupt:
            print("\n\n게임 정보 분석 에이전트를 종료합니다.")
            break
        except EOFError:
            print("\n\n게임 정보 분석 에이전트를 종료합니다.")
            break


if __name__ == "__main__":
    main()