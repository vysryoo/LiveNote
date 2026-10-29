# D5 검색 단계 Precision@4

측정일: 2026-10-30

## 조건

- 실험: `D5`
- 분할 방식: `semantic`
- 분할 기준값: `{'chunk_tokens': 300, 'chunk_overlap_tokens': 50, 'semantic_percentile': 90.0, 'semantic_overlap_sentences': 1, 'semantic_min_tokens': 40, 'semantic_max_tokens': 400}`
- 검색 조각 평균 토큰: `281.1`
- 데이터: `dev (art-2, eng-2, nur-1)`
- 검색 질의: `섹션 확정 요약`
- 검색 대상: `강의 자료 PDF 조각만 (섹션 요약 제외)`
- 채점 모델: `gpt-6.1-terra`
- 채점 추론 강도: `low`
- 채점 기준표 버전: `v1`

## Precision@4 (분야별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| 고급교양·간호 | 82.8% | ±9.2%p | 16 | 64 |
| 공학·전기전자 | 76.8% | ±7.8%p | 28 | 112 |
| 예술·디자인 | 77.6% | ±9.4%p | 19 | 76 |
| 전체 | 78.6% | ±5.1%p | 63 | 252 |

## Precision@4 (자료 형태별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| slide | 78.6% | ±5.1%p | 63 | 252 |
| 전체 | 78.6% | ±5.1%p | 63 | 252 |
