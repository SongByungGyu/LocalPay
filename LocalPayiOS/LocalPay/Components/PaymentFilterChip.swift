import SwiftUI

/// 지도 상단의 결제수단 필터 Chip 4종을 가로로 나열.
struct PaymentFilterBar: View {
    @Binding var selection: PaymentFilter

    var body: some View {
        HStack(spacing: AppSpacing.sm) {
            ForEach(PaymentFilter.allCases) { filter in
                PaymentFilterChip(
                    filter: filter,
                    isSelected: selection == filter,
                    action: { selection = filter }
                )
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("결제수단 필터")
    }
}

struct PaymentFilterChip: View {
    let filter: PaymentFilter
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(filter.title)
                .font(AppTypography.chip)
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
    @Previewable @State var s: PaymentFilter = .all
    PaymentFilterBar(selection: $s)
        .padding()
}
