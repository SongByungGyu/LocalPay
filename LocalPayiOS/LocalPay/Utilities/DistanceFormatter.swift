import Foundation

/// 거리 표시 헬퍼. 1000m 미만은 m, 이상은 km(소수 1자리).
enum DistanceFormatter {
    static func short(fromMeters meters: Double?) -> String {
        guard let m = meters else { return "-" }
        if m < 1000 {
            return "\(Int(m))m"
        } else {
            let km = m / 1000
            return String(format: "%.1fkm", km)
        }
    }
}
