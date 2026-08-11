import Foundation

/// Remote Repository 계층에서 던지는 통합 에러.
/// ViewModel 은 이 타입을 잡아 사용자에게는 `userMessage` 만 노출한다 (기술 문자열 원본 노출 금지).
enum NetworkError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case httpStatus(code: Int, body: String?)
    case decoding(underlying: Error)
    case transport(underlying: Error)

    /// 사용자에게 그대로 보여줘도 안전한 한국어 메시지.
    var userMessage: String {
        switch self {
        case .invalidURL, .invalidResponse:
            return "가맹점 정보를 불러오지 못했습니다."
        case .httpStatus(let code, _):
            if code == 404 {
                return "가맹점 정보를 찾지 못했습니다."
            }
            return "서버와의 통신에 문제가 있습니다. (\(code))"
        case .decoding:
            return "가맹점 정보를 해석하지 못했습니다."
        case .transport:
            return "네트워크 연결이 원활하지 않습니다."
        }
    }

    var errorDescription: String? { userMessage }
}
