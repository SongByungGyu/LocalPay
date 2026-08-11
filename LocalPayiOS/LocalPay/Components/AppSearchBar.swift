import SwiftUI

/// 지도 상단 Floating SearchBar. Tap 시 검색 화면으로 이동시키는 용도.
struct AppSearchBar: View {
    let placeholder: String
    var showsChevron: Bool = false
    var onTap: (() -> Void)? = nil
    @Binding var text: String
    /// nil 이면 read-only(tap-to-navigate) 모드.
    let onSubmit: (() -> Void)?

    var body: some View {
        HStack(spacing: AppSpacing.sm) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(AppColor.textSecondary)

            if onSubmit != nil {
                TextField(placeholder, text: $text)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textPrimary)
                    .submitLabel(.search)
                    .onSubmit { onSubmit?() }
                if !text.isEmpty {
                    Button {
                        text = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(AppColor.textSecondary)
                    }
                    .buttonStyle(.plain)
                }
            } else {
                Text(text.isEmpty ? placeholder : text)
                    .font(AppTypography.body)
                    .foregroundStyle(text.isEmpty ? AppColor.textSecondary : AppColor.textPrimary)
                    .lineLimit(1)
                Spacer(minLength: 0)
                if showsChevron {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(AppColor.textSecondary)
                }
            }
        }
        .padding(.horizontal, AppSpacing.md)
        .frame(height: 44)
        .background(
            RoundedRectangle(cornerRadius: 22).fill(AppColor.background)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22).stroke(AppColor.divider, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.08), radius: 6, x: 0, y: 2)
        .contentShape(RoundedRectangle(cornerRadius: 22))
        .onTapGesture {
            onTap?()
        }
    }
}

#Preview {
    @Previewable @State var t = ""
    VStack(spacing: 12) {
        AppSearchBar(placeholder: "가게, 상품, 시장을 검색해보세요", showsChevron: true, text: $t, onSubmit: nil)
        AppSearchBar(placeholder: "검색어를 입력하세요", text: $t, onSubmit: { })
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
