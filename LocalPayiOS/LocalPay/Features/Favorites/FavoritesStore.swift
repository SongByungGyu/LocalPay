import Foundation
import Observation

/// 즐겨찾기 Merchant ID 집합. UserDefaults 로 영속화. CLAUDE.md §20.
@Observable
final class FavoritesStore {

    private let defaultsKey = "LocalPay.favorites.merchantIds"
    private let defaults: UserDefaults

    private(set) var ids: Set<String>

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let raw = defaults.array(forKey: defaultsKey) as? [String] {
            self.ids = Set(raw)
        } else {
            self.ids = []
        }
    }

    func isFavorite(_ id: String) -> Bool {
        ids.contains(id)
    }

    func toggle(_ id: String) {
        if ids.contains(id) {
            ids.remove(id)
        } else {
            ids.insert(id)
        }
        persist()
    }

    func add(_ id: String) {
        guard !ids.contains(id) else { return }
        ids.insert(id)
        persist()
    }

    func remove(_ id: String) {
        guard ids.contains(id) else { return }
        ids.remove(id)
        persist()
    }

    var count: Int { ids.count }

    // MARK: - Persistence

    private func persist() {
        defaults.set(Array(ids), forKey: defaultsKey)
    }

    // MARK: - Preview helpers

    static func previewInstance(prefilled: [String] = []) -> FavoritesStore {
        let ud = UserDefaults(suiteName: "preview.\(UUID().uuidString)")!
        let store = FavoritesStore(defaults: ud)
        prefilled.forEach { store.add($0) }
        return store
    }
}
