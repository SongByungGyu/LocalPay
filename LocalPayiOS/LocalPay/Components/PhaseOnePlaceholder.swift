import SwiftUI

/// Phase 1 동안 각 Tab 이 아직 비어있음을 사용자·개발자에게 명시적으로 보여주는 자리표시자.
///
/// - Phase 진행 시 이 컴포넌트로 렌더링되던 화면을 실제 View 로 교체한다.
/// - "DEMO" 뱃지로 실제 서비스 데이터가 아님을 상기시킨다. CLAUDE.md §12.
struct PhaseOnePlaceholder: View {
    let title: String
    let subtitle: String
    let iconName: String

    var body: some View {
        ZStack {
            AppColor.background.ignoresSafeArea()

            VStack(spacing: AppSpacing.lg) {
                Image(systemName: iconName)
                    .font(.system(size: 56))
                    .foregroundStyle(AppColor.primary)

                VStack(spacing: AppSpacing.xs) {
                    Text(title)
                        .font(AppTypography.navigationTitle)
                        .foregroundStyle(AppColor.textPrimary)
                    Text(subtitle)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColor.textSecondary)
                        .multilineTextAlignment(.center)
                }

                DemoBadge()
            }
            .padding(.horizontal, AppSpacing.lg)
        }
    }
}

/// 현재 화면이 Dummy 상태임을 항상 명시. CLAUDE.md §12.
struct DemoBadge: View {
    var body: some View {
        Text("DEMO 예시 데이터")
            .font(AppTypography.chip)
            .foregroundStyle(AppColor.primary)
            .padding(.horizontal, AppSpacing.md)
            .padding(.vertical, AppSpacing.xs)
            .background(
                Capsule().fill(AppColor.primary.opacity(0.12))
            )
    }
}

#Preview {
    PhaseOnePlaceholder(
        title: "지도",
        subtitle: "Phase 2 에서 지도·마커·필터가 여기에 추가됩니다.",
        iconName: "map.fill"
    )
}
