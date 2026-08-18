import SwiftUI

/// 시장 대표 마커 탭 시 하단 sheet.
/// 상단에 시장 이름 · 매장 count · payment · 좌표 근사 안내,
/// 그 아래 매장 리스트 (paginated fetch).
struct MarketDetailSheet: View {
    let market: MarketAggregate
    let onSelectMerchant: (Merchant) -> Void

    @State private var viewModel: MarketMerchantsViewModel

    init(market: MarketAggregate, onSelectMerchant: @escaping (Merchant) -> Void) {
        self.market = market
        self.onSelectMerchant = onSelectMerchant
        _viewModel = State(initialValue: MarketMerchantsViewModel(marketId: market.id))
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider().background(AppColor.divider)
            content
        }
        .background(AppColor.background)
        .task { await viewModel.loadInitial() }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: AppSpacing.xs) {
            HStack(spacing: 6) {
                Image(systemName: "storefront.fill")
                    .foregroundStyle(AppColor.primary)
                Text(market.name)
                    .font(AppTypography.navigationTitle)
                    .foregroundStyle(AppColor.textPrimary)
            }
            HStack(spacing: 8) {
                Text("온누리 사용처 \(market.merchantCount)곳")
                    .font(AppTypography.body.weight(.semibold))
                    .foregroundStyle(AppColor.primary)
                Text("· 지류 \(market.paperCount) · 디지털 \(market.digitalCount)")
                    .font(AppTypography.chip)
                    .foregroundStyle(AppColor.textSecondary)
            }
            Text("이 위치는 \(market.name) 대표 좌표 기준입니다. 개별 매장의 정확한 위치와 다를 수 있습니다.")
                .font(.system(size: 12))
                .foregroundStyle(AppColor.textSecondary)
                .padding(.top, 2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppSpacing.lg)
    }

    @ViewBuilder
    private var content: some View {
        if viewModel.isLoading && viewModel.merchants.isEmpty {
            ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if viewModel.merchants.isEmpty {
            EmptyStateView(
                iconName: "storefront",
                title: "매장 정보가 없어요",
                subtitle: "조건에 맞는 매장이 없습니다."
            )
        } else {
            ScrollView {
                LazyVStack(spacing: AppSpacing.sm) {
                    ForEach(viewModel.merchants) { m in
                        MerchantCard(merchant: m, onTap: { onSelectMerchant(m) })
                    }
                }
                .padding(.horizontal, AppSpacing.lg)
                .padding(.bottom, AppSpacing.xxl)
            }
        }
    }
}

@Observable
final class MarketMerchantsViewModel {
    let marketId: String
    private(set) var merchants: [Merchant] = []
    private(set) var isLoading: Bool = false
    private(set) var loadError: String?

    private let repository: MerchantRepository

    init(marketId: String, repository: MerchantRepository = RepositoryFactory.makeMerchantRepository()) {
        self.marketId = marketId
        self.repository = repository
    }

    func loadInitial() async {
        isLoading = true
        loadError = nil
        do {
            let result = try await repository.merchantsInMarket(
                marketId: marketId,
                category: .all,
                payment: .all,
                query: nil,
                limit: 100,
                offset: 0
            )
            merchants = result
        } catch {
            #if DEBUG
            print("[MarketMerchantsViewModel] load FAILED: \(error)")
            #endif
            loadError = "매장 정보를 불러오지 못했습니다."
            merchants = []
        }
        isLoading = false
    }
}
