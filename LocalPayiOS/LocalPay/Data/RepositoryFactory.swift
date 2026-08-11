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
            #if DEBUG
            print("[RepositoryFactory] → DummyMerchantRepository (preview=\(isRunningInPreview) tests=\(isRunningInTests))")
            #endif
            return DummyMerchantRepository()
        }
        let base = AppConfiguration.current.apiBaseURL
        #if DEBUG
        print("[RepositoryFactory] → RemoteMerchantRepository baseURL=\(base.absoluteString)")
        #endif
        return RemoteMerchantRepository(baseURL: base)
    }

    // MARK: - Environment detection

    private static var isRunningInPreview: Bool {
        ProcessInfo.processInfo.environment["XCODE_RUNNING_FOR_PREVIEWS"] == "1"
    }

    /// XCTest 실행 여부. `XCTestConfigurationFilePath` 는 XCTest 러너가 유일하게 세팅하는 env 이므로
    /// 시뮬레이터 일반 실행에서 XCTest.framework 이 auto-inject 되어도 오판단하지 않는다.
    private static var isRunningInTests: Bool {
        ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil
    }
}
