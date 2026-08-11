import Foundation

/// 매장이 실제로 받는 결제 수단 종류.
/// CLAUDE.md §12 참고. Dummy 정책이므로 UI 에서는 항상 "DEMO" 를 함께 표시한다.
enum PaymentType: String, CaseIterable, Codable, Identifiable, Hashable, Sendable {
    case onnuriDigital       // 디지털 온누리
    case onnuriPaper         // 지류 온누리
    case onnuriCard          // 카드형 온누리
    case localCurrency       // 지역화폐 (안양사랑페이 등)
    case qr                  // 일반 QR 결제
    case card                // 일반 카드

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .onnuriDigital:  return "디지털 온누리"
        case .onnuriPaper:    return "지류 온누리"
        case .onnuriCard:     return "카드형 온누리"
        case .localCurrency:  return "지역화폐"
        case .qr:             return "QR"
        case .card:           return "카드"
        }
    }

    var isOnnuri: Bool {
        switch self {
        case .onnuriDigital, .onnuriPaper, .onnuriCard: return true
        default: return false
        }
    }

    var isLocalCurrency: Bool { self == .localCurrency }
}
