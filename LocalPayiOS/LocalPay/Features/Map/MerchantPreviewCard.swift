import SwiftUI

/// 지도에서 Marker 선택 시 하단에 뜨는 카드. CLAUDE.md §15.
struct MerchantPreviewCard: View {
    let merchant: Merchant
    let onClose: () -> Void
    let onOpenDetail: () -> Void

    @Environment(FavoritesStore.self) private var favorites

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            HStack(alignment: .top, spacing: AppSpacing.sm) {
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 6) {
                        Text(merchant.name)
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColor.textPrimary)
                            .lineLimit(1)
                    }

                    HStack(spacing: 6) {
                        HStack(spacing: 3) {
                            Image(systemName: merchant.category.iconName)
                                .font(.system(size: 11))
                            Text(merchant.category.title)
                                .font(AppTypography.chip)
                        }
                        .foregroundStyle(AppColor.textSecondary)

                        Text("·")
                            .foregroundStyle(AppColor.textSecondary)

                        RatingView(rating: merchant.rating, reviewCount: merchant.reviewCount)

                        Text("·")
                            .foregroundStyle(AppColor.textSecondary)

                        Text(DistanceFormatter.short(fromMeters: merchant.distanceMeters))
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textSecondary)
                    }
                }
                Spacer()
                FavoriteToggleButton(
                    isFavorite: favorites.isFavorite(merchant.id),
                    action: { favorites.toggle(merchant.id) }
                )
                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(AppColor.textSecondary)
                        .frame(width: 32, height: 32)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("닫기")
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
                HStack(spacing: AppSpacing.xs) {
                    ForEach(merchant.products.prefix(3), id: \.self) { p in
                        ProductChip(name: p)
                    }
                    if merchant.products.count > 3 {
                        Text("+\(merchant.products.count - 3)")
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textSecondary)
                    }
                    Spacer(minLength: 0)
                }
            }

            Button(action: onOpenDetail) {
                Text("상세보기")
                    .font(AppTypography.button)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: AppSize.buttonHeight)
                    .background(RoundedRectangle(cornerRadius: AppRadius.button).fill(AppColor.primary))
            }
            .buttonStyle(.plain)
        }
        .padding(AppSpacing.lg)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.cardLarge).fill(AppColor.background)
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.cardLarge).stroke(AppColor.divider, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.12), radius: 12, x: 0, y: 4)
    }
}

#Preview {
    ZStack {
        Color.gray.opacity(0.2).ignoresSafeArea()
        MerchantPreviewCard(
            merchant: DummyMerchantSeed.allMerchants[0],
            onClose: {},
            onOpenDetail: {}
        )
        .padding()
        .environment(FavoritesStore.previewInstance())
    }
}
