import SwiftUI

/// Merchant 상세 화면. CLAUDE.md §16, §17.
struct MerchantDetailView: View {
    let merchantId: String

    @State private var viewModel: MerchantDetailViewModel
    @Environment(FavoritesStore.self) private var favorites
    @Environment(ReviewsStore.self) private var reviewsStore
    @State private var showComposer = false

    init(merchantId: String) {
        self.merchantId = merchantId
        _viewModel = State(initialValue: MerchantDetailViewModel(merchantId: merchantId))
    }

    var body: some View {
        Group {
            if let m = viewModel.merchant {
                content(for: m)
            } else if viewModel.isLoading {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.loadError != nil {
                EmptyStateView(
                    iconName: "exclamationmark.triangle",
                    title: "정보를 불러오지 못했어요",
                    subtitle: "잠시 후 다시 시도해 주세요.",
                    actionTitle: "다시 시도"
                ) {
                    Task { await viewModel.load() }
                }
            } else {
                Color.clear
            }
        }
        .background(AppColor.background)
        .navigationBarTitleDisplayMode(.inline)
        .task { await viewModel.load() }
        .sheet(isPresented: $showComposer) {
            if let m = viewModel.merchant {
                ReviewComposerView(
                    merchantId: m.id,
                    supportedPaymentTypes: m.supportedPaymentTypes,
                    onSubmit: { newReview in
                        reviewsStore.append(newReview, for: m.id)
                        showComposer = false
                    }
                )
                .presentationDetents([.medium, .large])
            }
        }
    }

    @ViewBuilder
    private func content(for m: Merchant) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.xl) {
                headerBanner(for: m)
                headerInfo(for: m)
                Divider().background(AppColor.divider)

                paymentSection(for: m)
                productsSection(for: m)
                infoSection(for: m)
                recentPaymentsSection(for: m)
                reviewsSection(for: m)
            }
            .padding(.horizontal, AppSpacing.lg)
            .padding(.bottom, AppSpacing.xxl)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                FavoriteToggleButton(
                    isFavorite: favorites.isFavorite(m.id),
                    action: { favorites.toggle(m.id) }
                )
            }
        }
    }

    // MARK: - Header

    @ViewBuilder
    private func headerBanner(for m: Merchant) -> some View {
        ZStack {
            LinearGradient(
                colors: [PaymentBadgeStyle(m.paymentBadge).color.opacity(0.35),
                         PaymentBadgeStyle(m.paymentBadge).color.opacity(0.1)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            VStack {
                Image(systemName: m.category.iconName)
                    .font(.system(size: 56, weight: .semibold))
                    .foregroundStyle(PaymentBadgeStyle(m.paymentBadge).color)
            }
        }
        .frame(height: 160)
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.cardLarge))
        .padding(.top, AppSpacing.md)
    }

    @ViewBuilder
    private func headerInfo(for m: Merchant) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(m.name)
                .font(AppTypography.navigationTitle)
                .foregroundStyle(AppColor.textPrimary)
            HStack(spacing: 6) {
                Text(m.category.title)
                    .font(AppTypography.chip)
                    .foregroundStyle(AppColor.textSecondary)
                Text("·")
                    .foregroundStyle(AppColor.textSecondary)
                RatingView(rating: m.rating, reviewCount: reviewCount(for: m))
                Text("·")
                    .foregroundStyle(AppColor.textSecondary)
                Text(DistanceFormatter.short(fromMeters: m.distanceMeters))
                    .font(AppTypography.chip)
                    .foregroundStyle(AppColor.textSecondary)
            }
            if let desc = m.description {
                Text(desc)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textPrimary)
                    .padding(.top, 4)
            }
        }
    }

    // MARK: - Sections

    @ViewBuilder
    private func paymentSection(for m: Merchant) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "사용 가능한 결제", accessory: "DEMO")
            VStack(alignment: .leading, spacing: 6) {
                ForEach(m.supportedPaymentTypes, id: \.self) { p in
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(AppColor.success)
                        Text("\(p.displayName) 가능")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColor.textPrimary)
                    }
                }
                if let name = m.localCurrencyName, m.supportsLocalCurrency {
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(AppColor.success)
                        Text("\(name) 가능")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColor.textPrimary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func productsSection(for m: Merchant) -> some View {
        if !m.products.isEmpty {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                SectionHeader(title: "판매 상품")
                ProductChipFlow(products: m.products)
            }
        }
    }

    @ViewBuilder
    private func infoSection(for m: Merchant) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "가게 정보")
            infoRow(icon: "mappin.circle.fill", label: m.address)
            if let phone = m.phone {
                infoRow(icon: "phone.circle.fill", label: phone)
            }
            if let bh = m.businessHours {
                infoRow(icon: "clock.fill", label: bh.summary)
                if let closed = bh.closedNote {
                    infoRow(icon: "calendar", label: closed)
                }
            }
            if let market = m.marketName {
                infoRow(icon: "storefront.fill", label: "\(market) 내")
            }
            if let ts = m.lastVerifiedAt {
                infoRow(icon: "checkmark.seal.fill", label: "최근 정보 확인: \(DateHelper.shortDate(ts))")
            }
        }
    }

    @ViewBuilder
    private func infoRow(icon: String, label: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: icon)
                .foregroundStyle(AppColor.primary)
                .frame(width: 20)
            Text(label)
                .font(AppTypography.body)
                .foregroundStyle(AppColor.textPrimary)
            Spacer(minLength: 0)
        }
    }

    @ViewBuilder
    private func recentPaymentsSection(for m: Merchant) -> some View {
        if !m.recentPayments.isEmpty {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                SectionHeader(title: "최근 결제 확인", accessory: "DEMO")
                VStack(spacing: AppSpacing.xs) {
                    ForEach(m.recentPayments) { p in
                        HStack(spacing: 8) {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundStyle(AppColor.success)
                            Text("\(DateHelper.relative(p.succeededAt)) \(p.paymentType.displayName) 결제 성공")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColor.textPrimary)
                            if let note = p.note {
                                Text("· \(note)")
                                    .font(AppTypography.chip)
                                    .foregroundStyle(AppColor.textSecondary)
                            }
                            Spacer(minLength: 0)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func reviewsSection(for m: Merchant) -> some View {
        let userReviews = reviewsStore.userReviews(for: m.id)
        let combined = userReviews + m.reviews

        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "후기", accessory: "\(reviewCount(for: m))개")
            if combined.isEmpty {
                Text("아직 등록된 후기가 없어요. 첫 후기를 남겨보세요.")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textSecondary)
                    .padding(.vertical, AppSpacing.md)
            } else {
                VStack(spacing: AppSpacing.sm) {
                    ForEach(combined) { r in
                        ReviewCard(review: r)
                    }
                }
            }
            Button(action: { showComposer = true }) {
                HStack {
                    Image(systemName: "square.and.pencil")
                    Text("후기 작성하기")
                }
                .font(AppTypography.button)
                .foregroundStyle(AppColor.primary)
                .frame(maxWidth: .infinity)
                .frame(height: AppSize.buttonHeight)
                .background(RoundedRectangle(cornerRadius: AppRadius.button).stroke(AppColor.primary, lineWidth: 1.5))
            }
            .buttonStyle(.plain)
        }
    }

    private func reviewCount(for m: Merchant) -> Int {
        m.reviewCount + reviewsStore.userReviews(for: m.id).count
    }
}

#Preview {
    NavigationStack {
        MerchantDetailView(merchantId: DummyMerchantSeed.allMerchants[0].id)
    }
    .environment(FavoritesStore.previewInstance())
    .environment(ReviewsStore.previewInstance())
}
