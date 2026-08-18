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
    /// Phase 13 Gate 3-C: server 는 기본으로 `location_precision='market_level'` 매장 제외
    /// (그들은 mapMarkets 로 시장 대표 마커에서 렌더링).
    func mapMerchants(
        bbox: MapBBox,
        category: MerchantCategory,
        payment: PaymentFilter
    ) async throws -> [Merchant]

    /// 지도 BBOX 안 시장/상점가 대표 마커. Phase 13 Gate 3-C.
    /// 개별 매장이 아닌 aggregate. 탭 시 merchantsInMarket 으로 상세 fetch.
    func mapMarkets(
        bbox: MapBBox,
        category: MerchantCategory,
        payment: PaymentFilter
    ) async throws -> [MarketAggregate]

    /// 시장/상점가 안 매장 리스트 (paginated).
    func merchantsInMarket(
        marketId: String,
        category: MerchantCategory,
        payment: PaymentFilter,
        query: String?,
        limit: Int,
        offset: Int
    ) async throws -> [Merchant]
}
