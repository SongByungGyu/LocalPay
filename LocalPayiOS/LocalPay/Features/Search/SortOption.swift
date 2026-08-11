import Foundation

/// 검색 결과 정렬. CLAUDE.md §18.
enum SortOption: String, CaseIterable, Identifiable {
    case distance
    case rating
    case reviewCount

    var id: String { rawValue }

    var title: String {
        switch self {
        case .distance:    return "거리순"
        case .rating:      return "평점순"
        case .reviewCount: return "후기순"
        }
    }

    func apply(_ list: [Merchant]) -> [Merchant] {
        switch self {
        case .distance:
            return list.sorted { ($0.distanceMeters ?? .greatestFiniteMagnitude) < ($1.distanceMeters ?? .greatestFiniteMagnitude) }
        case .rating:
            return list.sorted { $0.rating > $1.rating }
        case .reviewCount:
            return list.sorted { $0.reviewCount > $1.reviewCount }
        }
    }
}
