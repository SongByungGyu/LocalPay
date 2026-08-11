import SwiftUI

/// 판매 상품 이름 Chip. CLAUDE.md §16.
struct ProductChip: View {
    let name: String

    var body: some View {
        Text(name)
            .font(AppTypography.chip)
            .foregroundStyle(AppColor.textPrimary)
            .padding(.horizontal, AppSpacing.md)
            .padding(.vertical, 6)
            .background(
                Capsule().fill(AppColor.surface)
            )
            .overlay(
                Capsule().stroke(AppColor.divider, lineWidth: 1)
            )
    }
}

/// 상품 목록을 자연스럽게 줄바꿈해서 보여주는 flow layout.
struct ProductChipFlow: View {
    let products: [String]

    var body: some View {
        FlowLayout(spacing: AppSpacing.sm) {
            ForEach(products, id: \.self) { p in
                ProductChip(name: p)
            }
        }
    }
}

/// 간단한 flow(wrap) layout. iOS 16+ Layout protocol 사용.
struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? .infinity
        let rows = arrange(subviews: subviews, in: width)
        let height = rows.map { $0.height }.reduce(0) { $0 + $1 } + spacing * CGFloat(max(rows.count - 1, 0))
        return CGSize(width: width == .infinity ? rows.map { $0.width }.max() ?? 0 : width, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let rows = arrange(subviews: subviews, in: bounds.width)
        var y = bounds.minY
        for row in rows {
            var x = bounds.minX
            for item in row.items {
                item.view.place(at: CGPoint(x: x, y: y), anchor: .topLeading, proposal: ProposedViewSize(width: item.size.width, height: item.size.height))
                x += item.size.width + spacing
            }
            y += row.height + spacing
        }
    }

    private struct RowItem {
        let view: LayoutSubview
        let size: CGSize
    }
    private struct Row {
        var items: [RowItem] = []
        var width: CGFloat = 0
        var height: CGFloat = 0
    }

    private func arrange(subviews: Subviews, in maxWidth: CGFloat) -> [Row] {
        var rows: [Row] = []
        var current = Row()
        for sv in subviews {
            let size = sv.sizeThatFits(.unspecified)
            let projected = current.width + (current.items.isEmpty ? 0 : spacing) + size.width
            if projected > maxWidth && !current.items.isEmpty {
                rows.append(current)
                current = Row()
            }
            current.items.append(RowItem(view: sv, size: size))
            current.width = current.items.reduce(0) { $0 + $1.size.width } + spacing * CGFloat(max(current.items.count - 1, 0))
            current.height = max(current.height, size.height)
        }
        if !current.items.isEmpty { rows.append(current) }
        return rows
    }
}

#Preview {
    ProductChipFlow(products: ["삼겹살", "목살", "한우 등심", "선물세트", "양념갈비", "돼지갈비"])
        .padding()
        .frame(width: 320)
}
