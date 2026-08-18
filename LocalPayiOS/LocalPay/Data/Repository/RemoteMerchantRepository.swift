import CoreLocation
import Foundation

/// LocalPay Backend v1 (`/api/v1/…`) 을 호출하는 실 Repository.
/// - 응답 JSON 은 iOS `Merchant` 모델과 1:1 매핑 (docs/API_SCHEMA.md).
/// - `search` 는 Phase 13-B 부터 서버 `/api/v1/search` 를 직접 사용한다
///   (기존 fetchAll → 로컬 필터 방식 폐기).
/// - `mapMerchants` 는 Phase 13-A 지도 BBOX 조회.
final class RemoteMerchantRepository: MerchantRepository {

    private let client: HTTPClient

    init(baseURL: URL, session: URLSession = .shared) {
        self.client = HTTPClient(baseURL: baseURL, session: session)
    }

    // MARK: - MerchantRepository

    func fetchAll() async throws -> [Merchant] {
        try await client.get(
            "/api/v1/merchants",
            query: ["limit": "1000"]
        )
    }

    func fetch(id: String) async throws -> Merchant? {
        do {
            let merchant: Merchant = try await client.get("/api/v1/merchants/\(id)")
            return merchant
        } catch NetworkError.httpStatus(let code, _) where code == 404 {
            return nil
        }
    }

    func search(query: String) async throws -> [Merchant] {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return [] }
        return try await client.get(
            "/api/v1/search",
            query: [
                "q": q,
                "limit": "100"
            ]
        )
    }

    func nearby(center: CLLocationCoordinate2D, radiusMeters: Double) async throws -> [Merchant] {
        try await client.get(
            "/api/v1/merchants/nearby",
            query: [
                "lat": String(center.latitude),
                "lng": String(center.longitude),
                "radius": String(Int(radiusMeters.rounded())),
                "limit": "500"
            ]
        )
    }

    func filter(category: MerchantCategory, payment: PaymentFilter) async throws -> [Merchant] {
        try await client.get(
            "/api/v1/merchants",
            query: [
                "category": category == .all ? nil : category.rawValue,
                "payment": payment.rawValue,
                "limit": "1000"
            ]
        )
    }

    func mapMerchants(
        bbox: MapBBox,
        category: MerchantCategory,
        payment: PaymentFilter
    ) async throws -> [Merchant] {
        try await client.get(
            "/api/v1/merchants/map",
            query: [
                "north": String(bbox.north),
                "south": String(bbox.south),
                "east": String(bbox.east),
                "west": String(bbox.west),
                "category": category == .all ? nil : category.rawValue,
                "payment": payment.rawValue,
                "limit": "1000"
            ]
        )
    }

    func mapMarkets(
        bbox: MapBBox,
        category: MerchantCategory,
        payment: PaymentFilter
    ) async throws -> [MarketAggregate] {
        try await client.get(
            "/api/v1/markets/map",
            query: [
                "north": String(bbox.north),
                "south": String(bbox.south),
                "east": String(bbox.east),
                "west": String(bbox.west),
                "category": category == .all ? nil : category.rawValue,
                "payment": payment.rawValue,
                "limit": "200"
            ]
        )
    }

    func merchantsInMarket(
        marketId: String,
        category: MerchantCategory,
        payment: PaymentFilter,
        query: String?,
        limit: Int,
        offset: Int
    ) async throws -> [Merchant] {
        let encoded = marketId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? marketId
        return try await client.get(
            "/api/v1/markets/\(encoded)/merchants",
            query: [
                "category": category == .all ? nil : category.rawValue,
                "payment": payment.rawValue,
                "q": query,
                "limit": String(limit),
                "offset": String(offset)
            ]
        )
    }
}
