import SwiftUI

/// 시장 대표 마커. 매장 count 를 라벨로 표시. Phase 13 Gate 3-C.
/// docs/MAP_UX_TODO.md — 개별 매장 마커와 시각적으로 구분되어야 한다.
struct MarketMarker: View {
    let name: String
    let count: Int
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 2) {
            ZStack {
                Circle()
                    .fill(AppColor.primary)
                    .frame(width: isSelected ? 44 : 36, height: isSelected ? 44 : 36)
                    .overlay(
                        Circle().stroke(Color.white, lineWidth: 2)
                    )
                Image(systemName: "storefront.fill")
                    .foregroundStyle(.white)
                    .font(.system(size: isSelected ? 20 : 16, weight: .semibold))
            }
            Text("\(count)")
                .font(.system(size: 11, weight: .bold))
                .foregroundStyle(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Capsule().fill(AppColor.primary))
                .overlay(Capsule().stroke(Color.white, lineWidth: 1))
        }
        .shadow(color: .black.opacity(0.18), radius: 3, x: 0, y: 2)
    }
}
