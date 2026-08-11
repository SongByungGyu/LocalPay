import CoreLocation
import MapKit
import SwiftUI

/// 지도 홈. Phase 2 구현본. CLAUDE.md §7, §8, §10, §15.
///
/// - MapKit iOS 17 Map API 사용
/// - Marker 는 custom SwiftUI Annotation (`MerchantMarker`)
/// - 상단 Floating SearchBar → Search Tab 으로 유도 (Phase 4 에서 실제 검색)
/// - 결제수단·카테고리 Filter Bar 는 지도 위 오버레이
/// - 우측 하단 FloatingLocationButton 으로 현재 위치로 이동
struct MapHomeView: View {

    @State private var viewModel = MapHomeViewModel()
    @State private var locationService = LocationService()
    @State private var cameraPosition: MapCameraPosition = .region(
        MKCoordinateRegion(
            center: MapRegion.anyangDefault.center,
            span: MKCoordinateSpan(
                latitudeDelta: MapRegion.anyangDefault.latitudeDelta,
                longitudeDelta: MapRegion.anyangDefault.longitudeDelta
            )
        )
    )
    @State private var searchBarText: String = ""
    @State private var pushSearchTab: (() -> Void)? = nil
    @State private var showLocationDenied: Bool = false
    @State private var navigateToDetailId: String?

    var body: some View {
        NavigationStack {
            ZStack(alignment: .top) {
                mapLayer

                VStack(spacing: AppSpacing.sm) {
                    Spacer().frame(height: AppSpacing.xs)

                    AppSearchBar(
                        placeholder: "가게, 상품, 시장을 검색해보세요",
                        showsChevron: true,
                        onTap: { /* 검색 Tab 이동은 RootTabView 확장 필요. 지금은 자체 검색 sheet 대신 tap-to-focus 로 처리 */ },
                        text: $searchBarText,
                        onSubmit: nil
                    )
                    .padding(.horizontal, AppSpacing.lg)

                    PaymentFilterBar(selection: $viewModel.paymentFilter)
                        .padding(.horizontal, AppSpacing.lg)

                    CategoryScrollBar(selection: $viewModel.categoryFilter)
                }
                .padding(.top, AppSpacing.sm)
                .background(topGradient.ignoresSafeArea(edges: .top))

                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        FloatingLocationButton(
                            isPermissionGranted: locationService.permission == .granted,
                            action: onTapLocationButton
                        )
                        .padding(.trailing, AppSpacing.lg)
                        .padding(.bottom, viewModel.selectedMerchant == nil ? AppSpacing.lg : 240)
                    }
                }
                .animation(.easeInOut(duration: 0.2), value: viewModel.selectedMerchant == nil)

                if let m = viewModel.selectedMerchant {
                    VStack {
                        Spacer()
                        MerchantPreviewCard(
                            merchant: m,
                            onClose: { viewModel.clearSelection() },
                            onOpenDetail: { navigateToDetailId = m.id }
                        )
                        .padding(.horizontal, AppSpacing.lg)
                        .padding(.bottom, AppSpacing.lg)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    .animation(.spring(response: 0.35, dampingFraction: 0.85), value: viewModel.selectedMerchantId)
                }

                if locationService.permission == .denied && showLocationDenied {
                    LocationDeniedBanner(onDismiss: { showLocationDenied = false })
                        .padding(.top, 200)
                }

                if !viewModel.isLoading && viewModel.visibleMerchants.isEmpty && viewModel.selectedMerchant == nil {
                    NoMerchantChip()
                        .padding(.top, 210)
                }

                DemoBadgeOverlay()
                    .padding(.top, 200)
            }
            .navigationBarHidden(true)
            .task {
                await viewModel.loadInitial()
                locationService.requestWhenInUse()
            }
            .onChange(of: viewModel.paymentFilter) { _, _ in
                Task { await viewModel.onFilterChanged() }
            }
            .onChange(of: viewModel.categoryFilter) { _, _ in
                Task { await viewModel.onFilterChanged() }
            }
            .navigationDestination(item: $navigateToDetailId) { id in
                MerchantDetailView(merchantId: id)
            }
        }
    }

    // MARK: - Map

    @ViewBuilder
    private var mapLayer: some View {
        Map(position: $cameraPosition, selection: $viewModel.selectedMerchantId) {
            UserAnnotation()

            ForEach(viewModel.markers) { marker in
                Annotation(
                    "",
                    coordinate: marker.coordinate,
                    anchor: .bottom
                ) {
                    MerchantMarker(
                        badge: marker.badge,
                        category: marker.category,
                        isSelected: marker.isSelected
                    )
                    .onTapGesture {
                        viewModel.selectMerchant(id: marker.id)
                    }
                }
                .tag(marker.id)
            }
        }
        .mapControls {
            MapCompass()
            MapScaleView()
        }
        .ignoresSafeArea(edges: .bottom)
    }

    private var topGradient: LinearGradient {
        LinearGradient(
            gradient: Gradient(colors: [
                AppColor.background.opacity(0.98),
                AppColor.background.opacity(0.85),
                AppColor.background.opacity(0.0)
            ]),
            startPoint: .top,
            endPoint: .bottom
        )
    }

    // MARK: - Actions

    private func onTapLocationButton() {
        switch locationService.permission {
        case .granted:
            let coord = locationService.effectiveCoordinate
            withAnimation(.easeInOut(duration: 0.4)) {
                cameraPosition = .region(
                    MKCoordinateRegion(
                        center: coord,
                        span: MKCoordinateSpan(latitudeDelta: 0.02, longitudeDelta: 0.02)
                    )
                )
            }
        case .unknown:
            locationService.requestWhenInUse()
        case .denied:
            showLocationDenied = true
        }
    }
}

/// 화면 전체에서 항상 DEMO 임을 인지시키는 작은 오버레이. CLAUDE.md §12.
private struct DemoBadgeOverlay: View {
    var body: some View {
        HStack {
            Spacer()
            DemoBadge()
                .padding(.trailing, AppSpacing.lg)
        }
    }
}

/// 위치 권한 거절 시 상단에 뜨는 안내 배너.
private struct LocationDeniedBanner: View {
    let onDismiss: () -> Void

    var body: some View {
        HStack(spacing: AppSpacing.sm) {
            Image(systemName: "location.slash")
                .foregroundStyle(AppColor.error)
            VStack(alignment: .leading, spacing: 2) {
                Text("위치 권한이 꺼져있어요")
                    .font(AppTypography.chip.weight(.semibold))
                    .foregroundStyle(AppColor.textPrimary)
                Text("설정에서 위치 접근을 허용하면 주변 가맹점을 더 정확히 안내해 드릴 수 있어요.")
                    .font(.system(size: 12))
                    .foregroundStyle(AppColor.textSecondary)
            }
            Spacer()
            Button {
                onDismiss()
            } label: {
                Image(systemName: "xmark")
                    .foregroundStyle(AppColor.textSecondary)
            }
            .buttonStyle(.plain)
        }
        .padding(AppSpacing.md)
        .background(
            RoundedRectangle(cornerRadius: AppRadius.card).fill(AppColor.surface)
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.card).stroke(AppColor.error.opacity(0.35), lineWidth: 1)
        )
        .padding(.horizontal, AppSpacing.lg)
        .shadow(color: Color.black.opacity(0.08), radius: 6, x: 0, y: 2)
    }
}

/// 필터 결과 0건일 때 지도 상단에 뜨는 안내 chip.
private struct NoMerchantChip: View {
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: "mappin.slash")
                .font(.system(size: 12, weight: .semibold))
            Text("현재 필터에 맞는 가맹점이 없어요")
                .font(AppTypography.chip)
        }
        .foregroundStyle(AppColor.textSecondary)
        .padding(.horizontal, AppSpacing.md)
        .padding(.vertical, 8)
        .background(
            Capsule().fill(AppColor.background)
        )
        .overlay(
            Capsule().stroke(AppColor.divider, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.08), radius: 6, x: 0, y: 2)
    }
}

extension String: @retroactive Identifiable {
    public var id: String { self }
}

#Preview {
    MapHomeView()
}
