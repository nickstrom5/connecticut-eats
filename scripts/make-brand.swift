// Regenerates the brand images: the app icon (a charred, oblong New Haven apizza on a sheet pan; Nick's pick, Oct 5, 2026),
// docs/brand/, and the site's og.png, favicons and manifest icons.
// Usage: swift scripts/make-brand.swift   (run from ct-eats/)
import AppKit
import CoreGraphics

let root = FileManager.default.currentDirectoryPath
func rgb(_ hex: UInt32, _ a: CGFloat = 1) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255, blue: CGFloat(hex & 0xFF) / 255, alpha: a)
}
let navy = rgb(0x000E2F), white = rgb(0xFFFFFF), tomato = rgb(0xB3261E), gray = rgb(0x7C878E)

func canvas(_ w: Int, _ h: Int, _ draw: (CGContext) -> Void) -> CGImage {
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.setShouldAntialias(true); ctx.interpolationQuality = .high
    draw(ctx)
    return ctx.makeImage()!
}
func save(_ img: CGImage, _ path: String) {
    let url = URL(fileURLWithPath: root + "/" + path)
    try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    try! NSBitmapImageRep(cgImage: img).representation(using: .png, properties: [:])!.write(to: url)
    print("wrote", path)
}
/// A smooth closed blob around (cx, cy): an ellipse whose radius wobbles by `noise` (deterministic, so the pie is always the same pie).
func blob(_ cx: CGFloat, _ cy: CGFloat, _ rx: CGFloat, _ ry: CGFloat, noise: CGFloat, seed: CGFloat, n: Int = 48) -> CGPath {
    var pts: [CGPoint] = []
    for i in 0..<n {
        let t = CGFloat(i) / CGFloat(n) * 2 * .pi
        let k = 1 + noise * (0.55 * sin(3 * t + seed) + 0.3 * sin(7 * t + 2 * seed) + 0.15 * sin(13 * t + 3 * seed))
        pts.append(CGPoint(x: cx + rx * k * cos(t), y: cy + ry * k * sin(t)))
    }
    let p = CGMutablePath()
    let mid = { (a: CGPoint, b: CGPoint) in CGPoint(x: (a.x + b.x) / 2, y: (a.y + b.y) / 2) }
    p.move(to: mid(pts[n - 1], pts[0]))
    for i in 0..<n { p.addQuadCurve(to: mid(pts[i], pts[(i + 1) % n]), control: pts[i]) }
    p.closeSubpath()
    return p
}

// ---- concept A: a charred, oblong New Haven tomato pie on a sheet pan
func apizza(_ c: CGContext, _ s: CGFloat) {
    c.saveGState()
    c.translateBy(x: s / 2, y: s / 2); c.rotate(by: -0.26); c.translateBy(x: -s / 2, y: -s / 2)
    // sheet pan
    let pan = CGRect(x: s * 0.09, y: s * 0.20, width: s * 0.82, height: s * 0.60)
    c.setFillColor(gray); c.addPath(CGPath(roundedRect: pan, cornerWidth: s * 0.05, cornerHeight: s * 0.05, transform: nil)); c.fillPath()
    c.setFillColor(rgb(0x5F696F)); c.addPath(CGPath(roundedRect: pan.insetBy(dx: s * 0.025, dy: s * 0.025), cornerWidth: s * 0.035, cornerHeight: s * 0.035, transform: nil)); c.fillPath()
    // crust, sauce, char
    c.setFillColor(rgb(0xD99A5B)); c.addPath(blob(s * 0.5, s * 0.5, s * 0.36, s * 0.255, noise: 0.06, seed: 1.3)); c.fillPath()
    c.setFillColor(rgb(0xB82E1C)); c.addPath(blob(s * 0.5, s * 0.5, s * 0.295, s * 0.195, noise: 0.08, seed: 2.1)); c.fillPath()
    c.setFillColor(rgb(0x8F1F12))
    for (x, y, r) in [(0.40, 0.55, 0.05), (0.60, 0.44, 0.045), (0.52, 0.60, 0.03), (0.33, 0.44, 0.03), (0.68, 0.56, 0.035)] as [(CGFloat, CGFloat, CGFloat)] {
        c.addPath(blob(s * x, s * y, s * r, s * r * 0.75, noise: 0.15, seed: x * 10)); c.fillPath()
    }
    // grated cheese flecks
    c.setFillColor(rgb(0xF3E3C3))
    for (x, y) in [(0.45, 0.47), (0.56, 0.53), (0.38, 0.50), (0.63, 0.49), (0.50, 0.40), (0.47, 0.58), (0.70, 0.47), (0.31, 0.55)] as [(CGFloat, CGFloat)] {
        c.fillEllipse(in: CGRect(x: s * x, y: s * y, width: s * 0.022, height: s * 0.016))
    }
    // the char: small dark blisters scattered along the rim, the mark of a coal oven
    for i in 0..<26 {
        let t = CGFloat(i) / 26 * 2 * .pi + 0.35 * sin(CGFloat(i) * 2.3)
        let ring = 0.315 + 0.03 * sin(CGFloat(i) * 4.7)
        let rx = s * ring, ry = s * ring * 0.70
        let r = s * (0.010 + 0.010 * (0.5 + 0.5 * sin(CGFloat(i) * 5.1)))
        c.setFillColor(i % 3 == 0 ? rgb(0x5A3418) : rgb(0x2E1A0E))
        c.addPath(blob(s * 0.5 + rx * cos(t), s * 0.5 + ry * sin(t), r * 1.4, r, noise: 0.15, seed: CGFloat(i))); c.fillPath()
    }
    c.restoreGState()
}

func icon(_ size: Int) -> CGImage {
    canvas(size, size) { c in c.setFillColor(navy); c.fill(CGRect(x: 0, y: 0, width: size, height: size)); apizza(c, CGFloat(size)) }
}
/// Opaque: the App Store icon may not have an alpha channel.
func opaque(_ img: CGImage) -> CGImage {
    let ctx = CGContext(data: nil, width: img.width, height: img.height, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.draw(img, in: CGRect(x: 0, y: 0, width: img.width, height: img.height))
    return ctx.makeImage()!
}
func text(_ c: CGContext, _ str: String, font: NSFont, color: CGColor, at p: CGPoint) {
    let attr = NSAttributedString(string: str, attributes: [.font: font, .foregroundColor: NSColor(cgColor: color)!])
    c.textPosition = p; CTLineDraw(CTLineCreateWithAttributedString(attr), c)
}
func heavy(_ size: CGFloat) -> NSFont { NSFont(name: "HelveticaNeue-CondensedBlack", size: size) ?? NSFont.systemFont(ofSize: size, weight: .black) }

let appIcon = opaque(icon(1024))
save(appIcon, "ConnecticutEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png")
save(appIcon, "docs/brand/icon-1024.png")
save(opaque(icon(512)), "docs/icon-512.png")
save(opaque(icon(192)), "docs/icon-192.png")
save(opaque(icon(180)), "docs/apple-touch-icon.png")
save(opaque(icon(32)), "docs/favicon-32.png")
let og = canvas(1200, 630) { c in
    c.setFillColor(navy); c.fill(CGRect(x: 0, y: 0, width: 1200, height: 630))
    c.setFillColor(tomato); c.fill(CGRect(x: 72, y: 470, width: 90, height: 12))
    text(c, "CONNECTICUT", font: heavy(118), color: white, at: CGPoint(x: 66, y: 330))
    text(c, "EATS", font: heavy(118), color: rgb(0xFF8A7F), at: CGPoint(x: 66, y: 215))
    text(c, "Apizza & lobster roll guide · every restaurant in 169 towns", font: NSFont.systemFont(ofSize: 30, weight: .semibold), color: white, at: CGPoint(x: 70, y: 150))
    text(c, "Free for iPhone and iPad", font: NSFont.systemFont(ofSize: 28, weight: .regular), color: rgb(0xFF8A7F), at: CGPoint(x: 70, y: 98))
    c.saveGState(); c.translateBy(x: 800, y: 150); apizza(c, 360); c.restoreGState()
}
save(opaque(og), "docs/og.png")
