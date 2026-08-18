# CANONICAL_CANDIDATE — Canonical Merchant Candidate 설계

> Phase 13 Gate 3-B2. Raw 데이터 (온누리 · 지역화폐) 를 canonical `merchants`
> 테이블에 반영하기 전, **메모리 상 변환 결과** 를 검증하는 계층.
> Gate 3-B2 에서는 dry-run 만. 실제 INSERT 는 Gate 4 (dedup) 이후.

## 왜 Canonical Candidate 인가

두 갈래 raw 데이터 (온누리 CSV, 지역화폐 KOMSCO API) 를 각기 다른 스키마로 저장하고 있다. iOS 앱은 하나의 통일된 `Merchant` 모델만 안다. 그 사이에 **변환 · 병합** 계층이 필요하다.

```
raw_onnuri_merchants
        \
         ▶ Canonical Candidate (메모리) ─ dedup ─▶ merchants (DB)
        /                                             │
raw_local_currency_merchants                          ▼
                                                    iOS
```

Candidate 는 **DB 반영 이전의 최종 형태**. 오류·정합성·중복 후보를 미리 검사할 수 있다.

## Candidate 필드

`worker/importers/onnuri/canonical.py::CanonicalMerchantCandidate`

Backend `MerchantOut` schema · iOS `Merchant` domain model 과 1:1 호환. 즉 canonical merchants 에 그대로 저장하면 API 응답이 된다.

주요 필드:
- id, name, category, address, latitude, longitude
- supports_onnuri, supports_local_currency, local_currency_name
- supported_payment_types: `["onnuriPaper", "onnuriDigital", ...]`
- products, business_hours, market_name, description
- source (예: `onnuri-snapshot-20250731`), source_id (row_hash)
- **location_source, location_precision, location_confidence** (Gate 3-B2)

## Canonical id 규칙

`{source_type}-{region_alias}-{row_hash[:16]}`

예:
- `onnuri-a-4a9b1952c7a1c684` (안양 온누리 매장)
- 향후: `onnuri-s-...` (서울), `lc-a-...` (안양 지역화폐)

특성:
- **Idempotent**: 같은 매장은 재실행·재스냅샷에도 같은 id 유지
- **Scope**: source + region prefix 로 충돌 방지
- **Traceable**: row_hash 로 원본 raw record 로 역추적

## Location metadata 자동 결정

`docs/LOCATION_PRECISION.md` 규칙에 따라:

| 소속 시장 매핑 결과 | source | precision | confidence |
|---|---|---|---|
| 전통시장 dataset (5개) | `market_dataset` | `market_level` | 0.8 |
| 상점가 하드코딩 (7개) | `market_centroid_manual` | `market_level` | 0.7 |
| 매핑 없음 | `NULL` | `region_level` | `NULL` |
| Kakao Local (미래) | `kakao_place` | 계산됨 | 계산됨 |
| KOMSCO API (미래) | `source_exact` | `exact` | 1.0 |
| Dummy seed | `dummy_seed` | `exact` | 1.0 |

## Payment 변환

온누리 CSV `지류형 가맹 여부` / `디지털형 가맹 여부` (Y/N/O/X/있음/없음 등):

```
paper=Y digital=Y  → supported_payment_types = ["onnuriPaper", "onnuriDigital"]
paper=Y digital=N  → ["onnuriPaper"]
paper=N digital=Y  → ["onnuriDigital"]
```

`supports_onnuri = True` (온누리 데이터셋이므로 항상).  
`supports_local_currency = False` (온누리 데이터만으로는 판정 불가).

## Category 변환

`docs/CATEGORY_MAPPING` (별도 문서 없음, `worker/importers/onnuri/category_mapper.py` 참조):
1. products 키워드
2. name 키워드
3. (미래) Kakao category_group_code
4. etc

marketName 은 결정 대상이 아님 (스펙 §결정 2).

## Dry-run 결과 통계 (2026-08 실측)

`raw_onnuri_merchants` (안양 스냅샷 2025-07-31, 1,251건):

| 항목 | 값 |
|---|---|
| canonical_generated | 1,251 |
| coordinate_valid | 1,251 |
| location_source=market_dataset | 564 |
| location_source=market_centroid_manual | 687 |
| location_precision=market_level | 1,251 |
| category=restaurant | 338 |
| category=food | 187 |
| category=etc | 568 |

12개 시장/상점가 aggregation (`/api/v1/markets/map` 후보):
- 안양중앙인정시장 269, 평촌1번가 상점가 218, 안양1번가 상점가 143, 안양일번가 지하쇼핑몰 137, 안양남부시장 114, 안양관양시장 108, 안양중앙시장 72, 안양가구상점가 58, 안양농수산물 골목형상점가 53, 안양아크로상가골목형상점가 52, 안양중앙지하도상가 26, 안양육동시장 1

## Gate 4 이전 확정 필요 사항

1. **id 규칙 확정**: `onnuri-a-` 접두어가 canonical merchants.id 로 적합한지 (기존 dummy `m-001` 형식과 공존). 지금 그대로 진행 예정.
2. **Dedup 정책**: name+address+phone 조합 · confidence threshold · exact/high/medium/low.
3. **Merge 방식**: 같은 매장이 Onnuri + 지역화폐 양쪽에 있으면 어느 필드 우선?
4. **source · source_id · merchant_sources 매핑**: canonical 하나에 여러 source 연결.
5. **Traditional market vs 상점가 사전 분리**: 지금 `anyang_markets.py` 는 두 카테고리를 dict 로만 구분. 별도 필드로 관리하면 canonical.location_source 도 자동 정확.

## 관련 문서

- `docs/LOCATION_PRECISION.md` — 좌표 신뢰도 필드 상세
- `docs/MAP_UX_TODO.md` — location_precision 기반 지도 렌더링
- `docs/API_SCHEMA.md` — MerchantOut 필드 (Gate 3-B2 이후 3필드 추가)
- `worker/importers/onnuri/canonical.py` — 변환기 구현
- `worker/importers/onnuri/canonical_dryrun.py` — dry-run · market aggregation
