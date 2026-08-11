import Foundation
import Observation

/// 사용자가 앱에서 새로 작성한 후기 저장소. CLAUDE.md §17.
///
/// - 기존 Dummy 매장의 seed 후기와 별도로 보관 (덮어쓰지 않음)
/// - UserDefaults 로 영속화
@Observable
final class ReviewsStore {

    private let defaultsKey = "LocalPay.userReviews.v1"
    private let defaults: UserDefaults

    /// Merchant.id → 사용자 후기 배열.
    private(set) var reviewsByMerchant: [String: [Review]]

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: defaultsKey),
           let decoded = try? JSONDecoder().decode([String: [Review]].self, from: data) {
            self.reviewsByMerchant = decoded
        } else {
            self.reviewsByMerchant = [:]
        }
    }

    func userReviews(for merchantId: String) -> [Review] {
        (reviewsByMerchant[merchantId] ?? []).sorted { $0.createdAt > $1.createdAt }
    }

    func append(_ review: Review, for merchantId: String) {
        var arr = reviewsByMerchant[merchantId] ?? []
        arr.append(review)
        reviewsByMerchant[merchantId] = arr
        persist()
    }

    var totalUserReviewCount: Int {
        reviewsByMerchant.values.reduce(0) { $0 + $1.count }
    }

    // MARK: - Persistence

    private func persist() {
        if let data = try? JSONEncoder().encode(reviewsByMerchant) {
            defaults.set(data, forKey: defaultsKey)
        }
    }

    // MARK: - Preview

    static func previewInstance() -> ReviewsStore {
        let ud = UserDefaults(suiteName: "preview.\(UUID().uuidString)")!
        return ReviewsStore(defaults: ud)
    }
}
