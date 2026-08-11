import SwiftUI

/// 매장 카드/상세에서 사용하는 결제수단 pill. CLAUDE.md §8.
struct PaymentBadge: View {
    let kind: PaymentBadgeKind

    var body: some View {
        let style = PaymentBadgeStyle(kind)
        HStack(spacing: 4) {
            Image(systemName: style.iconName)
                .font(.system(size: 11, weight: .bold))
            Text(style.shortLabel)
                .font(AppTypography.chip)
        }
        .foregroundStyle(style.color)
        .padding(.horizontal, AppSpacing.md)
        .padding(.vertical, 6)
        .background(
            Capsule().fill(style.color.opacity(0.12))
        )
        .accessibilityElement(children: .combine)
        .accessibilityLabel("결제수단 \(style.shortLabel)")
    }
}

#Preview {
    VStack(spacing: 8) {
        PaymentBadge(kind: .onnuri)
        PaymentBadge(kind: .localCurrency)
        PaymentBadge(kind: .both)
        PaymentBadge(kind: .none)
    }
    .padding()
}
