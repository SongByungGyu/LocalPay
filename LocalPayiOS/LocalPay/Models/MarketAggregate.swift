import CoreLocation
import Foundation

/// 시장/상점가 단위 aggregate. Phase 13 Gate 3-C.
///
/// Backend `GET /api/v1/markets/map` 응답과 1:1 매칭.
/// 개별 매장 (Merchant) 이 아닌 시장 대표 마커 렌더링용.
///
/// 시장 마커 탭 → 매장 리스트 API (`/api/v1/markets/{id}/merchants`) 로 상세 fetch.
struct MarketAggregate: Identifiable, Hashable, Codable, Sendable {
    let id: String              // "market:<slug>"
    let name: String
    let latitude: Double
    let longitude: Double
    let merchantCount: Int
    let paperCount: Int
    let digitalCount: Int
    let locationSource: String?
    let locationPrecision: String   // "market_level"
    let locationConfidence: Double?

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}
