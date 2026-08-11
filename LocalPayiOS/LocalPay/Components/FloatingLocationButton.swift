import SwiftUI

/// 지도 우측 하단 현재위치 Floating Button. CLAUDE.md §10.
struct FloatingLocationButton: View {
    let isPermissionGranted: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: isPermissionGranted ? "location.fill" : "location.slash")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(isPermissionGranted ? AppColor.primary : AppColor.textSecondary)
                .frame(width: 48, height: 48)
                .background(
                    Circle().fill(AppColor.background)
                )
                .overlay(
                    Circle().stroke(AppColor.divider, lineWidth: 1)
                )
                .shadow(color: Color.black.opacity(0.15), radius: 6, x: 0, y: 2)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isPermissionGranted ? "현재 위치로 이동" : "위치 권한이 필요합니다")
    }
}

#Preview {
    HStack(spacing: 20) {
        FloatingLocationButton(isPermissionGranted: true, action: {})
        FloatingLocationButton(isPermissionGranted: false, action: {})
    }
    .padding()
}
