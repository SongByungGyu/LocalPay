import SwiftUI

/// 하단 4-Tab. CLAUDE.md §6.
/// Phase 1 에서는 각 Tab 이 Placeholder View 를 렌더링하고,
/// Phase 2 부터 실제 화면(MapHomeView, SearchHomeView 등)으로 교체된다.
struct RootTabView: View {

    @State private var selection: Tab = .map

    enum Tab: Hashable {
        case map, search, favorites, my
    }

    var body: some View {
        TabView(selection: $selection) {
            MapHomeView()
                .tabItem { Label("지도", systemImage: "map.fill") }
                .tag(Tab.map)

            SearchHomeView()
                .tabItem { Label("검색", systemImage: "magnifyingglass") }
                .tag(Tab.search)

            FavoritesHomeView()
                .tabItem { Label("즐겨찾기", systemImage: "heart.fill") }
                .tag(Tab.favorites)

            MyPageHomeView()
                .tabItem { Label("MY", systemImage: "person.fill") }
                .tag(Tab.my)
        }
        .tint(AppColor.primary)
    }
}

#Preview {
    RootTabView()
}
