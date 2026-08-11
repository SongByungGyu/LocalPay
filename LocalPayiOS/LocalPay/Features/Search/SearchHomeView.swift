import SwiftUI

/// 검색 화면. CLAUDE.md §18, §19.
struct SearchHomeView: View {

    @State private var viewModel = SearchViewModel()
    @State private var navigateToDetailId: String?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                searchBarSection
                if viewModel.hasSearchedAtLeastOnce {
                    sortBar
                }
                resultsSection
            }
            .background(AppColor.background)
            .navigationTitle("검색")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(item: $navigateToDetailId) { id in
                MerchantDetailView(merchantId: id)
            }
        }
    }

    private var searchBarSection: some View {
        VStack(spacing: AppSpacing.sm) {
            AppSearchBar(
                placeholder: "가게 · 상품 · 시장으로 검색",
                text: $viewModel.query,
                onSubmit: { Task { await viewModel.performSearch() } }
            )
            .onChange(of: viewModel.query) { _, _ in
                viewModel.debouncedSearch()
            }
            SuggestionRow(onTap: { keyword in
                viewModel.query = keyword
                Task { await viewModel.performSearch() }
            })
        }
        .padding(.horizontal, AppSpacing.lg)
        .padding(.bottom, AppSpacing.sm)
    }

    private var sortBar: some View {
        HStack(spacing: AppSpacing.sm) {
            ForEach(SortOption.allCases) { opt in
                Button {
                    viewModel.sort = opt
                    viewModel.onSortChanged()
                } label: {
                    Text(opt.title)
                        .font(AppTypography.chip)
                        .foregroundStyle(viewModel.sort == opt ? AppColor.primary : AppColor.textSecondary)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(
                            Capsule().fill(viewModel.sort == opt ? AppColor.primary.opacity(0.12) : Color.clear)
                        )
                }
                .buttonStyle(.plain)
            }
            Spacer()
            Text("\(viewModel.results.count)개")
                .font(AppTypography.chip)
                .foregroundStyle(AppColor.textSecondary)
        }
        .padding(.horizontal, AppSpacing.lg)
        .padding(.bottom, AppSpacing.sm)
    }

    @ViewBuilder
    private var resultsSection: some View {
        if viewModel.isSearching {
            LoadingView(message: "검색 중...")
        } else if !viewModel.hasSearchedAtLeastOnce {
            EmptyStateView(
                iconName: "magnifyingglass",
                title: "무엇을 찾아드릴까요?",
                subtitle: "가게 이름, 상품(예: 삼겹살), 시장을 검색해 보세요."
            )
        } else if viewModel.results.isEmpty {
            EmptyStateView(
                iconName: "text.magnifyingglass",
                title: "검색 결과가 없어요",
                subtitle: "다른 키워드로 검색해 보시겠어요?"
            )
        } else {
            ScrollView {
                LazyVStack(spacing: AppSpacing.sm) {
                    ForEach(viewModel.results) { m in
                        MerchantCard(merchant: m, onTap: { navigateToDetailId = m.id })
                    }
                }
                .padding(.horizontal, AppSpacing.lg)
                .padding(.bottom, AppSpacing.xxl)
            }
        }
    }
}

private struct SuggestionRow: View {
    let onTap: (String) -> Void
    private let suggestions: [String] = ["삼겹살", "약국", "카페", "떡", "안양중앙시장", "안양사랑페이"]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: AppSpacing.xs) {
                ForEach(suggestions, id: \.self) { s in
                    Button { onTap(s) } label: {
                        Text(s)
                            .font(AppTypography.chip)
                            .foregroundStyle(AppColor.textPrimary)
                            .padding(.horizontal, AppSpacing.md)
                            .frame(height: 32)
                            .background(Capsule().fill(AppColor.surface))
                            .overlay(Capsule().stroke(AppColor.divider, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

#Preview {
    SearchHomeView()
        .environment(FavoritesStore.previewInstance())
}
