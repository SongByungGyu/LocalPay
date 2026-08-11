import CoreLocation
import Foundation

/// 두 좌표 사이의 미터 단위 대략 거리. CLLocation 기반.
enum GeoDistance {
    static func meters(from a: CLLocationCoordinate2D, to b: CLLocationCoordinate2D) -> Double {
        let la = CLLocation(latitude: a.latitude, longitude: a.longitude)
        let lb = CLLocation(latitude: b.latitude, longitude: b.longitude)
        return la.distance(from: lb)
    }
}
