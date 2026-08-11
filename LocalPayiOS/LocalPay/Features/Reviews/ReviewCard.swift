import SwiftUI

/// 결제 인증형 후기 카드. CLAUDE.md §17.
struct ReviewCard: View {
    let review: Review

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            HStack(alignment: .center, spacing: 6) {
                Text(review.userName)
                    .font(AppTypography.body.weight(.semibold))
                    .foregroundStyle(AppColor.textPrimary)
                Spacer()
                Text(DateHelper.relative(review.createdAt))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColor.textSecondary)
            }

            HStack(spacing: 2) {
                ForEach(0..<5) { i in
                    Image(systemName: i < review.rating ? "star.fill" : "star")
                        .font(.system(size: 12))
                        .foregroundStyle(.yellow)
                }
            }

            Text(review.content)
                .font(AppTypography.body)
                .foregroundStyle(AppColor.textPrimary)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 6) {
                if review.paymentVerified {
                    HStack(spacing: 4) {
                        Image(systemName: "checkmark.seal.fill")
                            .font(.system(size: 11, weight: .bold))
                        Text("\(review.paymentType.displayName) 결제 확인")
                            .font(AppTypography.chip)
                    }
                    .foregroundStyle(AppColor.success)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(AppColor.success.opacity(0.12)))
                }
                if let p = review.purchasedProduct {
                    Text("구매상품: \(p)")
                        .font(AppTypography.chip)
                        .foregroundStyle(AppColor.textSecondary)
                }
            }
        }
        .padding(AppSpacing.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.surface)
        )
    }
}

#Preview {
    ReviewCard(review: Review(
        userName: "안양민준",
        rating: 5,
        content: "삼겹살 구매했는데 온누리 결제 잘 됩니다.",
        createdAt: Date().addingTimeInterval(-3 * 86400),
        paymentType: .onnuriDigital,
        paymentVerified: true,
        purchasedProduct: "삼겹살"
    ))
    .padding()
}
