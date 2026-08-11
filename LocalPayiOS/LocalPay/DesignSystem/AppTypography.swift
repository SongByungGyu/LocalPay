import SwiftUI

/// 텍스트 크기 토큰. CLAUDE.md §31 을 따른다.
enum AppTypography {
    static let navigationTitle = Font.system(size: 22, weight: .bold)
    static let sectionTitle    = Font.system(size: 18, weight: .semibold)
    static let bodyLarge       = Font.system(size: 17, weight: .regular)
    static let body            = Font.system(size: 15, weight: .regular)
    static let caption         = Font.system(size: 13, weight: .regular)
    static let button          = Font.system(size: 16, weight: .semibold)
    static let chip            = Font.system(size: 14, weight: .medium)
}
