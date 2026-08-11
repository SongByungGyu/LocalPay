import CoreLocation
import Foundation

/// LocalPay Backend v1 (`/api/v1/merchants*`) 을 호출하는 실 Repository.
/// - Backend 응답 JSON 은 iOS `Merchant` 모델과 1:1 매핑 (docs/API_SCHEMA.md 참조).
/// - `search` 는 서버에 아직 endpoint 가 없어(현재 Phase) `fetchAll()` 결과를
///   `DummyMerchantRepository` 와 동일한 규칙으로 로컬 필터링한다.
///   Phase 11 서버 검색 API 가 열리면 이 부분만 교체하면 된다.
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
        let all = try await fetchAll()
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !q.isEmpty else { return all }

        return all.filter { merchant in
            if merchant.name.lowercased().contains(q) { return true }
            if let market = merchant.marketName?.lowercased(), market.contains(q) { return true }
            if merchant.category.title.lowercased().contains(q) { return true }
            if merchant.products.contains(where: { $0.lowercased().contains(q) }) { return true }
            return false
        }
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
}
