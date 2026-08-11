import SwiftUI

/// 상세화면 등에서 사용하는 섹션 제목. CLAUDE.md §16.
struct SectionHeader: View {
    let title: String
    var accessory: String? = nil

    var body: some View {
        HStack {
            Text(title)
                .font(AppTypography.sectionTitle)
                .foregroundStyle(AppColor.textPrimary)
            Spacer()
            if let accessory {
                Text(accessory)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColor.textSecondary)
            }
        }
    }
}

#Preview {
    SectionHeader(title: "사용 가능한 결제", accessory: "DEMO")
        .padding()
}
