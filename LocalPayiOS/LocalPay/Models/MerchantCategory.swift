import Foundation

/// 매장 카테고리. CLAUDE.md §14.
enum MerchantCategory: String, CaseIterable, Codable, Identifiable, Hashable, Sendable {
    case all
    case restaurant
    case cafe
    case pharmacy
    case mart
    case market
    case food
    case beauty
    case life
    case etc

    var id: String { rawValue }

    var title: String {
        switch self {
        case .all:        return "전체"
        case .restaurant: return "음식점"
        case .cafe:       return "카페"
        case .pharmacy:   return "약국"
        case .mart:       return "마트"
        case .market:     return "시장"
        case .food:       return "식품"
        case .beauty:     return "미용"
        case .life:       return "생활"
        case .etc:        return "기타"
        }
    }

    /// SF Symbols 이름.
    var iconName: String {
        switch self {
        case .all:        return "square.grid.2x2.fill"
        case .restaurant: return "fork.knife"
        case .cafe:       return "cup.and.saucer.fill"
        case .pharmacy:   return "cross.case.fill"
        case .mart:       return "cart.fill"
        case .market:     return "storefront.fill"
        case .food:       return "carrot.fill"
        case .beauty:     return "scissors"
        case .life:       return "house.fill"
        case .etc:        return "ellipsis.circle.fill"
        }
    }
}
