# Why Orchestrator-Workers Pattern?

## 문제 정의
- Steam 11만개 게임에서 복합 조건 검색 ("커플 + 퍼즐 + 2만원 이하")
- 여러 데이터 소스 통합 필요 (Vector DB, Steam API, 메타데이터)

## 패턴 선택 이유

### ReAct vs Orchestrator-Workers 비교
| 항목 | ReAct | Orchestrator-Workers | 선택 이유 |
|------|-------|---------------------|----------|
| 복잡도 | 단순 | 중간 | 3개 이상 데이터 소스 필요 |
| 병렬 처리 | 불가 | 가능 | 성능 최적화 필요 |
| 확장성 | 낮음 | 높음 | MCP 연동 계획 |

### 선택: Orchestrator-Workers
- **병렬 처리**: Vector DB + Steam API 동시 호출 → 응답 시간 50% 단축
- **역할 분리**: 각 Worker가 전문화 → 유지보수 용이
- **확장 가능**: 새 데이터 소스 추가 시 Worker만 추가