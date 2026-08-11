import Foundation

/// 안양시 기준 Dummy 가맹점 25 곳. 모두 가상의 매장이다. CLAUDE.md §13.
///
/// - 좌표: 안양시청 (37.3943, 126.9568) 근방 반경 ~3km
/// - 결제수단 조합: 온누리만 / 지역화폐만 / 둘 다 를 골고루 배분
/// - 카테고리: restaurant / cafe / pharmacy / mart / market / food / beauty / life / etc 골고루
enum DummyMerchantSeed {

    static let allMerchants: [Merchant] = build()

    // MARK: - Builder

    private static func build() -> [Merchant] {
        let today = Date()
        let cal = Calendar(identifier: .gregorian)
        func daysAgo(_ n: Int) -> Date { cal.date(byAdding: .day, value: -n, to: today) ?? today }

        return [
            // 1. 안양중앙시장 - 시장 카테고리
            Merchant(
                id: "m-001",
                name: "안양중앙시장 행복정육점",
                category: .food,
                latitude: 37.3946, longitude: 126.9235,
                address: "경기 안양시 만안구 만안로 232 안양중앙시장 내",
                roadAddress: "경기 안양시 만안구 만안로 232",
                phone: "031-441-1101",
                distanceMeters: nil,
                supportsOnnuri: true,
                supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .onnuriCard, .localCurrency, .card],
                products: ["삼겹살", "목살", "한우 등심", "선물세트", "양념갈비"],
                businessHours: BusinessHours(summary: "매일 09:00 - 20:00", closedNote: "둘째·넷째 일요일 휴무"),
                rating: 4.7, reviewCount: 128,
                marketName: "안양중앙시장",
                description: "3대째 이어온 정육점. 온누리·안양사랑페이 모두 사용 가능합니다.",
                lastVerifiedAt: daysAgo(1),
                reviews: [
                    Review(userName: "안양민준", rating: 5, content: "삼겹살 구매했는데 디지털 온누리 결제 잘 됩니다. 고기 신선해요.",
                           createdAt: daysAgo(3), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "삼겹살"),
                    Review(userName: "평촌맘", rating: 4, content: "지류 온누리도 받아주세요. 친절하십니다.",
                           createdAt: daysAgo(10), paymentType: .onnuriPaper, paymentVerified: true, purchasedProduct: "양념갈비"),
                    Review(userName: "안양토박이", rating: 5, content: "안양사랑페이 7% 할인 받으니 훨씬 이득이네요.",
                           createdAt: daysAgo(20), paymentType: .localCurrency, paymentVerified: true, purchasedProduct: "한우 등심")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(0), note: "삼겹살 500g"),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(3), note: "한우 등심"),
                    PaymentVerification(paymentType: .onnuriPaper, succeededAt: daysAgo(7), note: nil)
                ]
            ),

            // 2. 중앙시장 청년반찬
            Merchant(
                id: "m-002",
                name: "중앙시장 청년반찬",
                category: .food,
                latitude: 37.3951, longitude: 126.9240,
                address: "경기 안양시 만안구 만안로 234 안양중앙시장 청년몰",
                roadAddress: "경기 안양시 만안구 만안로 234",
                phone: "031-441-2020",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriCard, .card],
                products: ["멸치볶음", "장조림", "김치", "제육볶음", "명란젓"],
                businessHours: BusinessHours(summary: "화-일 10:00 - 20:00", closedNote: "월요일 휴무"),
                rating: 4.5, reviewCount: 62,
                marketName: "안양중앙시장",
                description: "청년몰의 인기 반찬가게. 소포장 반찬 종류가 많습니다.",
                lastVerifiedAt: daysAgo(5),
                reviews: [
                    Review(userName: "미영", rating: 5, content: "온누리 카드형으로 결제됨. 반찬 맛있어요!",
                           createdAt: daysAgo(2), paymentType: .onnuriCard, paymentVerified: true, purchasedProduct: "장조림")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriCard, succeededAt: daysAgo(1), note: "반찬 3종")
                ]
            ),

            // 3. 범계할머니손칼국수 (음식점)
            Merchant(
                id: "m-003",
                name: "범계할머니손칼국수",
                category: .restaurant,
                latitude: 37.3902, longitude: 126.9769,
                address: "경기 안양시 동안구 시민대로 175",
                roadAddress: "경기 안양시 동안구 시민대로 175",
                phone: "031-386-4455",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card],
                products: ["손칼국수", "만두국", "수육", "김치전"],
                businessHours: BusinessHours(summary: "매일 11:00 - 21:00", closedNote: nil),
                rating: 4.6, reviewCount: 214,
                marketName: nil,
                description: "20년 전통 손칼국수집. 안양사랑페이 결제 가능.",
                lastVerifiedAt: daysAgo(2),
                reviews: [
                    Review(userName: "혜정", rating: 5, content: "안양사랑페이 결제되고 국물 진해요.",
                           createdAt: daysAgo(4), paymentType: .localCurrency, paymentVerified: true, purchasedProduct: "손칼국수")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(1), note: nil)
                ]
            ),

            // 4. 평촌우리약국
            Merchant(
                id: "m-004",
                name: "평촌우리약국",
                category: .pharmacy,
                latitude: 37.3918, longitude: 126.9690,
                address: "경기 안양시 동안구 평촌대로 132",
                roadAddress: "경기 안양시 동안구 평촌대로 132",
                phone: "031-381-7788",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .localCurrency, .card],
                products: ["타이레놀", "지사제", "종합감기약", "밴드", "비타민"],
                businessHours: BusinessHours(summary: "월-금 09:00 - 21:00 / 토 09:00 - 18:00", closedNote: "일요일·공휴일 휴무"),
                rating: 4.4, reviewCount: 47,
                marketName: nil,
                description: "친절 상담이 좋은 동네 약국.",
                lastVerifiedAt: daysAgo(3),
                reviews: [
                    Review(userName: "재훈", rating: 4, content: "종합감기약 사면서 온누리 디지털 결제 잘 됐어요.",
                           createdAt: daysAgo(6), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "종합감기약")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(2), note: nil),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(8), note: nil)
                ]
            ),

            // 5. 안양착한카페
            Merchant(
                id: "m-005",
                name: "안양착한카페",
                category: .cafe,
                latitude: 37.3970, longitude: 126.9270,
                address: "경기 안양시 만안구 만안로 210",
                roadAddress: "경기 안양시 만안구 만안로 210",
                phone: "031-441-3300",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .localCurrency, .card],
                products: ["아메리카노", "카페라떼", "크로플", "수제청 에이드"],
                businessHours: BusinessHours(summary: "매일 08:00 - 22:00", closedNote: nil),
                rating: 4.8, reviewCount: 340,
                marketName: nil,
                description: "안양의 대표 착한가격 카페. 온누리·지역화폐 모두 사용 가능.",
                lastVerifiedAt: daysAgo(1),
                reviews: [
                    Review(userName: "지수", rating: 5, content: "아메리카노 2500원인데 온누리도 됨. 무조건 옴.",
                           createdAt: daysAgo(2), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "아메리카노"),
                    Review(userName: "은비", rating: 5, content: "안양사랑페이로 결제 잘 되고 사장님 친절해요.",
                           createdAt: daysAgo(9), paymentType: .localCurrency, paymentVerified: true, purchasedProduct: "카페라떼")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(0), note: "아메리카노 2잔"),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(5), note: nil)
                ]
            ),

            // 6. 평촌생활마트
            Merchant(
                id: "m-006",
                name: "평촌생활마트",
                category: .mart,
                latitude: 37.3892, longitude: 126.9660,
                address: "경기 안양시 동안구 평촌대로 88",
                roadAddress: "경기 안양시 동안구 평촌대로 88",
                phone: "031-386-1010",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriCard, .localCurrency, .card, .qr],
                products: ["즉석밥", "라면", "우유", "계란", "세제"],
                businessHours: BusinessHours(summary: "매일 08:00 - 23:00", closedNote: nil),
                rating: 4.3, reviewCount: 89,
                marketName: nil,
                description: "동네 생활 필수품 마트.",
                lastVerifiedAt: daysAgo(4),
                reviews: [
                    Review(userName: "서연", rating: 4, content: "온누리·지역화폐 다 되니 편해요.",
                           createdAt: daysAgo(7), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "즉석밥")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(2), note: nil)
                ]
            ),

            // 7. 인덕원분식
            Merchant(
                id: "m-007",
                name: "인덕원분식",
                category: .restaurant,
                latitude: 37.4014, longitude: 126.9782,
                address: "경기 안양시 동안구 관평로 289",
                roadAddress: "경기 안양시 동안구 관평로 289",
                phone: "031-421-1122",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .card],
                products: ["떡볶이", "김밥", "라볶이", "튀김"],
                businessHours: BusinessHours(summary: "화-일 11:00 - 21:00", closedNote: "월요일 휴무"),
                rating: 4.5, reviewCount: 156,
                marketName: nil,
                description: "인덕원 20년 분식집.",
                lastVerifiedAt: daysAgo(6),
                reviews: [
                    Review(userName: "다현", rating: 5, content: "지류 온누리 받아주는 몇 안 되는 분식집!",
                           createdAt: daysAgo(4), paymentType: .onnuriPaper, paymentVerified: true, purchasedProduct: "떡볶이")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriPaper, succeededAt: daysAgo(1), note: nil)
                ]
            ),

            // 8. 안양미용실
            Merchant(
                id: "m-008",
                name: "안양미용실",
                category: .beauty,
                latitude: 37.3990, longitude: 126.9280,
                address: "경기 안양시 만안구 안양로 480",
                roadAddress: "경기 안양시 만안구 안양로 480",
                phone: "031-441-8899",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card],
                products: ["커트", "펌", "염색", "매직"],
                businessHours: BusinessHours(summary: "화-일 10:00 - 20:00", closedNote: "월요일 휴무"),
                rating: 4.6, reviewCount: 72,
                marketName: nil,
                description: "안양 여성 헤어 전문점. 안양사랑페이 결제 시 5% 추가할인.",
                lastVerifiedAt: daysAgo(3),
                reviews: [
                    Review(userName: "수민", rating: 5, content: "안양사랑페이로 결제 잘 됨. 매직 자연스러워요.",
                           createdAt: daysAgo(11), paymentType: .localCurrency, paymentVerified: true, purchasedProduct: "매직")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(3), note: nil)
                ]
            ),

            // 9. 범계문구백화점
            Merchant(
                id: "m-009",
                name: "범계문구백화점",
                category: .life,
                latitude: 37.3906, longitude: 126.9755,
                address: "경기 안양시 동안구 시민대로 190",
                roadAddress: "경기 안양시 동안구 시민대로 190",
                phone: "031-386-5566",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .localCurrency, .card],
                products: ["노트", "볼펜", "포장지", "학용품 세트"],
                businessHours: BusinessHours(summary: "매일 09:00 - 21:00", closedNote: nil),
                rating: 4.2, reviewCount: 33,
                marketName: nil,
                description: "학용품, 사무용품 종합 매장.",
                lastVerifiedAt: daysAgo(9),
                reviews: [
                    Review(userName: "학부모", rating: 4, content: "온누리로 학용품 살 수 있어서 편해요.",
                           createdAt: daysAgo(15), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "학용품 세트")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(4), note: nil)
                ]
            ),

            // 10. 평촌한우촌
            Merchant(
                id: "m-010",
                name: "평촌한우촌",
                category: .restaurant,
                latitude: 37.3925, longitude: 126.9700,
                address: "경기 안양시 동안구 평촌대로 155",
                roadAddress: "경기 안양시 동안구 평촌대로 155",
                phone: "031-381-2266",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriCard, .localCurrency, .card],
                products: ["한우 등심", "한우 채끝", "육회", "냉면"],
                businessHours: BusinessHours(summary: "매일 11:30 - 22:00", closedNote: nil),
                rating: 4.7, reviewCount: 187,
                marketName: nil,
                description: "한우 전문점. 상품권 최대한 활용 가능.",
                lastVerifiedAt: daysAgo(2),
                reviews: [
                    Review(userName: "가족손님", rating: 5, content: "한우 회식 온누리 카드형으로 결제 완료. 서비스 훌륭.",
                           createdAt: daysAgo(3), paymentType: .onnuriCard, paymentVerified: true, purchasedProduct: "한우 등심")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriCard, succeededAt: daysAgo(0), note: "한우 등심 400g"),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(6), note: nil)
                ]
            ),

            // 11. 안양중앙시장 청춘꽃집
            Merchant(
                id: "m-011",
                name: "청춘꽃집",
                category: .etc,
                latitude: 37.3948, longitude: 126.9245,
                address: "경기 안양시 만안구 만안로 235 안양중앙시장",
                roadAddress: "경기 안양시 만안구 만안로 235",
                phone: "031-441-9911",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .card],
                products: ["꽃다발", "화분", "졸업식 꽃", "생일 꽃"],
                businessHours: BusinessHours(summary: "매일 10:00 - 20:00", closedNote: nil),
                rating: 4.9, reviewCount: 96,
                marketName: "안양중앙시장",
                description: "청년 사장님이 운영하는 감성 꽃집.",
                lastVerifiedAt: daysAgo(2),
                reviews: [
                    Review(userName: "지환", rating: 5, content: "온누리로 꽃다발 결제 잘 됩니다.",
                           createdAt: daysAgo(1), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "꽃다발")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(1), note: nil)
                ]
            ),

            // 12. 평촌우리제과
            Merchant(
                id: "m-012",
                name: "평촌우리제과",
                category: .cafe,
                latitude: 37.3900, longitude: 126.9680,
                address: "경기 안양시 동안구 평촌대로 100",
                roadAddress: "경기 안양시 동안구 평촌대로 100",
                phone: "031-381-5544",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card],
                products: ["식빵", "크루아상", "생크림 케이크", "단팥빵"],
                businessHours: BusinessHours(summary: "매일 07:00 - 22:00", closedNote: nil),
                rating: 4.5, reviewCount: 121,
                marketName: nil,
                description: "동네 인기 베이커리.",
                lastVerifiedAt: daysAgo(4),
                reviews: [
                    Review(userName: "재원", rating: 5, content: "안양사랑페이로 케이크 결제 완료. 부드러워요.",
                           createdAt: daysAgo(5), paymentType: .localCurrency, paymentVerified: true, purchasedProduct: "생크림 케이크")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(2), note: nil)
                ]
            ),

            // 13. 관양동 새마을수퍼
            Merchant(
                id: "m-013",
                name: "관양동 새마을수퍼",
                category: .mart,
                latitude: 37.3982, longitude: 126.9724,
                address: "경기 안양시 동안구 관양로 88",
                roadAddress: "경기 안양시 동안구 관양로 88",
                phone: "031-421-3311",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .card],
                products: ["과자", "음료", "생수", "라면", "간편식"],
                businessHours: BusinessHours(summary: "매일 06:30 - 24:00", closedNote: nil),
                rating: 4.1, reviewCount: 41,
                marketName: nil,
                description: "24시간 가까이 여는 동네 수퍼.",
                lastVerifiedAt: daysAgo(7),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriPaper, succeededAt: daysAgo(5), note: nil)
                ]
            ),

            // 14. 안양중앙시장 옛날통닭
            Merchant(
                id: "m-014",
                name: "안양중앙시장 옛날통닭",
                category: .restaurant,
                latitude: 37.3944, longitude: 126.9238,
                address: "경기 안양시 만안구 만안로 232 안양중앙시장",
                roadAddress: "경기 안양시 만안구 만안로 232",
                phone: "031-441-4444",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .localCurrency, .card],
                products: ["옛날통닭", "간장치킨", "닭강정"],
                businessHours: BusinessHours(summary: "화-일 12:00 - 22:00", closedNote: "월요일 휴무"),
                rating: 4.6, reviewCount: 205,
                marketName: "안양중앙시장",
                description: "가마솥에 튀기는 옛날통닭.",
                lastVerifiedAt: daysAgo(1),
                reviews: [
                    Review(userName: "동네주민", rating: 5, content: "온누리로 통닭 사먹는 재미. 바삭!",
                           createdAt: daysAgo(2), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "옛날통닭")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(0), note: nil),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(4), note: nil)
                ]
            ),

            // 15. 안양시청역 안경원
            Merchant(
                id: "m-015",
                name: "시청역안경원",
                category: .life,
                latitude: 37.3940, longitude: 126.9565,
                address: "경기 안양시 동안구 시민대로 235",
                roadAddress: "경기 안양시 동안구 시민대로 235",
                phone: "031-386-7070",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card],
                products: ["안경테", "선글라스", "렌즈"],
                businessHours: BusinessHours(summary: "월-토 10:00 - 20:00", closedNote: "일요일 휴무"),
                rating: 4.4, reviewCount: 58,
                marketName: nil,
                description: "정확한 시력측정과 안양사랑페이 결제 지원.",
                lastVerifiedAt: daysAgo(5),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(7), note: nil)
                ]
            ),

            // 16. 평촌스터디카페
            Merchant(
                id: "m-016",
                name: "평촌스터디카페",
                category: .cafe,
                latitude: 37.3910, longitude: 126.9720,
                address: "경기 안양시 동안구 시민대로 200",
                roadAddress: "경기 안양시 동안구 시민대로 200",
                phone: "031-381-9090",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .localCurrency, .card, .qr],
                products: ["시간권", "정기권", "음료"],
                businessHours: BusinessHours(summary: "24시간", closedNote: nil),
                rating: 4.3, reviewCount: 78,
                marketName: nil,
                description: "24시간 무인 스터디카페.",
                lastVerifiedAt: daysAgo(3),
                reviews: [
                    Review(userName: "수험생", rating: 4, content: "정기권 결제 온누리 됨. 조용해요.",
                           createdAt: daysAgo(8), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "정기권")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(3), note: nil)
                ]
            ),

            // 17. 안양농협 하나로마트 (샘플: 온누리 X, 지역화폐 X — 비사용 케이스로도 하나)
            Merchant(
                id: "m-017",
                name: "안양농협 하나로마트",
                category: .mart,
                latitude: 37.3960, longitude: 126.9550,
                address: "경기 안양시 만안구 삼덕로 45",
                roadAddress: "경기 안양시 만안구 삼덕로 45",
                phone: "031-441-6666",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.card, .qr],
                products: ["과일", "채소", "쌀", "정육"],
                businessHours: BusinessHours(summary: "매일 09:00 - 22:00", closedNote: nil),
                rating: 4.0, reviewCount: 24,
                marketName: nil,
                description: "일반 카드 및 페이 사용 가능. 상품권은 미사용.",
                lastVerifiedAt: daysAgo(12),
                reviews: [],
                recentPayments: []
            ),

            // 18. 안양대박곱창
            Merchant(
                id: "m-018",
                name: "안양대박곱창",
                category: .restaurant,
                latitude: 37.3935, longitude: 126.9585,
                address: "경기 안양시 만안구 안양로 250",
                roadAddress: "경기 안양시 만안구 안양로 250",
                phone: "031-441-8282",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriCard, .localCurrency, .card],
                products: ["소곱창", "대창", "막창", "볶음밥"],
                businessHours: BusinessHours(summary: "매일 16:00 - 24:00", closedNote: nil),
                rating: 4.6, reviewCount: 168,
                marketName: nil,
                description: "숯불곱창 전문점. 상품권 활용도 최고.",
                lastVerifiedAt: daysAgo(2),
                reviews: [
                    Review(userName: "회식러", rating: 5, content: "회식 4명 온누리·안양페이 조합 결제 성공.",
                           createdAt: daysAgo(3), paymentType: .onnuriCard, paymentVerified: true, purchasedProduct: "소곱창")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriCard, succeededAt: daysAgo(1), note: nil),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(5), note: nil)
                ]
            ),

            // 19. 관양시장 옹기떡집
            Merchant(
                id: "m-019",
                name: "옹기떡집",
                category: .food,
                latitude: 37.3988, longitude: 126.9738,
                address: "경기 안양시 동안구 관평로 210",
                roadAddress: "경기 안양시 동안구 관평로 210",
                phone: "031-421-5544",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .card],
                products: ["백설기", "인절미", "떡국떡", "꿀떡"],
                businessHours: BusinessHours(summary: "월-토 07:00 - 20:00", closedNote: "일요일 휴무"),
                rating: 4.7, reviewCount: 88,
                marketName: "관양시장",
                description: "3대째 이어온 방앗간.",
                lastVerifiedAt: daysAgo(4),
                reviews: [
                    Review(userName: "떡순이", rating: 5, content: "지류 온누리도 잘 받아주십니다.",
                           createdAt: daysAgo(6), paymentType: .onnuriPaper, paymentVerified: true, purchasedProduct: "인절미")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(2), note: nil)
                ]
            ),

            // 20. 인덕원카페 라온
            Merchant(
                id: "m-020",
                name: "인덕원카페 라온",
                category: .cafe,
                latitude: 37.4010, longitude: 126.9770,
                address: "경기 안양시 동안구 관평로 292",
                roadAddress: "경기 안양시 동안구 관평로 292",
                phone: "031-421-7777",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card, .qr],
                products: ["드립커피", "치즈케이크", "레몬에이드"],
                businessHours: BusinessHours(summary: "화-일 10:00 - 22:00", closedNote: "월요일 휴무"),
                rating: 4.7, reviewCount: 143,
                marketName: nil,
                description: "인덕원 감성 카페.",
                lastVerifiedAt: daysAgo(3),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(4), note: nil)
                ]
            ),

            // 21. 안양중앙시장 반찬왕
            Merchant(
                id: "m-021",
                name: "안양중앙시장 반찬왕",
                category: .food,
                latitude: 37.3953, longitude: 126.9242,
                address: "경기 안양시 만안구 만안로 234",
                roadAddress: "경기 안양시 만안구 만안로 234",
                phone: "031-441-7373",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .localCurrency, .card],
                products: ["오이무침", "김치", "젓갈", "장아찌"],
                businessHours: BusinessHours(summary: "매일 09:00 - 20:00", closedNote: nil),
                rating: 4.5, reviewCount: 66,
                marketName: "안양중앙시장",
                description: "반찬 종류만 30가지.",
                lastVerifiedAt: daysAgo(2),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(1), note: nil)
                ]
            ),

            // 22. 만안치과의원 근처 편의점 (etc)
            Merchant(
                id: "m-022",
                name: "동네정직세탁소",
                category: .life,
                latitude: 37.3975, longitude: 126.9600,
                address: "경기 안양시 만안구 만안로 130",
                roadAddress: "경기 안양시 만안구 만안로 130",
                phone: "031-441-2323",
                distanceMeters: nil,
                supportsOnnuri: false, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.localCurrency, .card],
                products: ["정장 드라이", "코트 드라이", "이불 세탁"],
                businessHours: BusinessHours(summary: "월-토 08:00 - 20:00", closedNote: "일요일 휴무"),
                rating: 4.3, reviewCount: 21,
                marketName: nil,
                description: "동네 세탁소. 안양사랑페이 결제 가능.",
                lastVerifiedAt: daysAgo(8),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(6), note: nil)
                ]
            ),

            // 23. 평촌족발
            Merchant(
                id: "m-023",
                name: "평촌족발",
                category: .restaurant,
                latitude: 37.3908, longitude: 126.9705,
                address: "경기 안양시 동안구 평촌대로 160",
                roadAddress: "경기 안양시 동안구 평촌대로 160",
                phone: "031-381-6262",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .localCurrency, .card],
                products: ["족발", "보쌈", "쟁반국수"],
                businessHours: BusinessHours(summary: "매일 15:00 - 24:00", closedNote: nil),
                rating: 4.5, reviewCount: 132,
                marketName: nil,
                description: "야식 명소.",
                lastVerifiedAt: daysAgo(2),
                reviews: [
                    Review(userName: "야식러", rating: 5, content: "온누리로 족발 결제. 배달 X, 방문 O.",
                           createdAt: daysAgo(4), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "족발")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(1), note: nil)
                ]
            ),

            // 24. 안양중앙시장 과일가게
            Merchant(
                id: "m-024",
                name: "중앙시장 계절과일",
                category: .food,
                latitude: 37.3950, longitude: 126.9237,
                address: "경기 안양시 만안구 만안로 233",
                roadAddress: "경기 안양시 만안구 만안로 233",
                phone: "031-441-1919",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: true,
                localCurrencyName: "안양사랑페이",
                supportedPaymentTypes: [.onnuriDigital, .onnuriPaper, .localCurrency, .card],
                products: ["사과", "귤", "포도", "복숭아", "선물세트"],
                businessHours: BusinessHours(summary: "매일 08:00 - 21:00", closedNote: nil),
                rating: 4.6, reviewCount: 74,
                marketName: "안양중앙시장",
                description: "제철 과일 전문.",
                lastVerifiedAt: daysAgo(1),
                reviews: [
                    Review(userName: "과일러버", rating: 5, content: "온누리로 사과 한 박스 결제. 달아요.",
                           createdAt: daysAgo(2), paymentType: .onnuriDigital, paymentVerified: true, purchasedProduct: "사과")
                ],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(0), note: "사과 1박스"),
                    PaymentVerification(paymentType: .localCurrency, succeededAt: daysAgo(5), note: nil)
                ]
            ),

            // 25. 안양 헤어살롱 준
            Merchant(
                id: "m-025",
                name: "헤어살롱 준",
                category: .beauty,
                latitude: 37.3928, longitude: 126.9575,
                address: "경기 안양시 만안구 안양로 300",
                roadAddress: "경기 안양시 만안구 안양로 300",
                phone: "031-441-5959",
                distanceMeters: nil,
                supportsOnnuri: true, supportsLocalCurrency: false,
                localCurrencyName: nil,
                supportedPaymentTypes: [.onnuriDigital, .onnuriCard, .card],
                products: ["남성 커트", "여성 커트", "베이직 펌"],
                businessHours: BusinessHours(summary: "화-일 10:30 - 20:00", closedNote: "월요일 휴무"),
                rating: 4.4, reviewCount: 45,
                marketName: nil,
                description: "가족 단위 손님 많은 미용실.",
                lastVerifiedAt: daysAgo(6),
                reviews: [],
                recentPayments: [
                    PaymentVerification(paymentType: .onnuriDigital, succeededAt: daysAgo(4), note: nil)
                ]
            )
        ]
    }
}
