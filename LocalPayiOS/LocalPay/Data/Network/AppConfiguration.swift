import Foundation

/// Backend API 접속 설정. Phase 12 부터 HTTPS 실 도메인 하나로 통합.
///
/// 실 도메인: `https://localpay.bgcompanyoffice.cloud`
/// 라우팅: VPS Traefik(v3, host mode, Docker provider, Let's Encrypt HTTP-01)
///        → localpay-api:8000 → FastAPI + PostgreSQL/PostGIS
/// SSH 터널 · 로컬 백엔드가 필요하지 않다.
struct AppConfiguration {

    /// 실제 iOS 앱이 호출할 REST Base URL. `/api/v1/...` 경로가 이 뒤에 붙는다.
    let apiBaseURL: URL

    /// 앱 전역에서 참조하는 현재 구성. `.current` 하나만 사용한다.
    ///
    /// DEBUG · Release 모두 실 운영 HTTPS 엔드포인트를 사용한다 (Phase 12).
    /// 이유:
    /// - SSH 터널 없이 실기기·시뮬레이터 어디서든 동작
    /// - iOS 26 시뮬레이터의 host loopback sandbox 이슈 회피
    /// - Wi-Fi/LTE 어느 네트워크에서도 동일 동작
    /// 실 개발 DB 는 아직 Dummy Seed (25개) 로만 채워져 있으므로 프로덕션 격리 문제 없음.
    /// 별도 개발 백엔드가 필요해지면 그때 DEBUG 분기를 다시 추가.
    static let current: AppConfiguration = {
        return AppConfiguration(
            apiBaseURL: URL(string: "https://localpay.bgcompanyoffice.cloud")!
        )
    }()
}
