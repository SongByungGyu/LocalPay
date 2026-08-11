import SwiftUI

/// 지역화폐 혜택 카드. CLAUDE.md §23.
struct CurrencyPolicyCard: View {

    struct Info {
        let title: String        // "안양사랑페이"
        let chargeBonusPercent: Int  // 예: 7
        let monthlyChargeCapKRW: Int // 예: 300_000
        let referenceMonth: String   // "2026.08"
    }

    let info: Info

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.md) {
            HStack {
                Image(systemName: "gift.fill")
                    .foregroundStyle(AppColor.localCurrency)
                Text(info.title)
                    .font(AppTypography.body.weight(.semibold))
                    .foregroundStyle(AppColor.textPrimary)
                Spacer()
                Text("DEMO")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(AppColor.localCurrency)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(AppColor.localCurrency.opacity(0.15)))
            }

            HStack(spacing: AppSpacing.md) {
                stat(label: "이번 달 충전 혜택", value: "\(info.chargeBonusPercent)%")
                Divider().frame(height: 32).background(AppColor.divider)
                stat(label: "월 구매한도", value: shortWon(info.monthlyChargeCapKRW))
            }

            Text("정보 기준일 \(info.referenceMonth) · 실제 정책은 지자체 발표를 확인해 주세요.")
                .font(AppTypography.caption)
                .foregroundStyle(AppColor.textSecondary)
        }
        .padding(AppSpacing.lg)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.localCurrency.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.card).stroke(AppColor.localCurrency.opacity(0.25), lineWidth: 1)
        )
    }

    private func stat(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(AppTypography.caption)
                .foregroundStyle(AppColor.textSecondary)
            Text(value)
                .font(AppTypography.sectionTitle)
                .foregroundStyle(AppColor.textPrimary)
        }
    }

    private func shortWon(_ n: Int) -> String {
        if n >= 10_000 {
            let man = n / 10_000
            return "\(man)만원"
        }
        return "\(n)원"
    }
}

#Preview {
    CurrencyPolicyCard(info: .init(
        title: "안양사랑페이",
        chargeBonusPercent: 7,
        monthlyChargeCapKRW: 300_000,
        referenceMonth: "2026.08"
    )).padding()
}
