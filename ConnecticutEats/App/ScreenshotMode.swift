import Foundation
import CoreLocation
import MapKit
import UIKit

/// `-screenshot <name>` opens one screen with fixed state for App Store screenshots (scripts/capture-screenshots.sh).
/// Names: home, apizza, lobster, burgers, detail, map, icons, saved, about.
enum ScreenshotMode {
    /// Debug builds only: an App Store build ignores the launch argument, so no one can reach seeded screens or fake locations.
    static var name: String? {
        #if DEBUG
        let args = ProcessInfo.processInfo.arguments
        guard let i = args.firstIndex(of: "-screenshot"), i + 1 < args.count else { return nil }
        return args[i + 1]
        #else
        return nil
        #endif
    }
    static var isActive: Bool { name != nil }

    /// The map shot opens on New Haven's apizza at neighborhood zoom, so the pins show one by one rather than as statewide clusters.
    static var mapRegion: MKCoordinateRegion? {
        name == "map" ? MKCoordinateRegion(center: CLLocationCoordinate2D(latitude: 41.293, longitude: -72.927),
                                           span: MKCoordinateSpan(latitudeDelta: 0.07, longitudeDelta: 0.04)) : nil
    }

    @MainActor
    static func apply(to model: AppModel) {
        guard let name, model.isLoaded else { return }
        model.filters = Filters()
        // the New Haven Green, so "nearest" lists have distances without a permission prompt
        model.screenshotLocation = CLLocation(latitude: 41.3083, longitude: -72.9279)
        // the first hand-checked place with this name (a branch never stands in for the original)
        let named = { (p: Place, n: String) in p.name.lowercased().hasPrefix(n.lowercased()) }
        let pick = { (n: String) in model.places.first { named($0, n) && $0.handChecked && $0.branchOf == nil } ?? model.places.first { named($0, n) } }
        for n in ["Frank Pepe Pizzeria Napoletana", "Louis' Lunch", "Abbott's Lobster in the Rough", "Shady Glen"] {
            if let p = pick(n), !model.isSaved(p) { model.toggleSaved(p) }
        }
        let open = { (g: Guide) in model.tab = .guides; model.selectedGuide = g; model.guidesPath = [.guide(g)] }
        switch name {
        case "apizza": open(.apizza)
        case "lobster": open(.lobster)
        case "burgers": open(.burgers)
        case "icons": open(.icons)
        case "detail":
            open(.apizza)
            if let p = pick("Frank Pepe Pizzeria Napoletana") ?? model.places.first { model.selectedPlace = p; model.guidesPath.append(.place(p)) }
        case "map": model.tab = .map
        case "saved": model.tab = .saved
        case "about": model.tab = .about
        default: model.tab = .guides; model.selectedGuide = nil
        }
        // iPad shows the place column next to every list, so give each shot a place instead of "Pick a place".
        guard UIDevice.current.userInterfaceIdiom == .pad, model.selectedPlace == nil else { return }
        let place: Place? = switch name {
        case "lobster": pick("Abbott's Lobster in the Rough")
        case "burgers": pick("Louis' Lunch")
        case "icons": pick("Shady Glen")
        case "saved": pick("Louis' Lunch")
        case "about": nil
        case "map": pick("Modern Apizza")
        default: pick("Frank Pepe Pizzeria Napoletana")
        }
        model.selectedPlace = place
    }
}
