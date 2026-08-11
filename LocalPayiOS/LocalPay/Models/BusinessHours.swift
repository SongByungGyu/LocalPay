import Foundation

/// 매장 영업시간. Dummy 단계라 문자열 요약으로 충분.
struct BusinessHours: Hashable, Codable, Sendable {
    /// 예: "매일 09:00 - 21:00"
    let summary: String
    /// 예: "일요일 휴무"
    let closedNote: String?

    init(summary: String, closedNote: String? = nil) {
        self.summary = summary
        self.closedNote = closedNote
    }
}
