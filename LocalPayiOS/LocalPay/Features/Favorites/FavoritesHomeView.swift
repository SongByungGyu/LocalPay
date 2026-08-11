import SwiftUI

/// 즐겨찾기 목록 화면. CLAUDE.md §20.
struct FavoritesHomeView: View {

    @Environment(FavoritesStore.self) private var favorites
    @State private var merchants: [Merchant] = []
    @State private var isLoading = false
    @State private var navigateToDetailId: String?

    private let repository: MerchantRepository = DummyMerchantRepository()

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && merchants.isEmpty {
                    LoadingView()
                } else if favorites.ids.isEmpty {
                    EmptyStateView(
                        iconName: "heart",
                        title: "아직 즐겨찾기가 없어요",
                        subtitle: "지도에서 마음에 드는 가게를 하트로 저장해 보세요."
                    )
                } else {
                    ScrollView {
                        LazyVStack(spacing: AppSpacing.sm) {
                            ForEach(merchants) { m in
                                MerchantCard(merchant: m, onTap: { navigateToDetailId = m.id })
                            }
                        }
                        .padding(.horizontal, AppSpacing.lg)
                        .padding(.vertical, AppSpacing.md)
                    }
                }
            }
            .background(AppColor.background)
            .navigationTitle("즐겨찾기")
            .navigationDestination(item: $navigateToDetailId) { id in
                MerchantDetailView(merchantId: id)
            }
            .task { await reload() }
            .onChange(of: favorites.ids) { _, _ in
                Task { await reload() }
            }
        }
    }

    private func reload() async {
        isLoading = true
        do {
            let all = try await repository.fetchAll()
            merchants = all.filter { favorites.ids.contains($0.id) }
        } catch {
            merchants = []
        }
        isLoading = false
    }
}

#Preview {
    FavoritesHomeView()
        .environment(FavoritesStore.previewInstance(prefilled: ["m-001", "m-005"]))
        .environment(ReviewsStore.previewInstance())
}
