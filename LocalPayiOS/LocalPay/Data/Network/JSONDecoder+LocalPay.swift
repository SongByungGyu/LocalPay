import Foundation

extension JSONDecoder {

    /// LocalPay 백엔드 응답용 Decoder.
    /// - 백엔드는 camelCase 이므로 `keyDecodingStrategy` 는 기본값.
    /// - Date 는 `2026-08-10T06:03:17.625283Z` 처럼 fractional seconds 를 포함할 수 있고,
    ///   `2026-08-10T06:03:17Z` 처럼 없는 경우도 처리해야 하므로 custom strategy 를 쓴다.
    static let localPay: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { container in
            let stringValue = try container.singleValueContainer().decode(String.self)
            if let date = LocalPayDateFormatters.parse(stringValue) {
                return date
            }
            throw DecodingError.dataCorruptedError(
                in: try container.singleValueContainer(),
                debugDescription: "Unsupported ISO-8601 date format: \(stringValue)"
            )
        }
        return decoder
    }()
}

/// ISO-8601 문자열을 관대하게 파싱한다.
/// fractional seconds 포함/미포함, `Z`/오프셋 형태 모두 처리한다.
enum LocalPayDateFormatters {

    private static let withFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    private static let withoutFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    static func parse(_ string: String) -> Date? {
        if let d = withFractional.date(from: string) { return d }
        if let d = withoutFractional.date(from: string) { return d }
        return nil
    }
}
