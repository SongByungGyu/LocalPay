# LOCATION_PRECISION — Merchant 위치 메타데이터 설계 (Phase 13 Gate 3-B1)

> Merchant 좌표가 어디에서 왔고 얼마나 정확한지 항상 추적 가능하도록 하는 메타데이터 계층.
> Gate 3-B1 raw 저장까지 승인. Canonical merchants 반영은 Gate 4 이후 별도.

## 왜 필요한가

이번 프로젝트는 여러 좌표 소스를 혼합한다:

| 소스 | 정확도 | 사용 시나리오 |
|---|---|---|
| Dummy 25 seed | high (수동 확인) | 개발/데모 |
| 온누리 시장 centroid | market-level (블록 단위 ±100~200m) | 상점가/지하도 소속 매장 |
| 전국전통시장표준데이터 | market-level (dataset 좌표) | 전통시장 소속 매장 |
| Kakao Local place | high (개별 매장 좌표) | 미래 유료 quota 회복 시 |
| KOMSCO 지역화폐 API | high (`lat/lot` 필드) | Gate 2 재개 시 |
| 사용자·관리자 manual 수정 | high | 오류 신고 처리 |

**섞어 쓰면서도 "이 좌표가 얼마나 믿을만한지" 를 잃지 않아야 한다.** 특히 지도 UX 상 "정확한 매장 마커" 와 "시장 대표 마커" 를 구분해 표시하려면 필수.

## 메타데이터 스키마

Canonical `merchants` 테이블에 아래 3개 필드 추가 예정 (Gate 4 이전 migration `0003`).

### `location_source` — VARCHAR(32)

좌표가 어디에서 왔는지.

| 값 | 설명 |
|---|---|
| `source_exact` | 원본 데이터셋이 직접 개별 매장 좌표를 제공 (예: KOMSCO API `lat/lot`) |
| `market_dataset` | 전국전통시장표준데이터 매칭 결과 (시장 좌표를 매장에 상속) |
| `market_centroid_manual` | 하드코딩된 상점가 centroid (예: `anyang_markets.py` 상점가 7개) |
| `kakao_place` | Kakao Local Keyword Search 로 조회한 개별 매장 좌표 |
| `manual` | 관리자 수동 입력·정정 |
| `dummy_seed` | Phase 1~9 개발 dummy 좌표 |

### `location_precision` — VARCHAR(16)

지도 상에서 얼마나 좁은 범위를 가리키는지.

| 값 | 반경 예상 | 마커 표기 |
|---|---|---|
| `exact` | ~30m 이내 | 개별 매장 마커 (정확) |
| `approximate` | ~100m | 개별 매장 마커 (근사) — UI 상 흐리게 or "약" 표기 |
| `market_level` | ~100–200m (블록/시장 단위) | 시장 대표 마커에 통합. 개별 매장 마커로 사용 금지 |
| `region_level` | 시도/시군구 (수 km 이상) | 지도 노출 X, 리스트뷰만 |

### `location_confidence` — FLOAT (0.0 ~ 1.0)

좌표 매칭 신뢰도. `resolved_high/medium/ambiguous` 를 float 로 정량화.

| 범위 | 해석 |
|---|---|
| 0.9 ~ 1.0 | high — 자동 확정 가능 |
| 0.6 ~ 0.9 | medium — 조건부 사용 (필요 시 관리자 검토) |
| 0.3 ~ 0.6 | low — 자동 사용 금지, review queue 로 |
| < 0.3 | reject — 좌표 무시 |

## 소스별 기본값 매핑

| location_source | precision | confidence |
|---|---|---|
| `source_exact` | `exact` | 1.0 |
| `market_dataset` | `market_level` | 0.8 (시장 매핑은 확실하지만 매장 위치는 아님) |
| `market_centroid_manual` | `market_level` | 0.7 (상점가는 블록 단위) |
| `kakao_place` | 계산됨 (resolved_high=exact/1.0, medium=approximate/0.7 등) | resolved 점수 그대로 |
| `manual` | 관리자 지정 | 관리자 지정 |
| `dummy_seed` | `exact` | 1.0 (테스트 데이터라 명목상) |

## API·iOS 반영

### Backend `MerchantOut` 응답
```jsonc
{
  "id": "...",
  "name": "...",
  "latitude": 37.3946,
  "longitude": 126.9235,
  "locationSource": "market_centroid_manual",
  "locationPrecision": "market_level",
  "locationConfidence": 0.7,
  ...
}
```

### iOS 렌더링 규칙 (제안)
- `location_precision == "market_level"` 인 매장은 **개별 마커 X**, 소속 시장 마커에 count 로만 표시
- `location_precision == "approximate"` 는 지도상 흐린 마커 or 반경 표시
- `location_precision == "exact"` 는 일반 마커
- `location_precision == "region_level"` 은 지도 미노출

## Gate 3-B2 현재 상태 (2026-08-18)

- Migration `0003_add_location_metadata.py` VPS apply 완료 (`0002 → 0003`, non-destructive).
- `merchants` 에 `location_source/precision/confidence` 3필드 추가. Dummy 25건 `dummy_seed / exact / 1.0` backfill 완료.
- Backend `MerchantOut` 응답 스키마에 3필드 추가 (`locationSource/locationPrecision/locationConfidence` camelCase alias).
- Canonical Candidate 변환기 완성 (`worker/importers/onnuri/canonical.py`) — dry-run 만.
- `raw_onnuri_merchants` 1,251건 canonical dry-run 결과:
  - `market_dataset` 564 · `market_centroid_manual` 687
  - `market_level` 1,251 (모두)
  - coordinate_valid 1,251
- **canonical `merchants` 에 실제 INSERT 는 Gate 4 이후.**

## 관련 파일

- `worker/importers/onnuri/anyang_markets.py` — 시장 좌표 사전 (현재)
- `backend/alembic/versions/0002_raw_and_source_tables.py` — 이번 Gate raw 스키마
- `backend/alembic/versions/0003_add_location_metadata.py` — **Gate 4 예정** (아직 없음)
- `docs/MAP_UX_TODO.md` — 이 정보를 지도에 어떻게 표현할지
