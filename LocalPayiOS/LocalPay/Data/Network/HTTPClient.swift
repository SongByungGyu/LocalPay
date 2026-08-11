import Foundation

/// URLSession + async/await 를 감싼 얇은 GET 전용 클라이언트.
/// 외부 네트워크 라이브러리 사용 금지 원칙(CLAUDE.md §3, §42) 을 지키기 위해 직접 구현한다.
struct HTTPClient {

    let baseURL: URL
    let session: URLSession
    let decoder: JSONDecoder

    init(
        baseURL: URL,
        session: URLSession = .shared,
        decoder: JSONDecoder = .localPay
    ) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = decoder
    }

    /// 지정한 경로에 GET 요청을 보내고 JSON body 를 `T` 로 decode 한다.
    /// - Parameters:
    ///   - path: `/api/v1/merchants` 처럼 앞에 슬래시가 있는 경로
    ///   - query: nil 값은 자동으로 제거된다
    func get<T: Decodable>(_ path: String, query: [String: String?] = [:]) async throws -> T {
        let request = try makeRequest(path: path, query: query)

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw NetworkError.transport(underlying: error)
        }

        guard let http = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw NetworkError.httpStatus(
                code: http.statusCode,
                body: String(data: data, encoding: .utf8)
            )
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decoding(underlying: error)
        }
    }

    // MARK: - Private

    private func makeRequest(path: String, query: [String: String?]) throws -> URLRequest {
        let url = baseURL.appendingPathComponent(path)
        guard var components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            throw NetworkError.invalidURL
        }
        let items = query.compactMap { key, value -> URLQueryItem? in
            guard let value else { return nil }
            return URLQueryItem(name: key, value: value)
        }
        if !items.isEmpty {
            components.queryItems = items
        }
        guard let finalURL = components.url else {
            throw NetworkError.invalidURL
        }
        var req = URLRequest(url: finalURL)
        req.httpMethod = "GET"
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        req.timeoutInterval = 15
        return req
    }
}
