import SwiftUI

/// 지도 상단 카테고리 가로 스크롤. CLAUDE.md §7.
struct CategoryScrollBar: View {
    @Binding var selection: MerchantCategory

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: AppSpacing.sm) {
                ForEach(MerchantCategory.allCases) { category in
                    CategoryChip(
                        category: category,
                        isSelected: selection == category,
                        action: { selection = category }
                    )
                }
            }
            .padding(.horizontal, AppSpacing.lg)
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("카테고리 필터")
    }
}

struct CategoryChip: View {
    let category: MerchantCategory
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: category.iconName)
                    .font(.system(size: 13, weight: .semibold))
                Text(category.title)
                    .font(AppTypography.chip)
            }
            .foregroundStyle(isSelected ? .white : AppColor.textPrimary)
            .padding(.horizontal, AppSpacing.md)
            .frame(height: AppSize.chipHeight)
            .background(
                Capsule().fill(isSelected ? AppColor.primary : AppColor.surface)
            )
            .overlay(
                Capsule().stroke(isSelected ? Color.clear : AppColor.divider, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

#Preview {
    @Previewable @State var s: MerchantCategory = .all
    CategoryScrollBar(selection: $s)
        .padding(.vertical)
}
