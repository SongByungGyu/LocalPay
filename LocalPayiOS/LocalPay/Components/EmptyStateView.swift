import SwiftUI

/// 빈 상태 / 오류 상태에서 공통으로 쓰는 안내 View. CLAUDE.md §24.
struct EmptyStateView: View {
    let iconName: String
    let title: String
    let subtitle: String?
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: AppSpacing.md) {
            Image(systemName: iconName)
                .font(.system(size: 44))
                .foregroundStyle(AppColor.textSecondary)
            Text(title)
                .font(AppTypography.sectionTitle)
                .foregroundStyle(AppColor.textPrimary)
                .multilineTextAlignment(.center)
            if let subtitle {
                Text(subtitle)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textSecondary)
                    .multilineTextAlignment(.center)
            }
            if let actionTitle, let action {
                Button(action: action) {
                    Text(actionTitle)
                        .font(AppTypography.button)
                        .foregroundStyle(.white)
                        .padding(.horizontal, AppSpacing.lg)
                        .frame(height: AppSize.buttonHeight)
                        .background(RoundedRectangle(cornerRadius: AppRadius.button).fill(AppColor.primary))
                }
                .buttonStyle(.plain)
                .padding(.top, AppSpacing.sm)
            }
        }
        .padding(AppSpacing.xl)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppColor.background)
    }
}

/// 로딩 스피너 + 짧은 메시지.
struct LoadingView: View {
    let message: String

    init(message: String = "불러오는 중...") {
        self.message = message
    }

    var body: some View {
        VStack(spacing: AppSpacing.md) {
            ProgressView()
                .scaleEffect(1.2)
            Text(message)
                .font(AppTypography.body)
                .foregroundStyle(AppColor.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppColor.background)
    }
}

#Preview("Empty") {
    EmptyStateView(
        iconName: "magnifyingglass",
        title: "검색 결과가 없어요",
        subtitle: "다른 키워드로 검색해 보시겠어요?",
        actionTitle: "다시 시도",
        action: {}
    )
}

#Preview("Loading") {
    LoadingView()
}
