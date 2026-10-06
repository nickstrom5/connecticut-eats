import SwiftUI

struct AboutView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Text("CONNECTICUT EATS").displayFont(30).foregroundStyle(Theme.navy)
                    Text("A free guide to \(model.restaurantCount.formatted()) Connecticut restaurants, with hand-checked lists of New Haven apizza, lobster rolls and clam shacks, burger and hot dog icons, diners and dairy bars. No account, no ads, no tracking.")
                        .font(.subheadline).foregroundStyle(Theme.ink2)
                    Text("Connecticut Eats (\u{201C}CT Eats\u{201D}) is an independent app by Nicholas Soderstrom. It is not affiliated with, endorsed by or operated by the State of Connecticut, its Department of Consumer Protection or Department of Public Health, the City of Hartford, the Farmington Valley Health District, the Mashantucket Pequot or Mohegan tribes or their casinos, the University of Connecticut, the James Beard Foundation, Apple, or any restaurant, team or chain.")
                        .font(.footnote).foregroundStyle(Theme.muted)
                }
                .padding(.vertical, 4)
            }
            Section("How the lists are built") {
                Text("Apizza, lobster rolls and clam shacks, burger and hot dog icons, diners, dairy bars, Little Poland and the icons are hand-checked: each was checked in October 2026 against a 2025 or 2026 source (the place's own website or menu, local news, or a tourism listing), with the address checked.")
                Text("The rest come from Overture Maps' open place data, the Connecticut Department of Consumer Protection's list of liquor permits, and the City of Hartford's food-establishment licenses. Map listings are kept only when they proved reliable: checked against Hartford's food licenses, high-confidence listings matched a licensed food business \(rate("Meta, confidence 0.95+")) of the time. Website links are checked, and any that no longer belong to the place are left out.")
                Text("Connecticut has no statewide inspection results or official grade. In the 10 towns of the Farmington Valley Health District, a place's official A, B, C or U rating is shown with its date.")
                Text("Ratings, reviews, hours and photos are Apple Maps' own, shown live in Apple's place card. This app doesn't store or rank by them.")
            }
            .font(.subheadline).foregroundStyle(Theme.ink2)
            Section("Sources") {
                source("Overture Maps Foundation", "Restaurant listings and websites come from Overture Maps Foundation places data (overturemaps.org), release 2026-09-23.1, filtered and reformatted for this app.\n• Data from Meta, Microsoft, DAC and BrightQuery. Available under CDLA Permissive 2.0.\n• Data from Foursquare. Copyright 2024 Foursquare Labs, Inc. All rights reserved. Available under Apache 2.0. Foursquare data was transformed to the Overture schema; this app further filtered and reformatted it. See the NOTICE below.\n• Data from AllThePlaces. Available under CC0 1.0.", "https://overturemaps.org")
                source("Connecticut Department of Consumer Protection", "State Licenses and Credentials (data.ct.gov), public domain: on-premise liquor permits, used for the business's trade name, address and permit type only. The State of Connecticut makes no warranty as to the data's accuracy, completeness or timeliness and does not endorse this app.", "https://data.ct.gov/Business/State-Licenses-and-Credentials/ngch-56tr")
                source("City of Hartford", "Food Establishments Licenses Current (data.hartford.gov), modified for use in this app. Data courtesy of the City of Hartford, which makes no warranty as to its accuracy, completeness or timeliness and does not endorse this app.", "https://data.hartford.gov")
                source("Farmington Valley Health District", "Food service ratings by town (fvhd.org), shown as published with their dates. Ratings are a snapshot in time; the district does not endorse this app.", "https://fvhd.org/environmental-health/food/food-ratings/")
                source("Town outlines", "U.S. Census Bureau cartographic boundary files, 2025 (public domain), used to place each restaurant in one of Connecticut's 169 towns.", nil)
                source("Honors", "James Beard Foundation awards, finalists, semifinalists and America's Classics are reported as facts and checked by hand against public announcements. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. There is no MICHELIN Guide for Connecticut. Other names belong to their owners.", "https://www.jamesbeard.org/awards/search-past-awards")
                source("Maps", "Maps, place cards and directions by Apple Maps.", nil)
            }
            Section("Licenses") {
                NavigationLink("Community Data License Agreement – Permissive 2.0") { LicenseText(file: "CDLA-Permissive-2.0", title: "CDLA Permissive 2.0") }
                NavigationLink("Apache License 2.0") { LicenseText(file: "Apache-2.0", title: "Apache License 2.0") }
                NavigationLink("Foursquare OS Places NOTICE") { LicenseText(file: "Foursquare-NOTICE", title: "Foursquare NOTICE") }
            }
            Section("Privacy") {
                Text("The app collects nothing. Your location, if you allow it, only sorts lists by distance and shows where you are on the map, on this device. Saved places stay on this device.")
                    .font(.subheadline).foregroundStyle(Theme.ink2)
                Link("Privacy policy", destination: Links.privacy)
                Link("Terms of use", destination: Links.terms)
            }
            Section("Help") {
                Link("Report a missing or closed place", destination: Links.correctionEmail)
                Link("Email \(Links.supportEmail)", destination: URL(string: "mailto:\(Links.supportEmail)")!)
                Link("Website", destination: Links.site)
                Text("Data as of \(model.generated). Places open and close; check before you go. Version \(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0")")
                    .font(.footnote).foregroundStyle(Theme.muted)
            }
        }
        .navigationTitle("About")
        .tint(Theme.navy)
    }

    private func rate(_ group: String) -> String {
        guard let g = model.calibration["hartford"]?[group] else { return "most" }
        return "\(Int((g.matched * 100).rounded()))%"
    }

    @ViewBuilder
    private func source(_ name: String, _ detail: String, _ url: String?) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            if let url, let u = URL(string: url) { Link(name, destination: u).font(.subheadline.weight(.semibold)) }
            else { Text(name).font(.subheadline.weight(.semibold)) }
            Text(detail).font(.caption).foregroundStyle(Theme.muted)
        }
    }
}

/// A bundled license text (Resources/Licenses), reflowed rather than shown as raw 80-column lines.
struct LicenseText: View {
    let file: String
    let title: String

    var body: some View {
        ScrollView {
            Text(text).font(.footnote).foregroundStyle(Theme.ink).textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading).padding()
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var text: String {
        guard let url = Bundle.main.url(forResource: file, withExtension: "txt"),
              let raw = try? String(contentsOf: url, encoding: .utf8) else { return "License text missing." }
        // join hard-wrapped lines into paragraphs; keep blank lines and list items as breaks
        var out: [String] = []
        for para in raw.components(separatedBy: "\n\n") {
            let lines = para.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespaces) }
            var joined = ""
            for l in lines where !l.isEmpty {
                let startsItem = l.hasPrefix("–") || l.hasPrefix("-") || l.range(of: #"^\(?[a-z0-9]{1,3}[.)]\s"#, options: .regularExpression) != nil
                joined += joined.isEmpty ? l : (startsItem ? "\n" + l : " " + l)
            }
            if !joined.isEmpty { out.append(joined) }
        }
        return out.joined(separator: "\n\n")
    }
}
