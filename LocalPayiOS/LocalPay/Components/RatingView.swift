import SwiftUI

/// 별점 + 후기 수 표기. CLAUDE.md §15, §16, §19.
struct RatingView: View {
    let rating: Double
    let reviewCount: Int
    var showsReviewCount: Bool = true

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: "star.fill")
                .foregroundStyle(.yellow)
                .font(.system(size: 13))
            Text(String(format: "%.1f", rating))
                .font(AppTypography.chip.weight(.semibold))
                .foregroundStyle(AppColor.textPrimary)
            if showsReviewCount {
                Text("(\(reviewCount))")
                    .font(AppTypography.chip)
                    .foregroundStyle(AppColor.textSecondary)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("별점 \(String(format: "%.1f", rating))점, 후기 \(reviewCount)개")
    }
}

#Preview {
    RatingView(rating: 4.6, reviewCount: 128)
}
