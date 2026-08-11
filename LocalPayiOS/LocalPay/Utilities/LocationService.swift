import CoreLocation
import Foundation
import Observation

/// 위치 권한 상태. UI 에서 화면 분기용.
enum LocationPermission: Hashable {
    case unknown        // 아직 시스템에 요청 안 됨 or 판단 전
    case denied         // 사용자 거부 or Restricted
    case granted        // whenInUse / always
}

/// CoreLocation 얇은 래퍼. CLAUDE.md §10.
///
/// - 위치 권한 거절 상태에서도 앱이 동작해야 하므로, 실패 시 안양 기본 좌표를 fallback 으로 노출한다.
/// - 지도 화면 진입 시 `requestWhenInUse()` 를 호출하고, 이후 마지막 위치를 최대 1회 갱신한다.
@Observable
final class LocationService: NSObject, CLLocationManagerDelegate {

    /// 마지막으로 알려진 사용자 위치. 없으면 nil.
    private(set) var lastKnownLocation: CLLocationCoordinate2D?

    /// 현재 권한 상태.
    private(set) var permission: LocationPermission = .unknown

    /// 화면이 fallback 지역(안양) 을 쓰고 있는지.
    var isUsingFallback: Bool {
        lastKnownLocation == nil
    }

    /// 지도에서 초기 표시에 사용할 좌표. 실측 위치 없으면 안양.
    var effectiveCoordinate: CLLocationCoordinate2D {
        lastKnownLocation ?? MapRegion.anyangDefault.center
    }

    private let manager: CLLocationManager

    override init() {
        self.manager = CLLocationManager()
        super.init()
        self.manager.delegate = self
        self.manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        syncPermission(manager.authorizationStatus)
    }

    /// 지도 진입 시 호출. 필요 시 권한 프롬프트를 띄운다.
    func requestWhenInUse() {
        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .authorizedAlways, .authorizedWhenInUse:
            manager.requestLocation()
        default:
            break
        }
    }

    // MARK: - CLLocationManagerDelegate

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        syncPermission(manager.authorizationStatus)
        if permission == .granted {
            manager.requestLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let last = locations.last else { return }
        lastKnownLocation = last.coordinate
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Simulator 에서 위치가 없을 수 있음. fallback 유지.
    }

    // MARK: - Private

    private func syncPermission(_ status: CLAuthorizationStatus) {
        switch status {
        case .notDetermined:
            permission = .unknown
        case .restricted, .denied:
            permission = .denied
        case .authorizedAlways, .authorizedWhenInUse:
            permission = .granted
        @unknown default:
            permission = .unknown
        }
    }
}
