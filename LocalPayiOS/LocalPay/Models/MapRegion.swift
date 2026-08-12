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

/// 지도 카메라의 사각 영역 (Bounding Box). WGS84.
/// 서버 `/api/v1/merchants/map?north&south&east&west` 파라미터와 1:1.
/// MapKit `MKCoordinateRegion` · KakaoMap 어디에도 종속되지 않는다.
struct MapBBox: Hashable, Sendable {
    var north: Double
    var south: Double
    var east: Double
    var west: Double

    /// 서버 안전장치와 동일한 상한 (docs/API_SCHEMA · backend MAX_BBOX_DEGREES).
    /// 이보다 크면 서버가 400 을 던지므로 클라이언트에서도 요청 자체를 스킵.
    static let maxSpanDegrees: Double = 6.0

    var isValid: Bool {
        north > south
            && east > west
            && (north - south) <= Self.maxSpanDegrees
            && (east - west) <= Self.maxSpanDegrees
    }

    /// 두 BBOX 가 사실상 같은 영역인지 판단. 카메라 미세 이동으로 인한 중복 요청을 걸러낸다.
    /// tolerance 는 위·경도 각도 (기본 0.0005° ≈ 55m).
    func isApproximatelyEqual(to other: MapBBox, tolerance: Double = 0.0005) -> Bool {
        abs(north - other.north) < tolerance
            && abs(south - other.south) < tolerance
            && abs(east - other.east) < tolerance
            && abs(west - other.west) < tolerance
    }
}

extension MapRegion {
    /// MapRegion (center + delta) → BBOX 변환.
    var bbox: MapBBox {
        MapBBox(
            north: centerLatitude + latitudeDelta / 2,
            south: centerLatitude - latitudeDelta / 2,
            east: centerLongitude + longitudeDelta / 2,
            west: centerLongitude - longitudeDelta / 2
        )
    }
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
