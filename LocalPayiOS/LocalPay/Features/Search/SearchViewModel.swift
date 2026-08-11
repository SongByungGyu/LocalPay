import CoreLocation
import Foundation
import Observation

/// 검색 화면 상태. CLAUDE.md §18.
@Observable
final class SearchViewModel {

    var query: String = ""
    var sort: SortOption = .distance
    private(set) var results: [Merchant] = []
    private(set) var isSearching: Bool = false
    private(set) var hasSearchedAtLeastOnce: Bool = false

    private let repository: MerchantRepository
    private var currentTask: Task<Void, Never>?

    init(repository: MerchantRepository = DummyMerchantRepository()) {
        self.repository = repository
    }

    /// 300ms debounce 후 검색 수행.
    func debouncedSearch() {
        currentTask?.cancel()
        currentTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 300_000_000)
            guard !Task.isCancelled else { return }
            await self?.performSearch()
        }
    }

    func performSearch() async {
        isSearching = true
        hasSearchedAtLeastOnce = true
        do {
            let raw = try await repository.search(query: query)
            let center = MapRegion.anyangDefault.center
            let withDistance = raw.map { m -> Merchant in
                var copy = m
                copy.distanceMeters = GeoDistance.meters(from: center, to: m.coordinate)
                return copy
            }
            results = sort.apply(withDistance)
        } catch {
            results = []
        }
        isSearching = false
    }

    func onSortChanged() {
        results = sort.apply(results)
    }
}
