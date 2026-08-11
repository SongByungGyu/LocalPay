import SwiftUI

/// 지도 위 Merchant Marker. 색상 + 아이콘 조합으로 결제수단을 구분한다. CLAUDE.md §8.
struct MerchantMarker: View {
    let badge: PaymentBadgeKind
    let category: MerchantCategory
    let isSelected: Bool

    var body: some View {
        let style = PaymentBadgeStyle(badge)

        ZStack {
            // Pin body
            Circle()
                .fill(style.color)
                .frame(width: isSelected ? 46 : 36, height: isSelected ? 46 : 36)
                .shadow(color: style.color.opacity(0.35), radius: isSelected ? 8 : 4, x: 0, y: 2)

            // Inner white ring
            Circle()
                .stroke(Color.white, lineWidth: isSelected ? 3 : 2)
                .frame(width: isSelected ? 46 : 36, height: isSelected ? 46 : 36)

            // Category icon (색상 외 정보 전달)
            Image(systemName: category.iconName)
                .font(.system(size: isSelected ? 20 : 16, weight: .bold))
                .foregroundStyle(.white)

            // Payment-kind tiny indicator dot (오른쪽 위 코너)
            if badge != .none {
                Image(systemName: style.iconName)
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(style.color)
                    .padding(3)
                    .background(Circle().fill(Color.white))
                    .offset(x: isSelected ? 16 : 12, y: isSelected ? -16 : -12)
            }
        }
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isSelected)
        .accessibilityLabel("\(category.title), \(PaymentBadgeStyle(badge).shortLabel) 사용")
    }
}

#Preview {
    HStack(spacing: 20) {
        MerchantMarker(badge: .onnuri, category: .restaurant, isSelected: false)
        MerchantMarker(badge: .localCurrency, category: .cafe, isSelected: true)
        MerchantMarker(badge: .both, category: .market, isSelected: false)
    }
    .padding()
    .background(Color.gray.opacity(0.2))
}
