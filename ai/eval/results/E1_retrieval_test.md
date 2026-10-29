# E1 검색 단계 Precision@4

측정일: 2026-10-30

## 조건

- 실험: `E1`
- 분할 방식: `recursive`
- 분할 기준값: `{'chunk_tokens': 340, 'chunk_overlap_tokens': 50, 'semantic_percentile': 95.0, 'semantic_overlap_sentences': 1, 'semantic_min_tokens': 40, 'semantic_max_tokens': 400}`
- 검색 조각 평균 토큰: `211.8`
- 데이터: `test (art-1, art-3, eng-1, eng-3, nur-2, nur-3)`
- 검색 질의: `섹션 확정 요약`
- 검색 대상: `강의 자료 PDF 조각만 (섹션 요약 제외)`
- 채점 모델: `gpt-6.1-terra`
- 채점 추론 강도: `low`
- 채점 기준표 버전: `v1`

## Precision@4 (분야별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| 고급교양·간호 | 80.5% | ±5.5%p | 50 | 200 |
| 공학·전기전자 | 92.6% | ±4.2%p | 37 | 148 |
| 예술·디자인 | 84.2% | ±5.3%p | 46 | 184 |
| 전체 | 85.2% | ±3.0%p | 133 | 532 |

## Precision@4 (자료 형태별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| notes | 87.3% | ±4.2%p | 61 | 244 |
| slide | 83.3% | ±4.3%p | 72 | 288 |
| 전체 | 85.2% | ±3.0%p | 133 | 532 |
