import XCTest
@testable import LocalPay

/// 실 서버(FastAPI + PostGIS) 응답 스키마와 iOS `Merchant` 도메인 모델의 호환성을 보장한다.
/// 특히 fractional seconds(microseconds) 를 포함한 ISO-8601 타임스탬프가 정상 decode 되는지 검증한다.
final class RemoteMerchantRepositoryDecodingTests: XCTestCase {

    // MARK: - Date decoder

    func testDate_withFractionalSeconds_decodes() throws {
        let iso = "2026-08-10T06:03:17.625283Z"
        let date = try XCTUnwrap(LocalPayDateFormatters.parse(iso))
        // sanity: 2026 이후, UTC 오프셋 없이 파싱된 값이어야 한다.
        let comps = Calendar(identifier: .gregorian).dateComponents(
            in: TimeZone(identifier: "UTC")!, from: date
        )
        XCTAssertEqual(comps.year, 2026)
        XCTAssertEqual(comps.month, 8)
        XCTAssertEqual(comps.day, 10)
        XCTAssertEqual(comps.hour, 6)
    }

    func testDate_withoutFractionalSeconds_decodes() throws {
        let iso = "2026-08-11T04:30:00Z"
        XCTAssertNotNil(LocalPayDateFormatters.parse(iso))
    }

    func testDate_invalid_returnsNil() {
        XCTAssertNil(LocalPayDateFormatters.parse("not-a-date"))
    }

    // MARK: - Merchant

    /// 실 서버 `GET /api/v1/merchants/m-001` 응답 축약본.
    /// - fractional seconds 를 포함한 `lastVerifiedAt`, `reviews[].createdAt`, `recentPayments[].succeededAt` 를 그대로 사용한다.
    func testMerchant_realServerSample_decodes() throws {
        let json = """
        {
          "id": "m-001",
          "name": "안양중앙시장 행복정육점",
          "category": "food",
          "latitude": 37.3946,
          "longitude": 126.9235,
          "address": "경기 안양시 만안구 만안로 232 안양중앙시장 내",
          "roadAddress": "경기 안양시 만안구 만안로 232",
          "phone": "031-441-1101",
          "distanceMeters": null,
          "supportsOnnuri": true,
          "supportsLocalCurrency": true,
          "localCurrencyName": "안양사랑페이",
          "supportedPaymentTypes": ["onnuriDigital","onnuriPaper","onnuriCard","localCurrency","card"],
          "products": ["삼겹살","목살"],
          "businessHours": {"summary":"매일 09:00 - 20:00","closedNote":"둘째·넷째 일요일 휴무"},
          "rating": 4.7,
          "reviewCount": 128,
          "marketName": "안양중앙시장",
          "description": "3대째 이어온 정육점.",
          "lastVerifiedAt": "2026-08-10T06:03:17.625283Z",
          "reviews": [
            {
              "id": "85dda7ac-74e9-49e1-9dd1-1018234c8122",
              "userName": "안양민준",
              "rating": 5,
              "content": "삼겹살 구매했는데 잘 됩니다.",
              "createdAt": "2026-08-08T06:03:17.625290Z",
              "paymentType": "onnuriDigital",
              "paymentVerified": true,
              "purchasedProduct": "삼겹살"
            }
          ],
          "recentPayments": [
            {
              "id": "b9ebb98f-ddbc-41de-8c9e-bb3e924af931",
              "paymentType": "onnuriDigital",
              "succeededAt": "2026-08-11T06:03:17.625295Z",
              "note": "삼겹살 500g"
            }
          ]
        }
        """.data(using: .utf8)!

        let m = try JSONDecoder.localPay.decode(Merchant.self, from: json)
        XCTAssertEqual(m.id, "m-001")
        XCTAssertEqual(m.category, .food)
        XCTAssertNil(m.distanceMeters)
        XCTAssertTrue(m.supportsOnnuri)
        XCTAssertEqual(m.supportedPaymentTypes.first, .onnuriDigital)
        XCTAssertEqual(m.businessHours?.summary, "매일 09:00 - 20:00")
        XCTAssertNotNil(m.lastVerifiedAt)

        // reviews / recentPayments 내부 Date 도 정상 decode
        XCTAssertEqual(m.reviews.count, 1)
        XCTAssertEqual(m.reviews[0].userName, "안양민준")
        XCTAssertEqual(m.recentPayments.count, 1)
        XCTAssertEqual(m.recentPayments[0].note, "삼겹살 500g")
    }

    /// `/nearby` 는 `distanceMeters` 가 채워진 배열을 반환한다.
    func testMerchantArray_withDistanceMeters_decodes() throws {
        let json = """
        [
          {
            "id": "m-017",
            "name": "안양농협 하나로마트",
            "category": "mart",
            "latitude": 37.396,
            "longitude": 126.955,
            "address": "경기 안양시 만안구 삼덕로 45",
            "roadAddress": "경기 안양시 만안구 삼덕로 45",
            "phone": "031-441-6666",
            "distanceMeters": 110.98506945,
            "supportsOnnuri": false,
            "supportsLocalCurrency": false,
            "localCurrencyName": null,
            "supportedPaymentTypes": ["card","qr"],
            "products": ["과일"],
            "businessHours": {"summary":"매일 09:00 - 22:00","closedNote":null},
            "rating": 4.0,
            "reviewCount": 24,
            "marketName": null,
            "description": null,
            "lastVerifiedAt": "2026-07-30T06:03:17.625387Z",
            "reviews": [],
            "recentPayments": []
          }
        ]
        """.data(using: .utf8)!

        let list = try JSONDecoder.localPay.decode([Merchant].self, from: json)
        XCTAssertEqual(list.count, 1)
        XCTAssertEqual(list[0].distanceMeters, 110.98506945)
        XCTAssertNil(list[0].marketName)
        XCTAssertEqual(list[0].businessHours?.closedNote, nil)
    }

    // MARK: - NetworkError

    func testNetworkError_httpStatus404_userMessage() {
        let err = NetworkError.httpStatus(code: 404, body: nil)
        XCTAssertEqual(err.userMessage, "가맹점 정보를 찾지 못했습니다.")
    }

    func testNetworkError_transport_userMessage() {
        let err = NetworkError.transport(underlying: URLError(.notConnectedToInternet))
        XCTAssertEqual(err.userMessage, "네트워크 연결이 원활하지 않습니다.")
    }
}
