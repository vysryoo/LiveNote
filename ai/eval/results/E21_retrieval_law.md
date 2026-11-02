# E21 검색 단계 Precision@4

측정일: 2026-11-02

## 조건

- 실험: `E21`
- 분할 방식: `semantic`
- 분할 기준값: `{'chunk_chars': 400, 'chunk_tokens': 300, 'chunk_overlap_tokens': 50, 'semantic_percentile': 95.0, 'semantic_overlap_sentences': 1, 'semantic_min_tokens': 40, 'semantic_max_tokens': 200}`
- 검색 조각 평균 토큰: `255.4`
- 데이터: `law (law-1, law-2, law-3)`
- 검색 질의: `섹션 확정 요약`
- 검색 대상: `강의 자료 PDF 조각만 (섹션 요약 제외)`
- 채점 모델: `gpt-6.1-terra`
- 채점 추론 강도: `low`
- 채점 기준표 버전: `v1`

## Precision@4 (분야별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| 법학·인공지능 | 94.3% | ±2.3%p | 97 | 388 |
| 전체 | 94.3% | ±2.3%p | 97 | 388 |

## Precision@4 (자료 형태별)

| 구분 | Precision | 95% 신뢰구간 | 섹션 | 판정 |
| --- | --- | --- | --- | --- |
| notes | 97.2% | ±3.1%p | 27 | 108 |
| slide | 93.2% | ±2.9%p | 70 | 280 |
| 전체 | 94.3% | ±2.3%p | 97 | 388 |
