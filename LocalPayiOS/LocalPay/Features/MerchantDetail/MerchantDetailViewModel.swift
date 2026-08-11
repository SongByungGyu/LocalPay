import Foundation
import Observation

/// 상세화면 상태.
@Observable
final class MerchantDetailViewModel {

    private(set) var merchant: Merchant?
    private(set) var isLoading: Bool = false
    private(set) var loadError: String?

    private let repository: MerchantRepository
    private let merchantId: String

    init(merchantId: String, repository: MerchantRepository = RepositoryFactory.makeMerchantRepository()) {
        self.merchantId = merchantId
        self.repository = repository
    }

    func load() async {
        isLoading = true
        loadError = nil
        do {
            merchant = try await repository.fetch(id: merchantId)
        } catch {
            loadError = "가맹점 정보를 불러오지 못했습니다."
        }
        isLoading = false
    }
}
