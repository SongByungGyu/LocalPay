import SwiftUI

/// Asset Catalog "Colors" 네임스페이스에 정의된 색상 토큰.
/// View 내부에서 색상을 하드코딩하지 않고 이 enum 을 사용한다.
enum AppColor {
    static let background     = Color("Colors/Background",     bundle: .main)
    static let surface        = Color("Colors/Surface",        bundle: .main)
    static let primary        = Color("Colors/Primary",        bundle: .main)
    static let onnuri         = Color("Colors/Onnuri",         bundle: .main)
    static let localCurrency  = Color("Colors/LocalCurrency",  bundle: .main)
    static let both           = Color("Colors/Both",           bundle: .main)
    static let textPrimary    = Color("Colors/TextPrimary",    bundle: .main)
    static let textSecondary  = Color("Colors/TextSecondary",  bundle: .main)
    static let divider        = Color("Colors/Divider",        bundle: .main)
    static let success        = Color("Colors/Success",        bundle: .main)
    static let error          = Color("Colors/Error",          bundle: .main)
}
