import SwiftUI

/// 검색 결과 · 즐겨찾기 목록에서 사용하는 Merchant Card. CLAUDE.md §19.
struct MerchantCard: View {
    let merchant: Merchant
    var onTap: () -> Void = {}

    @Environment(FavoritesStore.self) private var favorites

    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: AppSpacing.md) {
                categoryThumb

                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(merchant.name)
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(AppColor.textPrimary)
                            .lineLimit(1)
                        Spacer()
                        Text(DistanceFormatter.short(fromMeters: merchant.distanceMeters))
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textSecondary)
                    }
                    HStack(spacing: 6) {
                        Text(merchant.category.title)
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textSecondary)
                        Text("·")
                            .foregroundStyle(AppColor.textSecondary)
                        RatingView(rating: merchant.rating, reviewCount: merchant.reviewCount)
                    }
                    HStack(spacing: 6) {
                        PaymentBadge(kind: merchant.paymentBadge)
                        if let name = merchant.localCurrencyName, merchant.supportsLocalCurrency {
                            Text(name)
                                .font(AppTypography.chip)
                                .foregroundStyle(AppColor.textSecondary)
                        }
                    }
                    if !merchant.products.isEmpty {
                        Text(merchant.products.prefix(3).joined(separator: " · "))
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textSecondary)
                            .lineLimit(1)
                    }
                }

                FavoriteToggleButton(
                    isFavorite: favorites.isFavorite(merchant.id),
                    action: { favorites.toggle(merchant.id) }
                )
            }
            .padding(AppSpacing.md)
            .background(
                RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.background)
            )
            .overlay(
                RoundedRectangle(cornerRadius: AppRadius.card).stroke(AppColor.divider, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    private var categoryThumb: some View {
        let style = PaymentBadgeStyle(merchant.paymentBadge)
        return ZStack {
            RoundedRectangle(cornerRadius: 12)
                .fill(style.color.opacity(0.18))
            Image(systemName: merchant.category.iconName)
                .font(.system(size: 22, weight: .semibold))
                .foregroundStyle(style.color)
        }
        .frame(width: 56, height: 56)
    }
}

#Preview {
    MerchantCard(merchant: DummyMerchantSeed.allMerchants[0], onTap: {})
        .padding()
        .environment(FavoritesStore.previewInstance())
}
