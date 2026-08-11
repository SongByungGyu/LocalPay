import Foundation

/// 결제 인증형 후기. CLAUDE.md §17.
struct Review: Identifiable, Hashable, Codable, Sendable {
    let id: UUID
    let userName: String
    let rating: Int                 // 1~5
    let content: String
    let createdAt: Date
    let paymentType: PaymentType
    let paymentVerified: Bool
    let purchasedProduct: String?

    init(
        id: UUID = UUID(),
        userName: String,
        rating: Int,
        content: String,
        createdAt: Date,
        paymentType: PaymentType,
        paymentVerified: Bool,
        purchasedProduct: String? = nil
    ) {
        self.id = id
        self.userName = userName
        self.rating = rating
        self.content = content
        self.createdAt = createdAt
        self.paymentType = paymentType
        self.paymentVerified = paymentVerified
        self.purchasedProduct = purchasedProduct
    }
}
