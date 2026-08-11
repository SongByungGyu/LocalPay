import SwiftUI

/// 결제수단 뱃지의 색상·아이콘·라벨 스타일. 색상 외에도 아이콘 차이로 정보를 전달한다. CLAUDE.md §8.
enum PaymentBadgeStyle {
    case onnuri
    case localCurrency
    case both
    case none

    init(_ kind: PaymentBadgeKind) {
        switch kind {
        case .onnuri:         self = .onnuri
        case .localCurrency:  self = .localCurrency
        case .both:           self = .both
        case .none:           self = .none
        }
    }

    var color: Color {
        switch self {
        case .onnuri:         return AppColor.onnuri
        case .localCurrency:  return AppColor.localCurrency
        case .both:           return AppColor.both
        case .none:           return AppColor.textSecondary
        }
    }

    var iconName: String {
        switch self {
        case .onnuri:         return "ticket.fill"
        case .localCurrency:  return "creditcard.fill"
        case .both:           return "star.circle.fill"
        case .none:           return "questionmark.circle.fill"
        }
    }

    var shortLabel: String {
        switch self {
        case .onnuri:         return "온누리"
        case .localCurrency:  return "지역화폐"
        case .both:           return "온누리·지역화폐"
        case .none:           return "미확인"
        }
    }
}
