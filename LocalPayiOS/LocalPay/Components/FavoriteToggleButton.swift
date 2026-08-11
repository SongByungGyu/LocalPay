import SwiftUI

/// 즐겨찾기 하트 버튼. Phase 5 에서 FavoritesStore 와 연결된다.
struct FavoriteToggleButton: View {
    let isFavorite: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: isFavorite ? "heart.fill" : "heart")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(isFavorite ? AppColor.error : AppColor.textSecondary)
                .frame(width: AppSize.touchTargetMin, height: AppSize.touchTargetMin)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isFavorite ? "즐겨찾기 해제" : "즐겨찾기 추가")
    }
}

#Preview {
    HStack {
        FavoriteToggleButton(isFavorite: false, action: {})
        FavoriteToggleButton(isFavorite: true, action: {})
    }
}
