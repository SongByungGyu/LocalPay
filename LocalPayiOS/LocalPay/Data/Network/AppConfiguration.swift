import Foundation

/// Backend API 접속 설정. 빌드 구성(DEBUG / Release) 별로 Base URL 을 분리한다.
///
/// DEBUG: 회사 Mac 에서 여는 SSH 터널(`ssh -N -L 18080:127.0.0.1:18080 …`) 로 VPS 백엔드에 접속한다.
/// Release: 실 서비스 도메인이 발급되면 아래 URL 만 교체하면 된다.
struct AppConfiguration {

    /// 실제 iOS 앱이 호출할 REST Base URL. `/api/v1/...` 경로가 이 뒤에 붙는다.
    let apiBaseURL: URL

    /// 앱 전역에서 참조하는 현재 구성. `.current` 하나만 사용한다.
    ///
    /// - DEBUG 에서 host 를 `localhost` 로 쓰는 이유: SSH 터널이 IPv6 `[::1]` 에만 bind 되는 경우가 있어
    ///   `127.0.0.1` 문자열이 URL 에 박히면 iOS URLSession 이 IPv4 만 시도하다 `Connection refused` 로 실패한다.
    ///   `localhost` 는 시스템 resolver 가 IPv4/IPv6 둘 다 반환하므로 Happy Eyeballs 가 성공한 쪽을 쓴다.
    static let current: AppConfiguration = {
        #if DEBUG
        return AppConfiguration(
            apiBaseURL: URL(string: "http://localhost:18080")!
        )
        #else
        return AppConfiguration(
            apiBaseURL: URL(string: "https://api.localpay.example.com")!
        )
        #endif
    }()
}
