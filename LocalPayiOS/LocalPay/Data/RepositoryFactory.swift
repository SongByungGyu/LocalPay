import Foundation

/// 앱 실행 컨텍스트에 맞는 `MerchantRepository` 를 만들어 주는 얇은 팩토리.
/// - 실제 앱 실행(DEBUG/Release): `RemoteMerchantRepository`
/// - SwiftUI Preview: `DummyMerchantRepository` (네트워크 미허용/오프라인 상황 대응)
/// - XCTest: `DummyMerchantRepository` (테스트에서 서버 의존 제거)
///
/// ViewModel 은 이 팩토리를 default parameter 로만 참조하고,
/// 명시적으로 Dummy 를 넘겨받으면 그대로 사용한다.
enum RepositoryFactory {

    static func makeMerchantRepository() -> MerchantRepository {
        if isRunningInPreview || isRunningInTests {
            return DummyMerchantRepository()
        }
        return RemoteMerchantRepository(baseURL: AppConfiguration.current.apiBaseURL)
    }

    // MARK: - Environment detection

    private static var isRunningInPreview: Bool {
        ProcessInfo.processInfo.environment["XCODE_RUNNING_FOR_PREVIEWS"] == "1"
    }

    private static var isRunningInTests: Bool {
        NSClassFromString("XCTestCase") != nil
    }
}
