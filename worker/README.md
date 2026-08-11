# worker

향후 공공데이터 · 지역화폐 가맹점 데이터를 정기적으로 수집·병합·업서트할 파이썬 워커가 들어갈 폴더.

Phase 10 시점에는 **비어 있음**. 다음 단계 (Phase 11) 에서 다음 구조로 채운다:

```
worker/
├── importers/
│   ├── onnuri/           소상공인시장진흥공단 온누리상품권 가맹점
│   ├── local_currency/   지자체별 지역사랑상품권 (경기지역화폐 등)
│   └── kakao_local/      좌표·주소 보정용 (선택)
├── jobs/
│   └── weekly_import.py  주간 배치
└── README.md
```

원칙:
- 임포터는 `backend/app/models` 를 재사용해 동일 스키마에 upsert
- API Key 는 반드시 `.env` (gitignored)
- 실제 외부 API 호출은 Phase 11 착수 시점부터
