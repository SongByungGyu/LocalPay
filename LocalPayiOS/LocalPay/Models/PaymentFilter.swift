import Foundation

/// 지도 상단의 결제수단 필터 Chip. CLAUDE.md §7.
enum PaymentFilter: String, CaseIterable, Identifiable, Hashable, Sendable {
    case all
    case onnuri
    case localCurrency
    case both

    var id: String { rawValue }

    var title: String {
        switch self {
        case .all:            return "전체"
        case .onnuri:         return "온누리"
        case .localCurrency:  return "지역화폐"
        case .both:           return "둘 다"
        }
    }
}
