import SwiftUI
import MapKit

struct PlaceDetailView: View {
    @Environment(AppModel.self) private var model
    @Environment(LocationService.self) private var location
    let place: Place

    @Environment(\.dynamicTypeSize) private var typeSize
    @State private var mapItem: MKMapItem?
    @State private var lookingUp = false
    @State private var notOnAppleMaps = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                header
                actions
                if let c = place.coordinate { mapSnippet(c) }
                if place.handChecked { checked }
                if place.jamesBeard != nil || place.otherHonors != nil { honors }
                if let r = place.healthRating { rating(r) }
                if let host = place.host { hostVenue(host) }
                listing
            }
            .padding(16)
        }
        .background(Theme.surface)
        .navigationTitle(place.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button { model.toggleSaved(place) } label: {
                    Label(model.isSaved(place) ? "Saved" : "Save", systemImage: model.isSaved(place) ? "heart.fill" : "heart")
                }
                ShareLink(item: shareText) { Label("Share", systemImage: "square.and.arrow.up") }
            }
        }
        .mapItemDetailSheet(item: $mapItem)
        .alert("Not on Apple Maps", isPresented: $notOnAppleMaps) {
            Button("Open Apple Maps anyway") { AppleMaps.openInMaps(place) }
            Button("OK", role: .cancel) {}
        } message: {
            Text("Apple Maps doesn't have a listing for \(place.name) at this spot, so there are no ratings or hours to show here.")
        }
    }

    // MARK: sections

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text((place.village.map { "\($0) · \(place.city ?? "")" } ?? place.city ?? "Connecticut").uppercased())
                .font(.caption.weight(.bold)).tracking(1.2).foregroundStyle(Theme.navy2)
            Text(place.name.uppercased())
                .displayFont(38).foregroundStyle(Theme.navy)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            Text([place.fullAddress, place.cuisine].filter { !$0.isEmpty }.joined(separator: " · "))
                .font(.subheadline).foregroundStyle(Theme.ink2)
                .textSelection(.enabled)
            if let here = model.screenshotLocation ?? location.location, let l = place.location {
                Text("\(here.milesText(to: l)) away").font(.subheadline).foregroundStyle(Theme.muted)
            }
            PlaceChips(place: place)
        }
    }

    private var actions: some View {
        VStack(spacing: 10) {
            Button {
                lookingUp = true
                Task {
                    let item = await AppleMaps.findItem(for: place)
                    lookingUp = false
                    if let item { mapItem = item } else { notOnAppleMaps = true }
                }
            } label: {
                // at the largest text sizes the caption goes under the title, so "Ratings" isn't split across lines
                let layout = typeSize.isAccessibilitySize ? AnyLayout(VStackLayout(alignment: .leading, spacing: 4)) : AnyLayout(HStackLayout())
                layout {
                    HStack {
                        if lookingUp { ProgressView().tint(.white) } else { Image(systemName: "star.bubble") }
                        Text("Ratings, hours & photos").fontWeight(.semibold)
                    }
                    if !typeSize.isAccessibilitySize { Spacer() }
                    Text("Apple Maps").font(.caption)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(14)
                .foregroundStyle(.white)
                .background(RoundedRectangle(cornerRadius: 12).fill(Theme.navy))
            }
            .disabled(place.coordinate == nil || lookingUp)
            .accessibilityHint("Opens the Apple Maps place card with current ratings and hours")

            HStack(spacing: 10) {
                actionButton("Directions", "arrow.triangle.turn.up.right.diamond") { AppleMaps.openInMaps(place, directions: true) }
                if let phone = place.phone, let url = URL(string: "tel:\(phone.filter { $0.isNumber || $0 == "+" })") {
                    actionButton("Call", "phone") { UIApplication.shared.open(url) }
                }
                if let web = place.website {
                    actionButton("Website", "safari") { UIApplication.shared.open(web) }
                }
            }
        }
    }

    private func actionButton(_ title: String, _ icon: String, _ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon).font(.title3)
                Text(title).font(.caption.weight(.semibold))
            }
            .frame(maxWidth: .infinity, minHeight: 56)
            .foregroundStyle(Theme.navy)
            .background(RoundedRectangle(cornerRadius: 12).strokeBorder(Theme.rule2))
        }
    }

    private func mapSnippet(_ c: CLLocationCoordinate2D) -> some View {
        Map(initialPosition: .region(MKCoordinateRegion(center: c, latitudinalMeters: 900, longitudinalMeters: 900)), interactionModes: []) {
            Marker(place.name, systemImage: MarkerGlyph.symbol(for: place), coordinate: c).tint(place.handChecked ? Theme.tomato : Theme.navy)
        }
        .frame(height: 170)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .onTapGesture { AppleMaps.openInMaps(place) }
        .accessibilityLabel("Map of \(place.name). Opens Apple Maps.")
    }

    private var checked: some View {
        section("Hand-checked") {
            VStack(alignment: .leading, spacing: 8) {
                if let note = place.note { Text(note).font(.subheadline).foregroundStyle(Theme.ink2) }
                if !place.kinds.names.isEmpty { fact("On our lists", place.kinds.names.joined(separator: ", ")) }
                if let d = place.dishes { fact("Known for", d) }
                if let s = place.season { fact("Season", s) } else if place.isSeasonal { fact("Season", "Seasonal; check before you go.") }
                if let f = place.founded { fact("At this address since", "\(f)") }
                if let b = place.branchOf { fact("A branch of", b) }
                Text("Checked open in October 2026 against a 2025 or 2026 source: the place's own site or menu, local news, or a tourism listing. Hours and menus change, so check before you go.")
                    .font(.caption).foregroundStyle(Theme.ink2)
            }
        }
    }

    private var honors: some View {
        section("Honors") {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(lines(place.jamesBeard, prefix: "James Beard: ") + lines(place.otherHonors, prefix: ""), id: \.self) { l in
                    Label(l, systemImage: "rosette").font(.subheadline).foregroundStyle(Theme.ink)
                }
                if let chef = place.chef { fact("Chef", chef) }
                Text("Honors are facts, not ratings. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation.")
                    .font(.caption).foregroundStyle(Theme.muted)
            }
        }
    }

    private func rating(_ r: HealthRating) -> some View {
        section("Health rating · official") {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 12) {
                    RatingBadge(rating: r.r, size: 46)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(r.meaning).font(.headline).foregroundStyle(Theme.ink)
                        if let d = r.d { Text("Rated \(Self.date(d))").font(.subheadline).foregroundStyle(Theme.ink2) }
                    }
                }
                Text("The Farmington Valley Health District rates restaurants A (Excellent), B (Good), C (Fair) or U (Unsatisfactory) at each routine inspection, and each place must post its rating. Only these 10 towns publish a current rating; the rest of Connecticut's health departments don't post results.")
                    .font(.caption).foregroundStyle(Theme.muted)
            }
        }
    }

    private func hostVenue(_ host: String) -> some View {
        section("Host venue") {
            Text(host == "Foxwoods"
                 ? "Inside Foxwoods Resort Casino, on Mashantucket Pequot tribal land, where Mashantucket Pequot Tribal Health Services inspects restaurants."
                 : "Inside Mohegan Sun, on Mohegan tribal land, where the Mohegan Tribal Health Department inspects restaurants.")
                .font(.subheadline).foregroundStyle(Theme.ink2)
        }
    }

    private var listing: some View {
        section("How we know it's here") {
            VStack(alignment: .leading, spacing: 8) {
                kv("Listed as", place.handChecked && place.tier != .licensed ? "Hand-checked" : place.tier.label)
                if place.tier == .licensed {
                    kv("License list", place.jurisdiction == .hartford ? "City of Hartford food license" : "Connecticut liquor permit")
                    if let k = place.licenseKind { kv("Permit", k) }
                    if let c = place.hartfordClass { kv("Hartford license", c) }
                }
                if place.chainCount >= 2 { kv("Locations in Connecticut", place.chainCount.formatted()) }
                Text(listingNote).font(.caption).foregroundStyle(Theme.muted)
            }
        }
    }

    private var listingNote: String {
        let checked = place.handChecked
        if place.source == "research" {
            return "On our hand-checked list (checked in October 2026 against a 2025 or 2026 source). The open map data didn't list it as a place to eat, so it's placed at its street address."
        }
        switch place.tier {
        case .licensed:
            return place.source == "official"
                ? "From the \(place.jurisdiction.listName). The open map data didn't have it, so it's placed at its street address."
                : "Matched to an active entry in the \(place.jurisdiction.listName)."
        case .confirmed where checked, .listing where checked:
            return "On our hand-checked list: checked open in October 2026 against a 2025 or 2026 source (its own site or menu, local news, or a tourism listing). It's in Overture's open map data too."
        case .confirmed, .listing:
            let rate = model.matchRate(for: place)
            let base = place.tier == .confirmed
                ? "A high-confidence listing in Overture's open map data."
                : "A single listing in Overture's open map data, so it may be closed or misfiled."
            let measured = rate.map { " Checked against Hartford's food licenses, listings like this matched a licensed food business \($0) of the time." } ?? ""
            return base + measured + (checked ? " It's also on our hand-checked list, checked in October 2026 against a 2025 or 2026 source." : "")
        }
    }

    // MARK: helpers

    private var shareText: String {
        [place.name, place.fullAddress, "via Connecticut Eats", Links.site.absoluteString].filter { !$0.isEmpty }.joined(separator: "\n")
    }

    static func date(_ iso: String) -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX")
        guard let d = f.date(from: iso) else { return iso }
        return d.formatted(date: .abbreviated, time: .omitted)
    }

    private func lines(_ s: String?, prefix: String) -> [String] {
        (s ?? "").components(separatedBy: "; ").filter { !$0.isEmpty }.map { prefix + $0 }
    }

    private func section<Content: View>(_ title: String, @ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title.uppercased()).font(.caption.weight(.bold)).tracking(1).foregroundStyle(Theme.ink2)
            Divider()
            content()
        }
    }

    private func fact(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
            Text(value).font(.subheadline).foregroundStyle(Theme.ink2)
        }
    }

    @ViewBuilder
    private func kv(_ k: String, _ v: String?) -> some View {
        if let v {
            HStack(alignment: .firstTextBaseline) {
                Text(k).font(.subheadline).foregroundStyle(Theme.ink2)
                Spacer(minLength: 12)
                Text(v).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).multilineTextAlignment(.trailing)
            }
        }
    }
}

/// The glyph a place gets on the maps: apizza, seafood, burgers and hot dogs, diners, dairy bars, everything else.
enum MarkerGlyph {
    static func symbol(for p: Place) -> String {
        if p.kinds.contains(.apizza) || p.tags.contains(.apizza) { return "flame.fill" }
        if !p.kinds.isDisjoint(with: [.lobsterRoll, .clamShack]) { return "fish.fill" }
        if !p.kinds.isDisjoint(with: [.burgerIcon, .steamedCheeseburger, .hotDogIcon]) { return "takeoutbag.and.cup.and.straw.fill" }
        if p.kinds.contains(.diner) { return "cup.and.saucer.fill" }
        if p.kinds.contains(.dairyBar) { return "birthday.cake.fill" }
        return "fork.knife"
    }
}

extension String {
    var nonEmpty: String? { isEmpty ? nil : self }
}
