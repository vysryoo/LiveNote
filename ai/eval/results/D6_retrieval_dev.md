# D6 검색 단계 Precision@4

측정일: 2026-10-30

## 조건

- 실험: `D6`
- 분할 방식: `semantic`
- 분할 기준값: `{'chunk_tokens': 300, 'chunk_overlap_tokens': 50, 'semantic_percentile': 95.0, 'semantic_overlap_sentences': 0, 'semantic_min_tokens': 40, 'semantic_max_tokens': 400}`
- 검색 조각 평균 토큰: `320.7`
- 데이터: `dev (art-2, eng-2, nur-1)`
- 검색 질의: `섹션 확정 요약`
- 검색 대상: `강의 자료 PDF 조각만 (섹션 요약 제외)`
- 채점 모델: `gpt-6.1-terra`
- 채점 추론 강도: `low`
- 채점 기준표 버전: `v1`

## Precision@4 (분야별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| 고급교양·간호 | 79.7% | ±9.9%p | 16 | 64 |
| 공학·전기전자 | 77.7% | ±7.7%p | 28 | 112 |
| 예술·디자인 | 81.6% | ±8.7%p | 19 | 76 |
| 전체 | 79.4% | ±5.0%p | 63 | 252 |

## Precision@4 (자료 형태별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| slide | 79.4% | ±5.0%p | 63 | 252 |
| 전체 | 79.4% | ±5.0%p | 63 | 252 |
