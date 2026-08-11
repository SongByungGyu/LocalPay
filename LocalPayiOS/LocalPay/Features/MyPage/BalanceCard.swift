import SwiftUI

/// 상품권/지역화폐 잔액 카드. 실제 잔액 API 는 붙지 않음 - DEMO 표시. CLAUDE.md §21.
struct BalanceCard: View {
    enum Wallet {
        case onnuriDigital
        case anyangSarangPay

        var title: String {
            switch self {
            case .onnuriDigital:   return "디지털 온누리"
            case .anyangSarangPay: return "안양사랑페이"
            }
        }

        var iconName: String {
            switch self {
            case .onnuriDigital:   return "ticket.fill"
            case .anyangSarangPay: return "creditcard.fill"
            }
        }

        var color: Color {
            switch self {
            case .onnuriDigital:   return AppColor.onnuri
            case .anyangSarangPay: return AppColor.localCurrency
            }
        }

        var officialCTA: String { "공식 앱에서 확인" }

        var demoBalance: Int {
            switch self {
            case .onnuriDigital:   return 128_500
            case .anyangSarangPay: return 43_200
            }
        }
    }

    let wallet: Wallet
    let showsDemoAmount: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            HStack(spacing: 6) {
                Image(systemName: wallet.iconName)
                    .foregroundStyle(wallet.color)
                Text(wallet.title)
                    .font(AppTypography.body.weight(.semibold))
                    .foregroundStyle(AppColor.textPrimary)
                Spacer()
                Text("DEMO")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(wallet.color)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(wallet.color.opacity(0.15)))
            }

            if showsDemoAmount {
                Text("\(formatted(wallet.demoBalance))원")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundStyle(AppColor.textPrimary)
                Text("실제 잔액이 아닌 예시 금액입니다.")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColor.textSecondary)
            } else {
                Text("잔액 연동 준비 중")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textSecondary)
            }

            Button {} label: {
                HStack {
                    Image(systemName: "arrow.up.right.square")
                    Text(wallet.officialCTA)
                }
                .font(AppTypography.chip.weight(.semibold))
                .foregroundStyle(wallet.color)
            }
            .buttonStyle(.plain)
            .disabled(true)
        }
        .padding(AppSpacing.lg)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.surface)
        )
    }

    private func formatted(_ n: Int) -> String {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        return f.string(from: NSNumber(value: n)) ?? "\(n)"
    }
}

#Preview {
    VStack {
        BalanceCard(wallet: .onnuriDigital, showsDemoAmount: true)
        BalanceCard(wallet: .anyangSarangPay, showsDemoAmount: false)
    }.padding()
}
