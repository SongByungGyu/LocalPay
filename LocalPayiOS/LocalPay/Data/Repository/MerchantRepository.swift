import CoreLocation
import Foundation

/// 가맹점 데이터 접근 추상화. CLAUDE.md §25, §26.
///
/// Phase 1 에서는 `DummyMerchantRepository` 만 구현한다.
/// 향후 `RemoteMerchantRepository` 로 교체될 수 있도록 도메인 모델만 노출한다.
protocol MerchantRepository: Sendable {
    func fetchAll() async throws -> [Merchant]
    func fetch(id: String) async throws -> Merchant?
    func search(query: String) async throws -> [Merchant]
    func nearby(center: CLLocationCoordinate2D, radiusMeters: Double) async throws -> [Merchant]
    func filter(category: MerchantCategory, payment: PaymentFilter) async throws -> [Merchant]
}
