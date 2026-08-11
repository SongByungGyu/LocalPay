import Foundation

/// 사람이 읽기 좋은 상대·짧은 날짜 포맷.
enum DateHelper {

    /// 예: "오늘", "어제", "3일 전", "지난주", "3주 전", "2026.06"
    static func relative(_ date: Date, now: Date = .init()) -> String {
        let cal = Calendar(identifier: .gregorian)
        let diff = cal.dateComponents([.day], from: cal.startOfDay(for: date), to: cal.startOfDay(for: now))
        let days = diff.day ?? 0
        switch days {
        case ..<0:  return shortDate(date)
        case 0:     return "오늘"
        case 1:     return "어제"
        case 2...6: return "\(days)일 전"
        case 7...13:return "지난주"
        case 14...29: return "\(days / 7)주 전"
        default:    return shortDate(date)
        }
    }

    static func shortDate(_ date: Date) -> String {
        let df = DateFormatter()
        df.locale = Locale(identifier: "ko_KR")
        df.dateFormat = "yyyy.MM.dd"
        return df.string(from: date)
    }
}
