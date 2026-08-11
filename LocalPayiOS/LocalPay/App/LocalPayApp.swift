import SwiftUI

@main
struct LocalPayApp: App {

    /// 전역 상태 저장소. Environment 로 주입한다.
    @State private var favoritesStore = FavoritesStore()
    @State private var reviewsStore = ReviewsStore()

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environment(favoritesStore)
                .environment(reviewsStore)
        }
    }
}
