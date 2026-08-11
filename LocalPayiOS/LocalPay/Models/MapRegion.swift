import CoreLocation
import Foundation

/// MapKit / KakaoMap 어디에도 종속되지 않는 지도 영역 표현. CLAUDE.md §4, §29.
struct MapRegion: Hashable, Sendable {
    var centerLatitude: Double
    var centerLongitude: Double
    var latitudeDelta: Double
    var longitudeDelta: Double

    var center: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: centerLatitude, longitude: centerLongitude)
    }

    /// 안양시 중심 기본 영역. CLAUDE.md §10.
    static let anyangDefault = MapRegion(
        centerLatitude: 37.3943,
        centerLongitude: 126.9568,
        latitudeDelta: 0.03,
        longitudeDelta: 0.03
    )
}

/// 지도에 찍히는 Marker 표현. 실제 지도 SDK 의 Annotation 과 분리한다.
struct MapMarkerModel: Identifiable, Hashable, Sendable {
    let id: String            // Merchant.id 와 동일
    let latitude: Double
    let longitude: Double
    let badge: PaymentBadgeKind
    let category: MerchantCategory
    var isSelected: Bool

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}
