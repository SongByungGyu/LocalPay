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

    /// 지도 화면에 현재 보이는 사각 영역 (BBOX) 안의 매장만 반환.
    /// Phase 13-A 부터 지도 로딩의 기본 API. 전국 데이터에서는 이 경로만 사용한다.
    func mapMerchants(
        bbox: MapBBox,
        category: MerchantCategory,
        payment: PaymentFilter
    ) async throws -> [Merchant]
}
