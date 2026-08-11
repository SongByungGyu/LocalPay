import CoreLocation
import Foundation

/// Phase 1~8 동안 사용하는 인메모리 Dummy Repository.
/// 실제 API 는 향후 `RemoteMerchantRepository` 로 교체된다. CLAUDE.md §25 ~ §28.
final class DummyMerchantRepository: MerchantRepository {

    private let merchants: [Merchant]

    init(merchants: [Merchant] = DummyMerchantSeed.allMerchants) {
        self.merchants = merchants
    }

    func fetchAll() async throws -> [Merchant] {
        merchants
    }

    func fetch(id: String) async throws -> Merchant? {
        merchants.first { $0.id == id }
    }

    func search(query: String) async throws -> [Merchant] {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !q.isEmpty else { return merchants }

        return merchants.filter { merchant in
            if merchant.name.lowercased().contains(q) { return true }
            if let market = merchant.marketName?.lowercased(), market.contains(q) { return true }
            if merchant.category.title.lowercased().contains(q) { return true }
            if merchant.products.contains(where: { $0.lowercased().contains(q) }) { return true }
            return false
        }
    }

    func nearby(center: CLLocationCoordinate2D, radiusMeters: Double) async throws -> [Merchant] {
        merchants
            .map { m -> (Merchant, Double) in
                let d = GeoDistance.meters(from: center, to: m.coordinate)
                var withDistance = m
                withDistance.distanceMeters = d
                return (withDistance, d)
            }
            .filter { $0.1 <= radiusMeters }
            .sorted { $0.1 < $1.1 }
            .map { $0.0 }
    }

    func filter(category: MerchantCategory, payment: PaymentFilter) async throws -> [Merchant] {
        merchants.filter { m in
            matches(category: category, in: m) && matches(payment: payment, in: m)
        }
    }

    // MARK: - Private

    private func matches(category: MerchantCategory, in m: Merchant) -> Bool {
        category == .all || m.category == category
    }

    private func matches(payment filter: PaymentFilter, in m: Merchant) -> Bool {
        switch filter {
        case .all:            return true
        case .onnuri:         return m.supportsOnnuri
        case .localCurrency:  return m.supportsLocalCurrency
        case .both:           return m.supportsOnnuri && m.supportsLocalCurrency
        }
    }
}
