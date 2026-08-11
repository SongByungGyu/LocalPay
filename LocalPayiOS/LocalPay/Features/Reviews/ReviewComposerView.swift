import SwiftUI

/// 사용자가 직접 후기를 작성하는 시트. CLAUDE.md §17.
struct ReviewComposerView: View {

    let merchantId: String
    let supportedPaymentTypes: [PaymentType]
    let onSubmit: (Review) -> Void

    @State private var rating: Int = 5
    @State private var content: String = ""
    @State private var product: String = ""
    @State private var selectedPayment: PaymentType
    @State private var paymentVerified: Bool = true

    @Environment(\.dismiss) private var dismiss

    init(merchantId: String, supportedPaymentTypes: [PaymentType], onSubmit: @escaping (Review) -> Void) {
        self.merchantId = merchantId
        self.supportedPaymentTypes = supportedPaymentTypes
        self.onSubmit = onSubmit
        _selectedPayment = State(initialValue: supportedPaymentTypes.first ?? .onnuriDigital)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("별점") {
                    HStack {
                        ForEach(1...5, id: \.self) { i in
                            Image(systemName: i <= rating ? "star.fill" : "star")
                                .font(.system(size: 22))
                                .foregroundStyle(.yellow)
                                .onTapGesture { rating = i }
                                .accessibilityLabel("\(i)점")
                        }
                    }
                }
                Section("후기 내용") {
                    TextField("솔직한 사용 후기를 남겨주세요", text: $content, axis: .vertical)
                        .lineLimit(3, reservesSpace: true)
                }
                Section("결제 수단") {
                    Picker("결제 수단", selection: $selectedPayment) {
                        ForEach(supportedPaymentTypes, id: \.self) { p in
                            Text(p.displayName).tag(p)
                        }
                    }
                    .pickerStyle(.navigationLink)

                    Toggle("결제 성공 인증", isOn: $paymentVerified)
                }
                Section("구매 상품 (선택)") {
                    TextField("예: 삼겹살", text: $product)
                }
                Section {
                    Text("DEMO: 후기는 이 기기에만 저장됩니다. 서비스 오픈 시 실제 결제 검증과 연동됩니다.")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColor.textSecondary)
                }
            }
            .navigationTitle("후기 작성")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("취소") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("등록") { submit() }
                        .disabled(content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func submit() {
        let review = Review(
            userName: "나",
            rating: rating,
            content: content.trimmingCharacters(in: .whitespacesAndNewlines),
            createdAt: Date(),
            paymentType: selectedPayment,
            paymentVerified: paymentVerified,
            purchasedProduct: product.isEmpty ? nil : product
        )
        onSubmit(review)
        dismiss()
    }
}

#Preview {
    ReviewComposerView(
        merchantId: "m-001",
        supportedPaymentTypes: [.onnuriDigital, .localCurrency],
        onSubmit: { _ in }
    )
}
