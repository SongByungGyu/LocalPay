import SwiftUI

/// MY 화면. CLAUDE.md §21, §22, §23.
struct MyPageHomeView: View {

    @Environment(FavoritesStore.self) private var favorites
    @Environment(ReviewsStore.self) private var reviews

    /// 개발 편의를 위한 스위치. 실제 잔액 API 는 붙지 않았다는 사실을 상시 노출.
    @State private var showDemoAmounts: Bool = true

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: AppSpacing.xl) {
                    profileHeader
                    statsRow
                    walletSection
                    policyCard
                    settingsSection
                    footerNotice
                }
                .padding(.horizontal, AppSpacing.lg)
                .padding(.vertical, AppSpacing.lg)
            }
            .background(AppColor.background)
            .navigationTitle("MY")
        }
    }

    // MARK: - Sections

    private var profileHeader: some View {
        HStack(spacing: AppSpacing.md) {
            ZStack {
                Circle().fill(AppColor.primary.opacity(0.15))
                Image(systemName: "person.fill")
                    .font(.system(size: 28))
                    .foregroundStyle(AppColor.primary)
            }
            .frame(width: 64, height: 64)

            VStack(alignment: .leading, spacing: 2) {
                Text("병규님")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColor.textPrimary)
                Text("경기 안양시")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textSecondary)
            }
            Spacer()
        }
    }

    private var statsRow: some View {
        HStack(spacing: AppSpacing.sm) {
            statTile(title: "즐겨찾기", value: "\(favorites.count)")
            statTile(title: "내 후기", value: "\(reviews.totalUserReviewCount)")
            statTile(title: "결제 인증", value: "0")
        }
    }

    private func statTile(title: String, value: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 20, weight: .bold))
                .foregroundStyle(AppColor.textPrimary)
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColor.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AppSpacing.md)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.surface)
        )
    }

    private var walletSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.md) {
            HStack {
                SectionHeader(title: "내 상품권")
                Spacer()
                Toggle("DEMO 금액 표시", isOn: $showDemoAmounts)
                    .font(AppTypography.caption)
                    .toggleStyle(.switch)
                    .labelsHidden()
            }
            BalanceCard(wallet: .onnuriDigital, showsDemoAmount: showDemoAmounts)
            BalanceCard(wallet: .anyangSarangPay, showsDemoAmount: showDemoAmounts)
        }
    }

    private var policyCard: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "지역화폐 혜택")
            CurrencyPolicyCard(info: .init(
                title: "안양사랑페이",
                chargeBonusPercent: 7,
                monthlyChargeCapKRW: 300_000,
                referenceMonth: "2026.08"
            ))
        }
    }

    private var settingsSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "설정")
            VStack(spacing: 0) {
                settingRow(icon: "location.fill", title: "기본 지역", trailing: "안양시")
                Divider().background(AppColor.divider)
                settingRow(icon: "bell.fill", title: "알림 설정", trailing: "꺼짐")
                Divider().background(AppColor.divider)
                settingRow(icon: "info.circle.fill", title: "앱 정보", trailing: "v0.1.0")
            }
            .background(
                RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.surface)
            )
        }
    }

    private func settingRow(icon: String, title: String, trailing: String) -> some View {
        HStack(spacing: AppSpacing.md) {
            Image(systemName: icon)
                .foregroundStyle(AppColor.primary)
                .frame(width: 24)
            Text(title)
                .font(AppTypography.body)
                .foregroundStyle(AppColor.textPrimary)
            Spacer()
            Text(trailing)
                .font(AppTypography.caption)
                .foregroundStyle(AppColor.textSecondary)
        }
        .padding(.horizontal, AppSpacing.md)
        .frame(height: 52)
    }

    private var footerNotice: some View {
        Text("현재 앱은 서비스 검증용 Dummy MVP 입니다. 실제 개인 상품권 잔액 · 결제 API 와는 연동되지 않습니다.")
            .font(AppTypography.caption)
            .foregroundStyle(AppColor.textSecondary)
            .multilineTextAlignment(.center)
            .padding(.top, AppSpacing.md)
    }
}

#Preview {
    MyPageHomeView()
        .environment(FavoritesStore.previewInstance(prefilled: ["m-001", "m-002"]))
        .environment(ReviewsStore.previewInstance())
}
