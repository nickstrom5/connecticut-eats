import Foundation
import CoreLocation

// MARK: - The bundled data file (Resources/places.json), written by pipeline/connecticut.py with CT_APP=1

struct DataFile: Decodable {
    /// the date of the license data the build used
    let generated: String
    /// a hash of the places, new with every rebuild that changes anything (older files: none, so `generated` stands in)
    let data_version: String?
    /// when the hand-checked guides were last researched: "October 2026"
    let research_checked: String?
    /// the Overture Maps release: "2026-09-23.1"
    let overture: String?
    /// ids that changed since an earlier build: old id -> new id, so saved places and Spotlight entries follow a place
    let aliases: [String: String]?
    /// when the Farmington Valley Health District's ratings were copied, and each town's ratings page
    let fvhd_fetched: String?
    let fvhd_pages: [String: String]?
    let cities: [String]
    let villages: [String]
    let cuisines: [String]
    let brands: [String]
    let hosts: [String]
    let sources: [String]
    let count_restaurants: Int
    /// match rates measured against official lists: "hartford" (food licenses) and "statewide_liquor" (DCP permits)
    let calibration: [String: [String: CalibrationGroup]]
    let places: [PlaceRecord]
}

struct CalibrationGroup: Decodable, Hashable {
    let n: Int
    let matched: Double
}

/// Farmington Valley Health District's own rating: A (Excellent), B (Good), C (Fair), U (Unsatisfactory), posted at the restaurant.
struct HealthRating: Decodable, Hashable {
    let r: String
    let d: String?
    /// the name the district rated it under, when that isn't the name shown
    let n: String?
    var meaning: String {
        switch r {
        case "A": "Excellent"
        case "B": "Good"
        case "C": "Fair"
        case "U": "Unsatisfactory"
        default: r
        }
    }
}

struct PlaceRecord: Decodable {
    let id: String
    let n: String
    let c: Int?
    let vi: Int?
    let cu: Int
    let t: Int
    let s: Int
    let a: String?
    let z: String?
    let la: Double?
    let lo: Double?
    let b: Int?
    let ch: Int?
    let j: Int?
    let lk: String?
    let hcl: String?
    let v: Int?
    let bar: Int?
    let host: Int?
    let g: Int?
    let hc: Int?
    let k: Int?
    let h: Int?
    let ip: Double?
    /// the featured score of a hand-checked place (the classics' "Featured first" order); `ip` is only on icons
    let fs: Double?
    let note: String?
    let jbf: String?
    let hon: String?
    let dish: String?
    let sea: String?
    let seas: Int?
    let br: String?
    let chef: String?
    let f: Int?
    let w: String?
    let ph: String?
    let fv: HealthRating?
}

// MARK: - The model the views use

/// Connecticut tags, from names and the hand-checked research (never from reviews).
struct PlaceTags: OptionSet, Hashable {
    let rawValue: Int
    static let apizza = PlaceTags(rawValue: 1)
    static let lobster = PlaceTags(rawValue: 2)
    static let clams = PlaceTags(rawValue: 4)
    static let steamed = PlaceTags(rawValue: 8)
    static let hotDog = PlaceTags(rawValue: 16)
    static let dairy = PlaceTags(rawValue: 32)
    static let diner = PlaceTags(rawValue: 64)
    static let polish = PlaceTags(rawValue: 128)
}

/// What the hand-checked research says a place is (data/research/README.md `kinds`).
struct Kinds: OptionSet, Hashable {
    let rawValue: Int
    static let apizza = Kinds(rawValue: 1)
    static let lobsterRoll = Kinds(rawValue: 2)
    static let clamShack = Kinds(rawValue: 4)
    static let steamedCheeseburger = Kinds(rawValue: 8)
    static let burgerIcon = Kinds(rawValue: 16)
    static let hotDogIcon = Kinds(rawValue: 32)
    static let diner = Kinds(rawValue: 64)
    static let dairyBar = Kinds(rawValue: 128)
    static let polish = Kinds(rawValue: 256)
    static let oldest = Kinds(rawValue: 512)
    static let grinder = Kinds(rawValue: 1024)

    static let labels: [(Kinds, String)] = [(.apizza, "Apizza"), (.lobsterRoll, "Lobster roll"), (.clamShack, "Clam shack"),
                                            (.steamedCheeseburger, "Steamed cheeseburger"), (.burgerIcon, "Burger icon"), (.hotDogIcon, "Hot dogs"),
                                            (.diner, "Diner"), (.dairyBar, "Dairy bar"), (.polish, "Polish"), (.oldest, "Historic"), (.grinder, "Grinders")]
    var names: [String] { Kinds.labels.filter { contains($0.0) }.map(\.1) }
}

/// How a place got on the list. The share that matched a licensed business comes from calibration.json.
enum Tier: Int, Comparable {
    case listing = 0        // one map listing
    case confirmed = 1      // a high-confidence Meta listing, or a hand-checked place
    case licensed = 2       // on the state liquor-permit list or Hartford's food-license list

    static func < (a: Tier, b: Tier) -> Bool { a.rawValue < b.rawValue }

    var label: String {
        switch self {
        case .licensed: "Licensed"
        case .confirmed: "Confirmed listing"
        case .listing: "Listing only"
        }
    }
}

enum Jurisdiction: Int {
    case none = 0, dcp = 1, hartford = 2
    var listName: String {
        switch self {
        case .dcp: "Connecticut Department of Consumer Protection liquor permits"
        case .hartford: "City of Hartford food-establishment licenses"
        case .none: ""
        }
    }
}

struct Place: Identifiable, Hashable {
    let id: String
    let name: String
    let address: String?
    /// one of Connecticut's 169 towns (the municipality)
    let city: String?
    /// the village people call it, when it isn't the town: Mystic, Noank, Storrs, Cos Cob
    let village: String?
    let zip: String?
    let coordinate: CLLocationCoordinate2D?
    let cuisine: String
    let brand: String?
    let chainCount: Int
    let tier: Tier
    let jurisdiction: Jurisdiction
    let licenseKind: String?
    let hartfordClass: String?
    let source: String
    let isVenue: Bool
    let isBar: Bool
    /// Foxwoods or Mohegan Sun: restaurants on tribal land inside a casino
    let host: String?
    let tags: PlaceTags
    /// On our hand-checked list (data/research): confirmed open with a 2025–26 source.
    let handChecked: Bool
    let kinds: Kinds
    let honorFlags: Int
    /// the Icons guide's order (honors and years at the address); only icons have it, and it's never shown as a number
    let iconicPoints: Double?
    /// the classics' "Featured first" order
    let featuredScore: Double?
    let note: String?
    let jamesBeard: String?
    let otherHonors: String?
    let dishes: String?
    let season: String?
    let isSeasonal: Bool
    let branchOf: String?
    let chef: String?
    let founded: Int?
    /// http or https only
    let website: URL?
    /// a US number, "+12035551234"; anything else could ring abroad, so it isn't offered
    let phone: String?
    let healthRating: HealthRating?
    /// normalized text for search: name, town, village, zip, cuisine, brand, dishes, then the address with street words abbreviated
    let searchText: String
    let nameText: String
    /// position in the A to Z order of every place, worked out once at load so sorting never compares names
    var nameRank = 0

    static func == (a: Place, b: Place) -> Bool { a.id == b.id }
    func hash(into h: inout Hasher) { h.combine(id) }

    var isHonored: Bool { handChecked }
    var isChain: Bool { chainCount >= 5 }
    /// a hand-checked place that isn't someone's branch: Frank Pepe on Wooster St, though Pepe's has eight
    var isHandCheckedOriginal: Bool { handChecked && branchOf == nil }
    var jamesBeardLabel: String? {
        if honorFlags & 1 != 0 { return "America's Classic" }
        if honorFlags & 2 != 0 { return "James Beard winner" }
        if honorFlags & 4 != 0 { return "James Beard nominee" }
        if honorFlags & 8 != 0 { return "James Beard semifinalist" }
        return nil
    }
    /// "Mystic (Stonington)" or "New Haven"
    var placeName: String? {
        guard let city else { return village }
        return village.map { "\($0) (\(city))" } ?? city
    }
    var townLine: String { [placeName, cuisine].compactMap { $0 }.joined(separator: " · ") }
    var fullAddress: String {
        [address, [village ?? city, zip].compactMap { $0 }.joined(separator: " ")].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: ", ")
    }
    var location: CLLocation? { coordinate.map { CLLocation(latitude: $0.latitude, longitude: $0.longitude) } }
    /// "(203) 555-1234"
    var phoneText: String? {
        phone.map { p in "(\(p.dropFirst(2).prefix(3))) \(p.dropFirst(5).prefix(3))-\(p.dropFirst(8))" }
    }

    static func usPhone(_ s: String?) -> String? {
        guard let s, s.range(of: #"^\+1[2-9][0-9]{9}$"#, options: .regularExpression) != nil else { return nil }
        return s
    }

    /// A website link only when it's a web address: no other scheme, and nothing scheme-less that could resolve oddly.
    static func webURL(_ s: String?) -> URL? {
        guard let s, let u = URL(string: s), ["http", "https"].contains(u.scheme?.lowercased() ?? ""), !(u.host ?? "").isEmpty else { return nil }
        return u
    }

    init(_ r: PlaceRecord, file: DataFile) {
        let city = r.c.flatMap { $0 < file.cities.count ? file.cities[$0] : nil }
        let village = r.vi.flatMap { $0 < file.villages.count ? file.villages[$0] : nil }
        let cuisine = r.cu < file.cuisines.count ? file.cuisines[r.cu] : "American & Other"
        let brand = r.b.flatMap { $0 < file.brands.count ? file.brands[$0] : nil }
        let host = r.host.flatMap { $0 < file.hosts.count ? file.hosts[$0] : nil }
        id = r.id
        name = r.n
        address = r.a
        self.city = city
        self.village = village
        zip = r.z
        if let la = r.la, let lo = r.lo { coordinate = CLLocationCoordinate2D(latitude: la, longitude: lo) } else { coordinate = nil }
        self.cuisine = cuisine
        self.brand = brand
        chainCount = r.ch ?? 1
        tier = Tier(rawValue: r.t) ?? .listing
        jurisdiction = Jurisdiction(rawValue: r.j ?? 0) ?? .none
        licenseKind = r.lk
        hartfordClass = r.hcl
        source = r.s < file.sources.count ? file.sources[r.s] : "meta"
        isVenue = r.v == 1
        isBar = r.bar == 1
        self.host = host
        tags = PlaceTags(rawValue: r.g ?? 0)
        handChecked = r.hc == 1
        kinds = Kinds(rawValue: r.k ?? 0)
        honorFlags = r.h ?? 0
        iconicPoints = r.ip
        featuredScore = r.fs ?? r.ip
        note = r.note
        jamesBeard = r.jbf
        otherHonors = r.hon
        dishes = r.dish
        season = r.sea
        isSeasonal = r.seas == 1
        branchOf = r.br
        chef = r.chef
        founded = r.f
        website = Self.webURL(r.w)
        phone = Self.usPhone(r.ph)
        healthRating = r.fv
        // the dishes a place is known for are searchable too: "white clam pie", "hot buttered"
        searchText = " " + Search.normalize([r.n, city, village, r.z, cuisine, brand, host, r.dish].compactMap { $0 }.joined(separator: " ")) + " "
            + Search.normalizeAddress(r.a ?? "") + " "
        nameText = " " + Search.normalize([r.n, brand].compactMap { $0 }.joined(separator: " ")) + " "
    }
}
