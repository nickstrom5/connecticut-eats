// Regenerates the brand images: the app icon (a charred, oblong New Haven apizza on a sheet pan; Nick's pick, Oct 5, 2026;
// redrawn Oct 9, 2026 in the shared Eats Ranked icon style, with one slice pulled out), docs/brand/, and the site's og.png,
// favicons and manifest icons.
// Usage: swift scripts/make-brand.swift   (run from ct-eats/)
//        swift scripts/make-brand.swift og ["<tagline>"]   redraws docs/og.png only, never the icons. scripts/make-site.py runs
//        this whenever the restaurant or town count changes; without a tagline it reads og_line from playbook/site-numbers.json.
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
let crust = rgb(0xD99A5B), sauce = rgb(0xB82E1C), char = rgb(0x2E1A0E), cheese = rgb(0xF3E3C3)

/// A smooth oblong with a different reach on each side, so it is irregular without being rotated: 4 cubic Béziers through
/// the right, top, left and bottom points (the top and bottom points slid sideways by `topX` and `bottomX`). Handles are
/// `k` of each reach (0.552 = an ellipse; more = squarer, like dough stretched into a pan). Returns the path and samples.
func oblong(_ o: CGPoint, right: CGFloat, top: CGFloat, left: CGFloat, bottom: CGFloat, topX: CGFloat = 0, bottomX: CGFloat = 0,
            k: CGFloat) -> (CGPath, [CGPoint]) {
    let R = CGPoint(x: o.x + right, y: o.y), T = CGPoint(x: o.x + topX, y: o.y + top)
    let L = CGPoint(x: o.x - left, y: o.y), B = CGPoint(x: o.x + bottomX, y: o.y - bottom)
    let segs: [(CGPoint, CGPoint, CGPoint, CGPoint)] = [
        (R, CGPoint(x: R.x, y: R.y + k * top), CGPoint(x: T.x + k * (right - topX), y: T.y), T),
        (T, CGPoint(x: T.x - k * (left + topX), y: T.y), CGPoint(x: L.x, y: L.y + k * top), L),
        (L, CGPoint(x: L.x, y: L.y - k * bottom), CGPoint(x: B.x - k * (left + bottomX), y: B.y), B),
        (B, CGPoint(x: B.x + k * (right - bottomX), y: B.y), CGPoint(x: R.x, y: R.y - k * bottom), R),
    ]
    let path = CGMutablePath()
    var samples: [CGPoint] = []
    path.move(to: R)
    for (p0, c1, c2, p3) in segs {
        path.addCurve(to: p3, control1: c1, control2: c2)
        for j in 0..<200 {
            let s = CGFloat(j) / 200, q = 1 - s
            samples.append(CGPoint(x: q * q * q * p0.x + 3 * q * q * s * c1.x + 3 * q * s * s * c2.x + s * s * s * p3.x,
                                   y: q * q * q * p0.y + 3 * q * q * s * c1.y + 3 * q * s * s * c2.y + s * s * s * p3.y))
        }
    }
    path.closeSubpath()
    return (path, samples)
}
/// The point of a sampled loop that lies at `deg` degrees from `o` (CoreGraphics y-up).
func edge(_ samples: [CGPoint], _ o: CGPoint, _ deg: CGFloat) -> CGPoint {
    let a = deg * .pi / 180
    func d(_ q: CGPoint) -> CGFloat { abs(remainder(atan2(q.y - o.y, q.x - o.x) - a, 2 * .pi)) }
    return samples.min { d($0) < d($1) }!
}

// ---- the icon: a New Haven apizza on its sheet pan, seen from straight above, with one slice pulled a little way out.
// Redrawn 2026-10-09 in the shared Eats Ranked icon style Nick approved (../state-prompts/ICON-STYLE.md): flat, level and
// centred, the same food and colours as Nick's Oct 5 pick. The pan is the one backing shape (one flat gray, 0 degrees,
// centred, showing only as a rim); a 13 px navy ring runs round the pie and the slice, and the cut between them is navy.
// 6 colours in all; marks: 5 char blisters + 3 cheese accents. Paints no background, so og.png can call it at another size.
func apizza(_ c: CGContext, _ s: CGFloat) {
    let u = s / 1024
    c.saveGState()
    c.setLineJoin(.round); c.setLineCap(.round)
    // the sheet pan: one flat gray rounded rectangle, 0.75 x 0.48, centred exactly (coverage stays under 36%)
    let panW = 768 * u, panH = 490 * u
    c.setFillColor(gray)
    c.addPath(CGPath(roundedRect: CGRect(x: (s - panW) / 2, y: (s - panH) / 2, width: panW, height: panH),
                     cornerWidth: 51 * u, cornerHeight: 51 * u, transform: nil))
    c.fillPath()

    // pie centre: up and left of the pan's centre, so the pulled-out slice still lands on the pan
    let o = CGPoint(x: s / 2 - 14 * u, y: s / 2 + 8 * u)
    // the crust's outside edge: an oblong about 0.64 x 0.38, squarer than an oval (stretched into the pan), a touch
    // fuller at the right-hand end and the bottom. 4 segments
    let (rim, rimPts) = oblong(o, right: 330 * u, top: 190 * u, left: 322 * u, bottom: 196 * u, topX: -10 * u, bottomX: -10 * u, k: 0.66)
    // the sauce: its own squarer oblong, set a little off-centre, so the rim runs 64-82 px wide and looks puffy. 4 segments
    let (top, topPts) = oblong(CGPoint(x: o.x + 4 * u, y: o.y - 3 * u), right: 256 * u, top: 120 * u, left: 250 * u, bottom: 128 * u,
                               topX: 8 * u, bottomX: 8 * u, k: 0.68)

    // char: 5 big coal-oven blisters on the rim only, laid along it, spaced unevenly; one rides on the slice.
    let blisters = CGMutablePath()
    for (deg, len, wid, f) in [(-24, 88, 50, 0.5), (40, 76, 46, 0.52), (122, 90, 52, 0.5), (186, 74, 46, 0.5), (246, 88, 50, 0.5)] as [(CGFloat, CGFloat, CGFloat, CGFloat)] {
        let a = edge(rimPts, o, deg), b = edge(topPts, o, deg)
        let p = CGPoint(x: b.x + (a.x - b.x) * f, y: b.y + (a.y - b.y) * f)
        var t = CGAffineTransform(translationX: p.x, y: p.y).rotated(by: atan2(a.y - b.y, a.x - b.x) + .pi / 2)
        blisters.addPath(CGPath(ellipseIn: CGRect(x: -len * u / 2, y: -wid * u / 2, width: len * u, height: wid * u), transform: &t))
    }
    // cheese: 3 grated-pecorino accents on the sauce, one of them on the slice
    let flecks = CGMutablePath()
    for (x, y, w, h, deg) in [(-126, 24, 60, 46, 20), (30, 66, 56, 42, -25), (150, -58, 56, 42, 10)] as [(CGFloat, CGFloat, CGFloat, CGFloat, CGFloat)] {
        var t = CGAffineTransform(translationX: o.x + x * u, y: o.y + y * u).rotated(by: deg * .pi / 180)
        flecks.addPath(CGPath(ellipseIn: CGRect(x: -w * u / 2, y: -h * u / 2, width: w * u, height: h * u), transform: &t))
    }

    // the slice: a 50-degree wedge toward the lower right, cut out with a 26 px gap and slid 30 px straight out
    let mid: CGFloat = -30 * .pi / 180, half: CGFloat = 25 * .pi / 180, far = 900 * u
    let wedge = CGMutablePath()
    wedge.move(to: o)
    wedge.addLine(to: CGPoint(x: o.x + far * cos(mid - half), y: o.y + far * sin(mid - half)))
    wedge.addLine(to: CGPoint(x: o.x + far * cos(mid + half), y: o.y + far * sin(mid + half)))
    wedge.closeSubpath()
    let cutLines = CGMutablePath()
    cutLines.move(to: CGPoint(x: o.x + far * cos(mid - half), y: o.y + far * sin(mid - half)))
    cutLines.addLine(to: o)
    cutLines.addLine(to: CGPoint(x: o.x + far * cos(mid + half), y: o.y + far * sin(mid + half)))
    let gap = cutLines.copy(strokingWithWidth: 26 * u, lineCap: .round, lineJoin: .round, miterLimit: 10)
    let removed = wedge.union(gap)
    let sliceArea = wedge.subtracting(gap)
    var slide = CGAffineTransform(translationX: 30 * u * cos(mid), y: 30 * u * sin(mid))

    // ring: 13 px of navy round the pie and round the slice (26 px round-join strokes under them). The whole pie's outline
    // is filled navy too, so the cut and the space the slice left read as one navy gap with no pan in it.
    let slicePiece = rim.intersection(sliceArea).copy(using: &slide)!
    c.setStrokeColor(navy); c.setFillColor(navy); c.setLineWidth(26 * u)
    c.addPath(rim); c.fillPath()
    c.addPath(rim); c.strokePath()
    c.addPath(slicePiece); c.strokePath()
    // then crust, sauce and the marks, each split into the pie and the slid-out slice
    for (layer, colour) in [(rim, crust), (top, sauce), (blisters as CGPath, char), (flecks as CGPath, cheese)] {
        c.setFillColor(colour)
        c.addPath(layer.subtracting(removed)); c.fillPath()
        c.addPath(layer.intersection(sliceArea).copy(using: &slide)!); c.fillPath()
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

let args = Array(CommandLine.arguments.dropFirst())
let ogOnly = args.first == "og"
if !ogOnly {
    let appIcon = opaque(icon(1024))
    save(appIcon, "ConnecticutEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png")
    save(appIcon, "docs/brand/icon-1024.png")
    save(opaque(icon(512)), "docs/icon-512.png")
    save(opaque(icon(192)), "docs/icon-192.png")
    save(opaque(icon(180)), "docs/apple-touch-icon.png")
    save(opaque(icon(32)), "docs/favicon-32.png")
}
/// The tagline carries the directory's real counts ("9,615 restaurants in 166 towns", from the data), never "every restaurant".
func ogLine() -> String {
    if ogOnly && args.count > 1 { return args[1] }
    let url = URL(fileURLWithPath: root + "/playbook/site-numbers.json")
    guard let data = try? Data(contentsOf: url), let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let line = json["og_line"] as? String else {
        fatalError("no og_line in playbook/site-numbers.json: run .venv/bin/python scripts/make-site.py first")
    }
    return line
}
let tagline = ogLine()
let og = canvas(1200, 630) { c in
    c.setFillColor(navy); c.fill(CGRect(x: 0, y: 0, width: 1200, height: 630))
    c.setFillColor(tomato); c.fill(CGRect(x: 72, y: 470, width: 90, height: 12))
    text(c, "CONNECTICUT", font: heavy(118), color: white, at: CGPoint(x: 66, y: 330))
    text(c, "EATS", font: heavy(118), color: rgb(0xFF8A7F), at: CGPoint(x: 66, y: 215))
    text(c, tagline, font: NSFont.systemFont(ofSize: 30, weight: .semibold), color: white, at: CGPoint(x: 70, y: 150))
    text(c, "Free for iPhone and iPad", font: NSFont.systemFont(ofSize: 28, weight: .regular), color: rgb(0xFF8A7F), at: CGPoint(x: 70, y: 98))
    c.saveGState(); c.translateBy(x: 800, y: 150); apizza(c, 360); c.restoreGState()
}
save(opaque(og), "docs/og.png")
