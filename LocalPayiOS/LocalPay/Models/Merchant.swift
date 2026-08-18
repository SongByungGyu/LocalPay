import CoreLocation
import Foundation

/// 지도 위 가맹점 도메인 모델. CLAUDE.md §11.
///
/// 주의: MapKit / CoreLocation 의 클래스에 강하게 의존하지 않도록 좌표는 원시 Double 로 보관하고,
/// `coordinate` computed property 만 CoreLocation 을 참조한다.
struct Merchant: Identifiable, Hashable, Codable, Sendable {
    let id: String
    let name: String
    let category: MerchantCategory
    let latitude: Double
    let longitude: Double

    let address: String
    let roadAddress: String?
    let phone: String?

    /// 상세화면 헤더/카드에서 사용. 위치 권한 없을 때는 nil.
    var distanceMeters: Double?

    let supportsOnnuri: Bool
    let supportsLocalCurrency: Bool
    /// "안양사랑페이" 같은 지역화폐 브랜드명. 미지원이면 nil.
    let localCurrencyName: String?
    let supportedPaymentTypes: [PaymentType]

    let products: [String]
    let businessHours: BusinessHours?
    let rating: Double            // 0.0 ~ 5.0
    let reviewCount: Int

    let marketName: String?       // 예: "안양중앙시장"
    let description: String?
    let lastVerifiedAt: Date?

    let reviews: [Review]
    let recentPayments: [PaymentVerification]

    // Phase 13 Gate 3-C — 좌표 신뢰도 메타데이터 (docs/LOCATION_PRECISION.md).
    // 서버 응답 optional. Codable 자동 합성이 JSON 에 없으면 nil 로 매핑.
    // DummyMerchantSeed 등 로컬 코드는 nil 세 개 명시 전달.
    let locationSource: String?
    let locationPrecision: String?
    let locationConfidence: Double?

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    /// 시장 centroid 좌표 등 개별 매장이 아닌 근사 위치 (docs/MAP_UX_TODO.md).
    var isMarketLevelLocation: Bool {
        locationPrecision == "market_level"
    }

    /// 결제 수단 표시 헬퍼. Marker 색/아이콘 결정에 사용.
    var paymentBadge: PaymentBadgeKind {
        switch (supportsOnnuri, supportsLocalCurrency) {
        case (true, true):   return .both
        case (true, false):  return .onnuri
        case (false, true):  return .localCurrency
        case (false, false): return .none
        }
    }
}

/// 결제수단 조합 뱃지 종류.
enum PaymentBadgeKind: Hashable, Sendable {
    case onnuri
    case localCurrency
    case both
    case none
}
