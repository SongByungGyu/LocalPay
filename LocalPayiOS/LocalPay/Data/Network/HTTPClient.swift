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
        #if DEBUG
        print("[HTTPClient] GET \(request.url?.absoluteString ?? "?")")
        #endif

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            // URLSession task 가 `Task.cancel()` 로 취소된 경우.
            // 이건 정상 취소지 오류가 아니므로 Swift-native CancellationError 로 변환해
            // 호출부의 `catch is CancellationError` 로 조용히 걸리도록 한다.
            if let urlErr = error as? URLError, urlErr.code == .cancelled {
                #if DEBUG
                print("[HTTPClient] cancelled: \(request.url?.absoluteString ?? "?")")
                #endif
                throw CancellationError()
            }
            #if DEBUG
            print("[HTTPClient] ✗ transport error: \(error)")
            #endif
            throw NetworkError.transport(underlying: error)
        }

        guard let http = response as? HTTPURLResponse else {
            #if DEBUG
            print("[HTTPClient] ✗ invalid response type")
            #endif
            throw NetworkError.invalidResponse
        }
        #if DEBUG
        print("[HTTPClient] ← HTTP \(http.statusCode) bytes=\(data.count)")
        #endif
        guard (200..<300).contains(http.statusCode) else {
            #if DEBUG
            let bodyPreview = String(data: data.prefix(500), encoding: .utf8) ?? ""
            print("[HTTPClient] ✗ HTTP \(http.statusCode) body=\(bodyPreview)")
            #endif
            throw NetworkError.httpStatus(
                code: http.statusCode,
                body: String(data: data, encoding: .utf8)
            )
        }

        do {
            let decoded = try decoder.decode(T.self, from: data)
            #if DEBUG
            if let list = decoded as? [Any] {
                print("[HTTPClient] ✓ decoded \(list.count) items")
            } else {
                print("[HTTPClient] ✓ decoded \(T.self)")
            }
            #endif
            return decoded
        } catch {
            #if DEBUG
            print("[HTTPClient] ✗ decoding failed: \(error)")
            #endif
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
