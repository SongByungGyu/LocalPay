import CoreLocation
import Foundation
import Observation

/// 지도 화면 상태. Phase 13-A 부터 카메라 BBOX 기반 자동 재조회.
/// CLAUDE.md §5 흐름 (필터 → 표시할 Marker → 선택된 Merchant Preview).
///
/// 로딩 방식:
/// - 초기 로딩·필터 변경: 현재 지도 BBOX 로 `/api/v1/merchants/map` 호출
/// - 카메라 이동 종료: 400ms debounce 후 새 BBOX 로 호출
/// - 이전 요청은 `Task.cancel()` + generation counter 로 폐기
///   (오래된 응답이 최신 지도를 덮어쓰지 못하게)
/// - 이전 BBOX 와 사실상 동일하면 요청 스킵
@Observable
final class MapHomeViewModel {

    // MARK: - Public state

    var paymentFilter: PaymentFilter = .all
    var categoryFilter: MerchantCategory = .all

    /// 지도 표시용 Merchant. filter + BBOX 적용된 결과.
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

    // MARK: - Internal (BBOX 상태)

    /// 마지막으로 성공한 요청의 BBOX. 유사 BBOX 중복 요청 판별용.
    private var lastRequestedBBox: MapBBox?

    /// 현재 진행 중인 fetch Task. 새 요청 시 cancel.
    private var currentFetchTask: Task<Void, Never>?

    /// 진행 중인 debounce Task.
    private var pendingDebounceTask: Task<Void, Never>?

    /// 세대 카운터. 응답이 도착했을 때 자신이 최신 세대인지 검사.
    private var generation: UInt64 = 0

    /// debounce 지연 (ms). 300~500ms 범위 (스펙 §5, §6).
    private let debounceMillis: UInt64 = 400

    // MARK: - Actions

    /// 앱 진입 · Map 최초 표시 직후 호출. 초기 지도 영역을 넘겨준다.
    func loadInitial(bbox: MapBBox) async {
        await performFetch(bbox: bbox)
    }

    /// 필터 변경 시 재로딩. 마지막 BBOX 를 그대로 재사용해 즉시 요청.
    func onFilterChanged() async {
        guard let bbox = lastRequestedBBox else { return }
        await performFetch(bbox: bbox)
    }

    /// 카메라 이동 종료 시 View 가 호출. 400ms debounce 후 fetch.
    /// 짧은 시간에 여러 번 오면 이전 debounce 는 cancel 되고 마지막만 실행.
    func onCameraChanged(bbox: MapBBox) {
        guard bbox.isValid else {
            #if DEBUG
            print("[MapHomeViewModel] onCameraChanged: bbox invalid, skip")
            #endif
            return
        }
        if let last = lastRequestedBBox, last.isApproximatelyEqual(to: bbox) {
            #if DEBUG
            print("[MapHomeViewModel] onCameraChanged: near-duplicate, skip")
            #endif
            return
        }

        pendingDebounceTask?.cancel()
        pendingDebounceTask = Task { [weak self] in
            do {
                try await Task.sleep(nanoseconds: (self?.debounceMillis ?? 400) * 1_000_000)
            } catch {
                return   // cancelled
            }
            guard !Task.isCancelled else { return }
            await self?.performFetch(bbox: bbox)
        }
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

    private func performFetch(bbox: MapBBox) async {
        currentFetchTask?.cancel()

        generation &+= 1
        let mySeq = generation
        let category = categoryFilter
        let payment = paymentFilter

        isLoading = true
        loadError = nil

        let task = Task { [weak self] in
            guard let self else { return }
            do {
                let result = try await self.repository.mapMerchants(
                    bbox: bbox,
                    category: category,
                    payment: payment
                )
                // 최신 세대만 반영. 그 사이 다른 요청이 세대를 올렸으면 응답 폐기.
                guard mySeq == self.generation, !Task.isCancelled else {
                    #if DEBUG
                    print("[MapHomeViewModel] stale response dropped (seq=\(mySeq) vs \(self.generation))")
                    #endif
                    return
                }
                #if DEBUG
                print("[MapHomeViewModel] BBOX ok count=\(result.count) cat=\(category) pay=\(payment)")
                #endif
                self.visibleMerchants = result
                self.lastRequestedBBox = bbox
                self.isLoading = false
            } catch is CancellationError {
                return
            } catch {
                guard mySeq == self.generation else { return }
                #if DEBUG
                print("[MapHomeViewModel] BBOX FAILED: \(error)")
                #endif
                self.loadError = "가맹점 정보를 불러오지 못했습니다."
                self.visibleMerchants = []
                self.isLoading = false
            }
        }
        currentFetchTask = task
        await task.value
    }
}
