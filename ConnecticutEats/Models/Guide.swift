import Foundation
import CoreLocation

/// The lists the app is built around. Each is a filter plus an order; none uses ratings (the app only publishes data it may).
enum Guide: String, CaseIterable, Identifiable, Hashable {
    case apizza, lobster, burgers, diners, dairy, polish, icons, oldest, nearMe, all

    var id: String { rawValue }

    var title: String {
        switch self {
        case .apizza: "New Haven Apizza"
        case .lobster: "Lobster Rolls & Clam Shacks"
        case .burgers: "Burger & Hot Dog Icons"
        case .diners: "Diners"
        case .dairy: "Dairy Bars"
        case .polish: "Little Poland"
        case .icons: "Connecticut Icons"
        case .oldest: "Oldest Places"
        case .nearMe: "Near Me"
        case .all: "All Restaurants"
        }
    }

    var subtitle: String {
        switch self {
        case .apizza: "Coal- and oven-fired pies, white clam to tomato, hand-checked"
        case .lobster: "Hot buttered rolls and fried clams, many open in season"
        case .burgers: "Louis' Lunch, Meriden steamed cheeseburgers and the stands"
        case .diners: "Long-running diners, hand-checked open"
        case .dairy: "Farm creameries and ice cream stands"
        case .polish: "Pierogi, kielbasa and bakeries, from New Britain out"
        case .icons: "James Beard honorees and long-running institutions"
        case .oldest: "Years at the same address, oldest first"
        case .nearMe: "Everything around you, closest first"
        case .all: "Restaurants, cafés, bars and bakeries statewide"
        }
    }

    var systemImage: String {
        switch self {
        case .apizza: "flame"
        case .lobster: "fish"
        case .burgers: "takeoutbag.and.cup.and.straw"
        case .diners: "cup.and.saucer"
        case .dairy: "birthday.cake"
        case .polish: "basket"
        case .icons: "star.circle"
        case .oldest: "clock.arrow.circlepath"
        case .nearMe: "location"
        case .all: "fork.knife"
        }
    }

    /// The Connecticut classics: hand-checked lists, highlighted on Home.
    var isClassic: Bool { [.apizza, .lobster, .burgers, .diners, .dairy, .polish].contains(self) }

    /// Guides whose order is a ranking worth numbering.
    var isRanked: Bool { [.icons, .oldest].contains(self) }

    var sortOptions: [SortOrder] {
        switch self {
        case .apizza, .lobster, .burgers, .diners, .dairy, .polish: [.featured, .nearest, .oldest, .name]
        case .icons: [.iconic, .oldest, .nearest]
        case .oldest: [.oldest]
        case .nearMe: [.nearest]
        case .all: [.name, .nearest]
        }
    }

    var defaultSort: SortOrder { sortOptions[0] }

    func includes(_ p: Place) -> Bool {
        switch self {
        // the classics promise "hand-checked", so only places our research confirmed open; a listing merely named "… Diner" isn't enough
        case .apizza: p.handChecked && p.kinds.contains(.apizza)
        case .lobster: p.handChecked && !p.kinds.isDisjoint(with: [.lobsterRoll, .clamShack])
        case .burgers: p.handChecked && !p.kinds.isDisjoint(with: [.burgerIcon, .steamedCheeseburger, .hotDogIcon])
        case .diners: p.handChecked && p.kinds.contains(.diner)
        case .dairy: p.handChecked && p.kinds.contains(.dairyBar)
        case .polish: p.handChecked && p.kinds.contains(.polish)
        case .icons: p.iconicPoints != nil
        case .oldest: p.founded != nil
        case .nearMe, .all: true
        }
    }
}

enum SortOrder: String, CaseIterable, Identifiable {
    case featured, nearest, oldest, name, iconic
    var id: String { rawValue }
    var label: String {
        switch self {
        case .featured: "Featured first"
        case .nearest: "Nearest"
        case .oldest: "Oldest first"
        case .name: "A to Z"
        case .iconic: "Most iconic"
        }
    }
}

/// Filters shared by every list. Search text lives with each list.
struct Filters: Equatable, Codable {
    var town: String?
    var cuisine: String?
    var hideChains = false
    var confirmedOnly = false
    var includeNonRestaurants = false

    var activeCount: Int {
        [town != nil, cuisine != nil, hideChains, confirmedOnly, includeNonRestaurants].filter { $0 }.count
    }

    func allows(_ p: Place) -> Bool {
        if !includeNonRestaurants && p.isVenue { return false }
        if let town, p.city != town { return false }
        if let cuisine, p.cuisine != cuisine { return false }
        if hideChains && p.isChain { return false }
        if confirmedOnly && p.tier == .listing { return false }
        return true
    }
}

enum Ranking {
    static func sort(_ places: [Place], by order: SortOrder, from here: CLLocation?) -> [Place] {
        func name(_ a: Place, _ b: Place) -> Bool { a.name.localizedCaseInsensitiveCompare(b.name) == .orderedAscending }
        func dist(_ p: Place) -> Double { (here != nil ? p.location?.distance(from: here!) : nil) ?? .greatestFiniteMagnitude }
        switch order {
        case .nearest where here != nil:
            return places.sorted { dist($0) != dist($1) ? dist($0) < dist($1) : name($0, $1) }
        case .featured, .nearest:
            // honored places first, then the verified year at this address, then name
            return places.sorted {
                let a = $0.iconicPoints ?? -1, b = $1.iconicPoints ?? -1
                if a != b { return a > b }
                let fa = $0.founded ?? 9999, fb = $1.founded ?? 9999
                return fa != fb ? fa < fb : name($0, $1)
            }
        case .oldest:
            return places.sorted { ($0.founded ?? 9999, $0.name) < ($1.founded ?? 9999, $1.name) }
        case .name:
            return places.sorted(by: name)
        case .iconic:
            return places.sorted { ($0.iconicPoints ?? -1) != ($1.iconicPoints ?? -1) ? ($0.iconicPoints ?? -1) > ($1.iconicPoints ?? -1) : name($0, $1) }
        }
    }
}
