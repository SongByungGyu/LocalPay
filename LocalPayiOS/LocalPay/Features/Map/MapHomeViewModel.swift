import CoreLocation
import Foundation
import Observation

/// 지도 화면 상태. CLAUDE.md §5 흐름 (필터 → 표시할 Marker → 선택된 Merchant Preview).
@Observable
final class MapHomeViewModel {

    // MARK: - Public state

    var paymentFilter: PaymentFilter = .all
    var categoryFilter: MerchantCategory = .all

    /// 지도 표시용 Merchant. filter 적용된 결과.
    private(set) var visibleMerchants: [Merchant] = []

    /// 하단 Preview Card 로 보여줄 선택된 Merchant. 없으면 nil.
    var selectedMerchantId: String?

    private(set) var isLoading: Bool = false
    private(set) var loadError: String?

    // MARK: - Dependencies

    private let repository: MerchantRepository

    init(repository: MerchantRepository = RepositoryFactory.makeMerchantRepository()) {
        self.repository = repository
    }

    // MARK: - Actions

    func loadInitial() async {
        await reload()
    }

    /// 필터 변경 시 재로딩.
    func onFilterChanged() async {
        await reload()
    }

    /// 사용자가 Marker 를 탭.
    func selectMerchant(id: String) {
        selectedMerchantId = id
    }

    func clearSelection() {
        selectedMerchantId = nil
    }

    /// 거리 계산을 위해 현재 지도 중심을 알려준다.
    func updateDistances(from center: CLLocationCoordinate2D) {
        visibleMerchants = visibleMerchants.map { m in
            var copy = m
            copy.distanceMeters = GeoDistance.meters(from: center, to: m.coordinate)
            return copy
        }
    }

    // MARK: - Derived

    var selectedMerchant: Merchant? {
        guard let id = selectedMerchantId else { return nil }
        return visibleMerchants.first { $0.id == id }
    }

    var markers: [MapMarkerModel] {
        visibleMerchants.map { m in
            MapMarkerModel(
                id: m.id,
                latitude: m.latitude,
                longitude: m.longitude,
                badge: m.paymentBadge,
                category: m.category,
                isSelected: m.id == selectedMerchantId
            )
        }
    }

    // MARK: - Private

    private func reload() async {
        isLoading = true
        loadError = nil
        do {
            let result = try await repository.filter(category: categoryFilter, payment: paymentFilter)
            visibleMerchants = result
        } catch {
            loadError = "가맹점 정보를 불러오지 못했습니다."
            visibleMerchants = []
        }
        isLoading = false
    }
}
