import SwiftUI

/// UConn-inspired Connecticut palette (no Husky marks), light only: navy #000E2F, white, gray #7C878E for rules,
/// and a tomato-red fill. Tomato always carries white text; the gray is never text (3.7:1 on white).
enum Theme {
    static let navy = Color(hex: 0x000E2F)
    static let navy2 = Color(hex: 0x2A4170)
    static let tomato = Color(hex: 0xB3261E)
    static let tomatoSoft = Color(hex: 0xF8DEDA)
    static let onTomatoSoft = Color(hex: 0x6B1510)
    static let gray = Color(hex: 0x7C878E)
    static let ink = Color(hex: 0x0B1426)
    static let ink2 = Color(hex: 0x2B3A55)
    static let muted = Color(hex: 0x4C5870)
    static let surface = Color.white
    static let surface2 = Color(hex: 0xF2F4F8)
    static let surface3 = Color(hex: 0xE3E8F0)
    static let rule = Color(hex: 0xDCE2EB)
    static let rule2 = Color(hex: 0xB9C3D2)

    /// Farmington Valley Health District's own A/B/C/U ratings (official, posted at the restaurant).
    static let ratingColors: [String: Color] = ["A": Color(hex: 0x12733A), "B": Color(hex: 0x4B6E1B), "C": Color(hex: 0x8A5A00), "U": Color(hex: 0xB3261E)]
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

/// A small uppercase label: "APIZZA", "SEASONAL".
struct Chip: View {
    enum Style { case tomato, navy, plain, dashed }
    let text: String
    var style: Style = .plain

    var body: some View {
        Text(text.uppercased())
            .font(.caption2.weight(.bold))
            .tracking(0.4)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .foregroundStyle(style == .navy ? Color.white : style == .tomato ? Theme.onTomatoSoft : style == .dashed ? Theme.muted : Theme.navy)
            .background {
                RoundedRectangle(cornerRadius: 5).fill(style == .tomato ? Theme.tomatoSoft : style == .navy ? Theme.navy : style == .dashed ? .clear : Theme.surface2)
            }
            .overlay {
                if style == .dashed { RoundedRectangle(cornerRadius: 5).strokeBorder(Theme.rule2, style: StrokeStyle(lineWidth: 1, dash: [3, 2])) }
            }
            .accessibilityLabel(text)
    }
}

/// An official Farmington Valley Health District rating letter.
struct RatingBadge: View {
    let rating: String
    var size: CGFloat = 22

    var body: some View {
        Text(rating)
            .displayFont(size * 0.72)
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(RoundedRectangle(cornerRadius: size * 0.27).fill(Theme.ratingColors[rating] ?? Theme.muted))
            .accessibilityLabel("Health rating \(rating)")
    }
}

/// The Long Island Sound shoreline: a low wave, the one Connecticut element in the header.
struct Shoreline: Shape {
    func path(in r: CGRect) -> Path {
        var p = Path()
        let mid = r.midY, amp = r.height * 0.38, w = r.width
        p.move(to: CGPoint(x: 0, y: mid))
        let n = 6
        for i in 0..<n {
            let x0 = w * CGFloat(i) / CGFloat(n), x1 = w * CGFloat(i + 1) / CGFloat(n)
            p.addCurve(to: CGPoint(x: x1, y: mid), control1: CGPoint(x: x0 + (x1 - x0) * 0.33, y: mid - amp), control2: CGPoint(x: x0 + (x1 - x0) * 0.66, y: mid + amp))
        }
        p.addLine(to: CGPoint(x: w, y: r.maxY)); p.addLine(to: CGPoint(x: 0, y: r.maxY)); p.closeSubpath()
        return p
    }
}

/// Condensed, heavy display type for titles and big numbers (the system font's compressed width). It scales with the
/// reader's text size, capped at 1.6× so a big number can't swallow its row.
struct DisplayFont: ViewModifier {
    let size: CGFloat
    var weight: Font.Weight = .black
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1

    func body(content: Content) -> some View {
        content.font(.system(size: size * min(scale, 1.6), weight: weight).width(.compressed))
    }
}

extension View {
    func displayFont(_ size: CGFloat, weight: Font.Weight = .black) -> some View {
        modifier(DisplayFont(size: size, weight: weight))
    }
}
