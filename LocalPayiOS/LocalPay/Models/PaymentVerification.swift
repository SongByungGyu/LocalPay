import Foundation

/// 상세화면 '최근 결제 확인' 섹션에 표시할 Dummy 결제 인증 로그. CLAUDE.md §16.
struct PaymentVerification: Identifiable, Hashable, Codable, Sendable {
    let id: UUID
    let paymentType: PaymentType
    let succeededAt: Date
    let note: String?

    init(
        id: UUID = UUID(),
        paymentType: PaymentType,
        succeededAt: Date,
        note: String? = nil
    ) {
        self.id = id
        self.paymentType = paymentType
        self.succeededAt = succeededAt
        self.note = note
    }
}
