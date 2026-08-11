import CoreGraphics
import SwiftUI

/// 간격 및 코너 반경 토큰. CLAUDE.md §31 을 따른다.
enum AppSpacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16   // 기본 horizontal padding
    static let xl: CGFloat = 20
    static let xxl: CGFloat = 24
}

enum AppRadius {
    static let chip: CGFloat = 18
    static let card: CGFloat = 16
    static let cardLarge: CGFloat = 20
    static let button: CGFloat = 12
}

enum AppSize {
    static let buttonHeight: CGFloat = 48
    static let buttonHeightLarge: CGFloat = 52
    static let chipHeight: CGFloat = 36
    static let chipHeightLarge: CGFloat = 40
    static let touchTargetMin: CGFloat = 44
}
