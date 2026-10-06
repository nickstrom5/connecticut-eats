// Three app-icon concepts for Nick to pick from: a New Haven apizza, a hot buttered lobster roll, a steamed cheeseburger.
// Usage: swift scripts/icon-concepts.swift   (run from ct-eats/) -> playbook/icon-concepts.png and playbook/icon-<name>-1024.png
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

// ---- concept B: a hot buttered lobster roll in a split-top bun
func lobsterRoll(_ c: CGContext, _ s: CGFloat) {
    // meat: overlapping chunks, red outside and white inside, glossy with butter
    let chunks: [(CGFloat, CGFloat, CGFloat)] = [(0.25, 0.55, 0.10), (0.37, 0.60, 0.11), (0.50, 0.58, 0.115), (0.63, 0.61, 0.11), (0.75, 0.55, 0.10), (0.44, 0.52, 0.09), (0.58, 0.52, 0.09)]
    for (i, (x, y, r)) in chunks.enumerated() {
        // lobster meat is mostly white, with the red-orange of the shell on its outside edge
        c.setFillColor(rgb(0xE8603C)); c.addPath(blob(s * x, s * y, s * r, s * r * 0.82, noise: 0.10, seed: CGFloat(i) * 1.7)); c.fillPath()
        c.setFillColor(rgb(0xFCEDE6)); c.addPath(blob(s * (x + 0.01), s * (y - 0.018), s * r * 0.80, s * r * 0.62, noise: 0.12, seed: CGFloat(i))); c.fillPath()
        c.setFillColor(rgb(0xF4A08A)); c.addPath(blob(s * (x - 0.02), s * (y + 0.02), s * r * 0.30, s * r * 0.16, noise: 0.1, seed: CGFloat(i) * 3)); c.fillPath()
    }
    c.setFillColor(rgb(0xFFD966, 0.35))   // a glaze of melted butter over the top
    c.addPath(blob(s * 0.5, s * 0.60, s * 0.30, s * 0.07, noise: 0.05, seed: 0.4)); c.fillPath()
    c.setFillColor(rgb(0xFFE07A, 0.95))   // butter shine
    for (x, y, w) in [(0.33, 0.66, 0.05), (0.55, 0.67, 0.06), (0.71, 0.63, 0.04), (0.46, 0.63, 0.03)] as [(CGFloat, CGFloat, CGFloat)] {
        c.fillEllipse(in: CGRect(x: s * x, y: s * y, width: s * w, height: s * w * 0.45))
    }
    // the split-top bun's front wall: griddled gold sides, a pale crumb band along the top edge
    let bun = CGRect(x: s * 0.13, y: s * 0.28, width: s * 0.74, height: s * 0.25)
    c.setFillColor(rgb(0xF2D7A6)); c.addPath(CGPath(roundedRect: bun, cornerWidth: s * 0.08, cornerHeight: s * 0.08, transform: nil)); c.fillPath()
    let toasted = CGRect(x: s * 0.13, y: s * 0.28, width: s * 0.74, height: s * 0.205)
    c.setFillColor(rgb(0xD48A3C)); c.addPath(CGPath(roundedRect: toasted, cornerWidth: s * 0.08, cornerHeight: s * 0.08, transform: nil)); c.fillPath()
    c.setFillColor(rgb(0xE9A85A))
    c.addPath(CGPath(roundedRect: CGRect(x: s * 0.17, y: s * 0.32, width: s * 0.66, height: s * 0.10), cornerWidth: s * 0.05, cornerHeight: s * 0.05, transform: nil)); c.fillPath()
}

// ---- concept C: a Meriden steamed cheeseburger, the white cheddar running down the sides
func steamedBurger(_ c: CGContext, _ s: CGFloat) {
    // steam
    c.setStrokeColor(rgb(0xFFFFFF, 0.75)); c.setLineWidth(s * 0.028); c.setLineCap(.round)
    for x in [0.38, 0.5, 0.62] as [CGFloat] {
        let p = CGMutablePath(); p.move(to: CGPoint(x: s * x, y: s * 0.72))
        p.addCurve(to: CGPoint(x: s * x, y: s * 0.90), control1: CGPoint(x: s * (x - 0.05), y: s * 0.78), control2: CGPoint(x: s * (x + 0.05), y: s * 0.84))
        c.addPath(p); c.strokePath()
    }
    // bottom bun
    c.setFillColor(rgb(0xD99A5B))
    c.addPath(CGPath(roundedRect: CGRect(x: s * 0.19, y: s * 0.18, width: s * 0.62, height: s * 0.11), cornerWidth: s * 0.05, cornerHeight: s * 0.05, transform: nil)); c.fillPath()
    // patty
    c.setFillColor(rgb(0x4E2817))
    c.addPath(CGPath(roundedRect: CGRect(x: s * 0.16, y: s * 0.28, width: s * 0.68, height: s * 0.12), cornerWidth: s * 0.05, cornerHeight: s * 0.05, transform: nil)); c.fillPath()
    // molten white cheddar: a layer plus drips down over the patty
    c.setFillColor(rgb(0xF6ECD2))
    c.addPath(CGPath(roundedRect: CGRect(x: s * 0.13, y: s * 0.385, width: s * 0.74, height: s * 0.07), cornerWidth: s * 0.035, cornerHeight: s * 0.035, transform: nil)); c.fillPath()
    for (x, len, w) in [(0.20, 0.13, 0.06), (0.36, 0.08, 0.05), (0.55, 0.15, 0.065), (0.73, 0.10, 0.055)] as [(CGFloat, CGFloat, CGFloat)] {
        let r = CGRect(x: s * x, y: s * (0.42 - len), width: s * w, height: s * len)
        c.addPath(CGPath(roundedRect: r, cornerWidth: s * w / 2, cornerHeight: s * w / 2, transform: nil)); c.fillPath()
    }
    // top bun dome
    let dome = CGMutablePath()
    dome.move(to: CGPoint(x: s * 0.17, y: s * 0.45))
    dome.addCurve(to: CGPoint(x: s * 0.83, y: s * 0.45), control1: CGPoint(x: s * 0.17, y: s * 0.74), control2: CGPoint(x: s * 0.83, y: s * 0.74))
    dome.closeSubpath()
    c.setFillColor(rgb(0xE0A35E)); c.addPath(dome); c.fillPath()
    c.setFillColor(rgb(0xF0C688, 0.9)); c.fillEllipse(in: CGRect(x: s * 0.30, y: s * 0.56, width: s * 0.20, height: s * 0.06))
}

let concepts: [(String, String, (CGContext, CGFloat) -> Void)] = [("apizza", "A · New Haven apizza", apizza), ("lobster", "B · Hot buttered lobster roll", lobsterRoll), ("steamed", "C · Steamed cheeseburger", steamedBurger)]
func icon(_ size: Int, _ f: (CGContext, CGFloat) -> Void) -> CGImage {
    canvas(size, size) { c in c.setFillColor(navy); c.fill(CGRect(x: 0, y: 0, width: size, height: size)); f(c, CGFloat(size)) }
}
for (n, _, f) in concepts { save(icon(1024, f), "playbook/icon-\(n)-1024.png") }

// contact sheet: each concept at 512, 180 and 60 px (with the iOS corner mask), on light and dark grounds
func text(_ c: CGContext, _ str: String, size: CGFloat, color: CGColor, at p: CGPoint, weight: NSFont.Weight = .semibold) {
    let attr = NSAttributedString(string: str, attributes: [.font: NSFont.systemFont(ofSize: size, weight: weight), .foregroundColor: NSColor(cgColor: color)!])
    c.textPosition = p; CTLineDraw(CTLineCreateWithAttributedString(attr), c)
}
let W = 1500, H = 1020
let sheet = canvas(W, H) { c in
    c.setFillColor(rgb(0xF2F4F8)); c.fill(CGRect(x: 0, y: 0, width: W, height: H))
    c.setFillColor(rgb(0x1C1C1E)); c.fill(CGRect(x: 0, y: 0, width: W, height: 150))
    for (i, (_, label, f)) in concepts.enumerated() {
        let x0 = CGFloat(40 + i * 490)
        text(c, label, size: 30, color: navy, at: CGPoint(x: x0, y: CGFloat(H) - 60))
        for (sz, y) in [(420, 420), (180, 190)] as [(Int, Int)] {
            let img = icon(sz, f), r = CGRect(x: x0, y: CGFloat(y), width: CGFloat(sz), height: CGFloat(sz))
            c.saveGState(); c.addPath(CGPath(roundedRect: r, cornerWidth: CGFloat(sz) * 0.225, cornerHeight: CGFloat(sz) * 0.225, transform: nil)); c.clip(); c.draw(img, in: r); c.restoreGState()
        }
        text(c, "512 · 180 · 60 px", size: 18, color: gray, at: CGPoint(x: x0 + 200, y: 260), weight: .regular)
        for (j, ground) in [rgb(0xF2F4F8), rgb(0x1C1C1E)].enumerated() {
            let img = icon(60, f), r = CGRect(x: x0 + 200 + CGFloat(j) * 90, y: j == 0 ? 190 : 45, width: 60, height: 60)
            _ = ground
            c.saveGState(); c.addPath(CGPath(roundedRect: r, cornerWidth: 13.5, cornerHeight: 13.5, transform: nil)); c.clip(); c.draw(img, in: r); c.restoreGState()
        }
        let img = icon(60, f), r = CGRect(x: x0 + 40, y: 45, width: 60, height: 60)
        c.saveGState(); c.addPath(CGPath(roundedRect: r, cornerWidth: 13.5, cornerHeight: 13.5, transform: nil)); c.clip(); c.draw(img, in: r); c.restoreGState()
        text(c, "CT Eats", size: 15, color: white, at: CGPoint(x: x0 + 44, y: 22), weight: .regular)
    }
}
save(sheet, "playbook/icon-concepts.png")
