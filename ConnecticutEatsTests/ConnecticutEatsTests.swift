import XCTest
import CoreLocation
@testable import ConnecticutEats

@MainActor
final class ConnecticutEatsTests: XCTestCase {

    /// A tiny data file with the same shape as Resources/places.json.
    nonisolated static let sampleJSON = """
        {"v":1,"generated":"2026-10-05","data_version":"abc123def456","research_checked":"October 2026","overture":"2026-09-23.1",
         "aliases":{"old-b":"b","older-b":"old-b","loop1":"loop2","loop2":"loop1"},
         "cities":["New Haven","Groton","Stonington","Meriden","Hartford","Canton","New Britain","Manchester","Preston","Washington"],
         "villages":["Mystic","Noank","New Preston"],
         "cuisines":["Pizza","Seafood","Burgers","Bar & Pub","American & Other"],"brands":["Dunkin'"],"hosts":["Foxwoods","Mohegan Sun"],
         "tags":["apizza","lobster","clams","steamed","hotdog","dairy","diner","polish"],"sources":["official","meta","AllThePlaces","DAC","research"],
         "count":12,"count_restaurants":11,
         "calibration":{"hartford":{"Meta, confidence 0.95+":{"n":258,"matched":0.674},"Meta, 0.90-0.95":{"n":83,"matched":0.398}}},
         "fvhd_fetched":"2026-10-05","fvhd_pages":{"Canton":"https://fvhd.org/environmental-health/food/food-ratings/canton/"},
         "places":[
          {"id":"a","n":"Frank Pepe Pizzeria Napoletana","c":0,"cu":0,"t":2,"s":0,"j":1,"lk":"Restaurant Liquor","hc":1,"k":1,"g":1,"h":1,"ip":90,"fs":80,"ch":8,"a":"157 Wooster St","z":"06511","la":41.3029,"lo":-72.9171,"f":1925,"dish":"white clam pie","jbf":"America's Classics 1999","ph":"+12038655762","w":"https://www.pepespizzeria.com/"},
          {"id":"b","n":"Modern Apizza","c":0,"cu":0,"t":1,"s":1,"hc":1,"k":1,"g":1,"ip":70,"fs":85,"a":"874 State St","la":41.3175,"lo":-72.9067,"f":1934,"ph":"+2037765306","w":"javascript:alert(1)"},
          {"id":"c","n":"Abbott's Lobster in the Rough","c":1,"vi":1,"cu":1,"t":1,"s":1,"hc":1,"k":6,"g":6,"seas":1,"sea":"May to October","ip":60,"a":"117 Pearl St","la":41.3196,"lo":-71.9897,"dish":"hot buttered lobster roll","h":4,"w":"abbottslobster.com"},
          {"id":"d","n":"Ted's Restaurant","c":3,"cu":2,"t":1,"s":1,"hc":1,"k":24,"g":8,"ip":65,"a":"1046 Broad St","la":41.5530,"lo":-72.8018,"f":1959,"ph":"(203) 237-6660"},
          {"id":"e","n":"Dunkin'","c":4,"cu":4,"t":1,"s":2,"b":0,"ch":400,"la":41.7637,"lo":-72.6851},
          {"id":"f","n":"Mystic Diner","c":2,"vi":0,"cu":4,"t":0,"s":1,"g":64,"a":"10 Main St","la":41.354,"lo":-71.966},
          {"id":"g","n":"Cumberland Farms","c":4,"cu":4,"t":1,"s":1,"v":1,"la":41.77,"lo":-72.68},
          {"id":"h","n":"Bobby's Burgers","c":4,"cu":2,"t":1,"s":1,"host":1,"la":41.49,"lo":-72.09},
          {"id":"i","n":"ABC Pizza & Restaurant","c":5,"cu":0,"t":1,"s":1,"a":"9 River St","la":41.82,"lo":-72.92,"fv":{"r":"A","d":"2026-04-29","n":"ABC Pizza"}},
          {"id":"j","n":"Shady Glen","c":7,"cu":4,"t":0,"s":1,"hc":1,"k":128,"a":"840 E Middle Tpke","la":41.78,"lo":-72.49},
          {"id":"k","n":"The Smithy","c":9,"vi":2,"cu":4,"t":1,"s":1,"a":"10 Main St","la":41.676,"lo":-73.35},
          {"id":"l","n":"Preston Pizza","c":8,"cu":0,"t":1,"s":1,"a":"260 CT-32","la":41.52,"lo":-72.08}
         ]}
        """

    private func sampleModel(defaults: UserDefaults? = nil, json: String = sampleJSON) async throws -> AppModel {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("places-test-\(UUID().uuidString).json")
        try json.data(using: .utf8)!.write(to: url)
        let model = AppModel(defaults: defaults ?? UserDefaults(suiteName: "test-\(UUID().uuidString)")!)
        await model.load(from: url)
        XCTAssertTrue(model.isLoaded, model.loadError ?? "")
        return model
    }

    func testDecodesAndHidesNonRestaurantsByDefault() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.places.count, 12)
        let all = m.list(.all, sort: .name, search: "", here: nil)
        XCTAssertFalse(all.contains { $0.name == "Cumberland Farms" }, "gas-station counters are hidden unless asked for")
        m.filters.includeNonRestaurants = true
        XCTAssertTrue(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Cumberland Farms" })
    }

    func testGuidesListOnlyHandCheckedPlaces() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(Set(m.list(.apizza, sort: .name, search: "", here: nil).map(\.id)), ["a", "b"])
        XCTAssertEqual(m.list(.lobster, sort: .name, search: "", here: nil).map(\.id), ["c"], "lobster roll + clam shack both count")
        XCTAssertEqual(m.list(.burgers, sort: .name, search: "", here: nil).map(\.id), ["d"], "a steamed cheeseburger is a burger icon")
        XCTAssertEqual(m.list(.diners, sort: .name, search: "", here: nil), [], "a listing merely named \u{201C}Diner\u{201D} stays out of the checked guide")
        XCTAssertEqual(m.list(.dairy, sort: .name, search: "", here: nil).map(\.id), ["j"])
        XCTAssertEqual(m.list(.all, sort: .name, search: "mystic diner", here: nil).map(\.id), ["f"], "but it's still in the directory")
        XCTAssertEqual(m.list(.oldest, sort: .oldest, search: "", here: nil).map(\.id), ["a", "b", "d"])
        XCTAssertEqual(m.list(.icons, sort: .iconic, search: "", here: nil).first?.id, "a")
        XCTAssertEqual(m.list(.nearMe, sort: .nearest, search: "", here: nil), [], "near me needs a location")
    }

    func testVillagesAndTowns() async throws {
        let m = try await sampleModel()
        func ids(_ q: String) -> Set<String> { Set(m.list(.all, sort: .name, search: q, here: nil).map(\.id)) }
        XCTAssertEqual(ids("noank"), ["c"], "a village narrows to its places")
        XCTAssertEqual(ids("groton"), ["c"], "and its town finds them too")
        XCTAssertEqual(ids("mystic"), ["f"], "Mystic is a village of Stonington (and Groton)")
        XCTAssertEqual(ids("new haven"), ["a", "b"])
        XCTAssertEqual(ids("new preston"), ["k"], "the village New Preston, not the town of Preston")
        XCTAssertEqual(ids("preston"), ["l"])
        // stop words drop out next to a town, village or tag
        XCTAssertEqual(ids("apizza in new haven"), ids("apizza new haven"))
        XCTAssertEqual(ids("apizza in new haven"), ["a", "b"])
        XCTAssertEqual(ids("near mystic"), ids("mystic"))
        XCTAssertEqual(ids("lobster roll in noank"), ["c"])
        XCTAssertEqual(ids("the apizza of new haven"), ["a", "b"])
        // "near me" asks for nothing
        XCTAssertEqual(ids("pizza near me"), ids("pizza"))
        XCTAssertFalse(ids("pizza").isEmpty)
        XCTAssertEqual(ids("near me"), ids(""))
        let abbott = m.place(id: "c")!
        XCTAssertEqual(abbott.placeName, "Noank (Groton)")
        XCTAssertEqual(abbott.fullAddress, "117 Pearl St, Noank")
    }

    func testSearchTagsDishesAndStreets() async throws {
        let m = try await sampleModel()
        func ids(_ q: String) -> [String] { m.list(.all, sort: .name, search: q, here: nil).map(\.id) }
        XCTAssertEqual(Set(ids("apizza")), ["a", "b"])
        XCTAssertEqual(ids("white clam pie"), ["a"], "a dish is searchable")
        XCTAssertEqual(ids("hot buttered"), ["c"])
        XCTAssertEqual(ids("pepe"), ["a"])
        XCTAssertEqual(ids("pepes"), ["a"], "\u{201C}Pepe's\u{201D} finds Frank Pepe")
        XCTAssertEqual(ids("epe"), [], "matches the start of words only")
        XCTAssertEqual(ids("wooster street"), ["a"], "street words match the abbreviated address")
        XCTAssertEqual(ids("state st"), ["b"])
        XCTAssertEqual(ids("steamed cheeseburger"), ["d"])
        XCTAssertEqual(ids("mohegan sun"), ["h"], "the host casino is searchable")
        XCTAssertEqual(ids("route 32"), ["l"], "\u{201C}260 CT-32\u{201D} is a route address")
        XCTAssertEqual(ids("ct 32"), ["l"])
        XCTAssertEqual(ids("rte 32"), ["l"])
        XCTAssertEqual(ids("260 rt 32"), ["l"])
        XCTAssertEqual(Search.normalizeAddress("260 CT-32"), "260 rt 32")
        XCTAssertEqual(Search.normalizeAddress("1 US Route 1"), "1 us rt 1", "only the word right before the number")
        XCTAssertEqual(Search.normalizeAddress("12 Court St"), "12 ct st")
        XCTAssertEqual(ids("🍕"), [], "nothing searchable typed means no results, not everything")
        XCTAssertEqual(ids("!!! ?"), [])
    }

    func testSortsAndDefaults() async throws {
        let m = try await sampleModel()
        let green = CLLocation(latitude: 41.3083, longitude: -72.9279)
        let near = m.list(.nearMe, sort: .nearest, search: "", here: green)
        XCTAssertEqual(near.first?.id, "a", "Pepe's is closest to the New Haven Green")
        XCTAssertEqual(m.list(.apizza, sort: .featured, search: "", here: nil).map(\.id), ["b", "a"], "Featured follows fs, not the icon points")
        XCTAssertEqual(m.list(.icons, sort: .iconic, search: "", here: nil).first?.id, "a", "Most iconic follows ip")
        XCTAssertEqual(m.place(id: "c")!.featuredScore, 60, "no fs: the icon points stand in")
        let az = m.list(.all, sort: .name, search: "", here: nil).map(\.name)
        XCTAssertEqual(az, az.sorted { $0.localizedCaseInsensitiveCompare($1) == .orderedAscending }, "A to Z")
        // a classic opens by distance only for a reader in Connecticut
        XCTAssertEqual(Guide.apizza.defaultSort(inConnecticut: true), .nearest)
        XCTAssertEqual(Guide.apizza.defaultSort(inConnecticut: false), .featured)
        XCTAssertEqual(Guide.all.defaultSort(inConnecticut: true), .name)
        XCTAssertTrue(LocationService.isInConnecticut(green.coordinate))
        XCTAssertFalse(LocationService.isInConnecticut(CLLocationCoordinate2D(latitude: 37.3349, longitude: -122.009)))
    }

    /// Lists are built off the main thread and remembered; the result is the same list.
    func testListsBuiltInTheBackground() async throws {
        let m = try await sampleModel()
        let key = m.listKey(.all, sort: .name, search: "new haven", here: nil)
        XCTAssertNil(m.cachedList(key))
        let built = await m.buildList(key, here: nil)
        XCTAssertEqual(built.map(\.id), m.list(.all, sort: .name, search: "new haven", here: nil).map(\.id))
        XCTAssertEqual(m.cachedList(key)?.map(\.id), built.map(\.id))
        // a sort that isn't by distance doesn't care where you are; one by distance does, to about 100 m
        let green = CLLocation(latitude: 41.3083, longitude: -72.9279), nearby = CLLocation(latitude: 41.30835, longitude: -72.92795)
        XCTAssertEqual(m.listKey(.all, sort: .name, search: "", here: green), m.listKey(.all, sort: .name, search: "", here: nil))
        XCTAssertEqual(m.listKey(.nearMe, sort: .nearest, search: "", here: green), m.listKey(.nearMe, sort: .nearest, search: "", here: nearby))
        XCTAssertNotEqual(m.listKey(.nearMe, sort: .nearest, search: "", here: green), m.listKey(.nearMe, sort: .nearest, search: "", here: nil))
    }

    /// Filters are the lists' own: Home counts, the map and Surprise me show each guide whole, and only the two toggles
    /// outlast the visit.
    func testFiltersStayInTheLists() async throws {
        let defaults = UserDefaults(suiteName: "filters-\(UUID().uuidString)")!
        let m = try await sampleModel(defaults: defaults)
        m.filters = Filters(town: "Hartford", cuisine: "Pizza", hideChains: true, confirmedOnly: true, includeNonRestaurants: true)
        XCTAssertEqual(m.count(.apizza), 2, "Home counts ignore a town filter")
        XCTAssertEqual(m.mapPlaces(.apizza).count, 2, "so does the map")
        XCTAssertNotNil(m.randomPick(from: [.apizza], excluding: nil), "and Surprise me")
        XCTAssertTrue(m.list(.apizza, sort: .name, search: "", here: nil).isEmpty, "the list itself is filtered")
        let next = try await sampleModel(defaults: defaults)
        XCTAssertEqual(next.filters, Filters(hideChains: true, confirmedOnly: true), "town, cuisine and non-restaurants reset on launch")
    }

    /// One copy of what's open, for both layouts: an iPad window going narrow (or back) keeps the list and the place.
    func testLayoutChangeKeepsListAndPlace() async throws {
        let m = try await sampleModel()
        let abbott = m.place(id: "c")!, pepe = m.place(id: "a")!
        m.tab = .guides; m.selectedGuide = .lobster; m.selectedPlace = abbott
        m.syncToCompact()
        XCTAssertEqual(m.guidesPath, [.guide(.lobster), .place(abbott)])
        m.guidesPath = [.guide(.apizza), .place(pepe)]
        m.syncToRegular()
        XCTAssertEqual(m.selectedGuide, .apizza)
        XCTAssertEqual(m.selectedPlace, pepe)
        m.guidesPath = [.guide(.diners)]
        m.syncToRegular()
        XCTAssertEqual(m.selectedGuide, .diners)
        XCTAssertNil(m.selectedPlace, "a list with no place open")
        m.tab = .map; m.selectedPlace = abbott
        m.syncToCompact()
        XCTAssertEqual(m.mapPath, [abbott])
        m.mapPath = [pepe]
        m.syncToRegular()
        XCTAssertEqual(m.selectedPlace, pepe)
        m.tab = .saved; m.savedPath = []
        m.syncToRegular()
        XCTAssertNil(m.selectedPlace)
    }

    func testFiltersSavedPlacesAndLabels() async throws {
        let m = try await sampleModel()
        m.filters.hideChains = true
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Dunkin'" })
        XCTAssertTrue(m.list(.all, sort: .name, search: "", here: nil).contains { $0.id == "a" }, "the original Pepe's isn't hidden as a chain")
        m.filters = Filters(confirmedOnly: true)
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.id == "f" }, "single listings drop out")
        XCTAssertTrue(m.list(.all, sort: .name, search: "", here: nil).contains { $0.id == "j" }, "hand-checked counts as confirmed")
        XCTAssertEqual(m.list(.dairy, sort: .name, search: "", here: nil).map(\.id), ["j"])
        m.filters = Filters(town: "New Haven")
        XCTAssertEqual(Set(m.list(.all, sort: .name, search: "", here: nil).map(\.id)), ["a", "b"])
        let p = m.place(id: "b")!
        m.toggleSaved(p)
        XCTAssertEqual(m.savedPlaces.map(\.id), ["b"])
        m.toggleSaved(p)
        XCTAssertTrue(m.savedPlaces.isEmpty)
        XCTAssertEqual(m.matchRate(for: m.place(id: "b")!), "67%")
        XCTAssertNil(m.matchRate(for: m.place(id: "a")!), "licensed places don't cite a listing rate")
        XCTAssertEqual(m.place(id: "a")!.jamesBeardLabel, "America's Classic")
        XCTAssertEqual(m.place(id: "h")!.host, "Mohegan Sun")
        XCTAssertEqual(m.place(id: "i")!.healthRating?.meaning, "Excellent")
        XCTAssertEqual(m.place(id: "i")!.healthRating?.n, "ABC Pizza", "the name the district rated it under")
        XCTAssertEqual(PlaceDetailView.date("2026-04-29"), "Apr 29, 2026")
        XCTAssertEqual(m.place(id: "c")!.jamesBeardLabel, "James Beard nominee")
    }

    /// Call only dials a US number; Website only opens a web address.
    func testPhonesAndWebsites() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.place(id: "a")!.phone, "+12038655762")
        XCTAssertEqual(m.place(id: "a")!.phoneText, "(203) 865-5762")
        XCTAssertNil(m.place(id: "b")!.phone, "+20… would dial Egypt")
        XCTAssertNil(m.place(id: "d")!.phone, "not E.164")
        XCTAssertEqual(m.place(id: "a")!.website?.absoluteString, "https://www.pepespizzeria.com/")
        XCTAssertNil(m.place(id: "b")!.website, "javascript: is never a link")
        XCTAssertNil(m.place(id: "c")!.website, "a scheme-less value isn't guessed at")
        XCTAssertNil(Place.usPhone("+1203555123"), "too short")
        XCTAssertNil(Place.usPhone("+11035551234"), "no area code starts with 1")
    }

    /// The build's own dates and sources, not ones written into the app.
    func testDataMeta() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.dataVersion, "abc123def456")
        XCTAssertEqual(m.researchChecked, "October 2026")
        XCTAssertEqual(m.sourceYears, "2025 or 2026")
        XCTAssertEqual(m.overtureRelease, "2026-09-23.1")
        XCTAssertEqual(m.fvhdFetched, "2026-10-05")
        XCTAssertEqual(m.fvhdPages["Canton"]?.absoluteString, "https://fvhd.org/environmental-health/food/food-ratings/canton/")
        // an older file without the new keys (and with a license number) still opens
        let old = """
            {"generated":"2026-10-05","cities":["New Haven"],"villages":[],"cuisines":["Pizza"],"brands":[],"hosts":[],"sources":["meta"],
             "count_restaurants":1,"calibration":{},
             "places":[{"id":"a","n":"Sally's Apizza","c":0,"cu":0,"t":1,"s":0,"lic":"LIR.0000001","ph":"(203) 624-5271","w":"sallysapizza.com"}]}
            """
        let o = try await sampleModel(json: old)
        XCTAssertEqual(o.dataVersion, "2026-10-05", "Spotlight keys on the date when there's no hash")
        XCTAssertEqual(o.researchChecked, "October 2026")
        XCTAssertNil(o.overtureRelease)
        XCTAssertTrue(o.fvhdPages.isEmpty)
    }

    /// Saved places follow a place whose id changed, through a chain of changes, and the new ids are what's kept.
    func testSavedPlacesFollowAliases() async throws {
        let defaults = UserDefaults(suiteName: "alias-\(UUID().uuidString)")!
        defaults.set(["older-b", "old-b", "b", "gone", "loop1"], forKey: "saved")
        let m = try await sampleModel(defaults: defaults)
        XCTAssertEqual(m.savedPlaces.map(\.id), ["b"], "three ids for Modern Apizza are one saved place")
        XCTAssertEqual(Set(defaults.stringArray(forKey: "saved") ?? []), ["b", "gone", "loop1"], "the remapped set is stored")
        XCTAssertEqual(m.place(id: "older-b")?.id, "b", "an old Spotlight id opens today's place")
        XCTAssertNil(m.place(id: "gone"), "an id that's gone opens nothing")
        XCTAssertNil(m.place(id: "loop1"), "a loop in the aliases ends")
    }

    func testSpotlightIndexesChainOriginalsNotBranches() throws {
        let file = try JSONDecoder().decode(DataFile.self, from: Data("""
            {"generated":"2026-10-05","cities":["New Haven","Fairfield"],"villages":[],"cuisines":["Pizza"],"brands":[],"hosts":[],"sources":["meta"],
             "count_restaurants":3,"calibration":{},
             "places":[{"id":"nh","n":"Frank Pepe Pizzeria Napoletana","c":0,"cu":0,"t":1,"s":0,"hc":1,"ch":8},
                       {"id":"ff","n":"Frank Pepe Pizzeria Napoletana","c":1,"cu":0,"t":1,"s":0,"hc":1,"ch":8,"br":"Frank Pepe Pizzeria Napoletana, New Haven"},
                       {"id":"x","n":"Some Pizza","c":1,"cu":0,"t":1,"s":0}]}
            """.utf8))
        let places = file.places.map { Place($0, file: file) }
        XCTAssertEqual(SpotlightIndexer.featured(places).map(\.id), ["nh"])
        // and "Hide chains" keeps the original, not the branch
        XCTAssertTrue(Filters(hideChains: true).allows(places[0]))
        XCTAssertFalse(Filters(hideChains: true).allows(places[1]))
    }

    /// The real bundled file decodes and holds the guides the app promises.
    func testBundledData() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "bundle-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        XCTAssertGreaterThan(m.restaurantCount, 9_000)
        XCTAssertGreaterThan(m.towns.count, 160, "nearly all 169 towns have a restaurant")
        XCTAssertGreaterThan(m.count(.apizza), 8)
        XCTAssertGreaterThan(m.count(.lobster), 30)
        // Icons: James Beard or other honors, or 40+ years at the address (not every hand-checked place)
        XCTAssertGreaterThan(m.count(.icons), 15)
        let iconYear = (Int(m.generated.prefix(4)) ?? 2026) - 40
        for p in m.places where Guide.icons.includes(p) {
            XCTAssertTrue(p.jamesBeard != nil || p.otherHonors != nil || (p.founded ?? 9999) <= iconYear, "\(p.name) (\(p.city ?? "")) isn't an icon")
        }
        XCTAssertEqual(Set(m.places.map(\.id)).count, m.places.count, "ids are unique")
        XCTAssertTrue(m.places.contains { $0.name == "Frank Pepe Pizzeria Napoletana" && $0.jamesBeardLabel == "America's Classic" && $0.city == "New Haven" })
        XCTAssertTrue(m.list(.lobster, sort: .name, search: "abbott", here: nil).contains { $0.village == "Noank" },
                      "a hand-checked shack keeps its check through duplicate merging")
        XCTAssertFalse(m.places.contains { $0.name.range(of: #"gentlem[ae]n'?s club|strip club|exotic dancer"#, options: [.regularExpression, .caseInsensitive]) != nil },
                       "adult clubs aren't restaurants")
        XCTAssertFalse(m.places.contains { ($0.website?.absoluteString ?? "").range(
            of: #"yelp\.com|business\.site|google\.com|groupon\.com|yellowpages\.com"#, options: .regularExpression) != nil },
                       "directory links were checked out")
        XCTAssertFalse(m.places.contains { $0.healthRating != nil && $0.healthRating?.d == nil }, "an official rating always shows its date")
        XCTAssertTrue(m.places.allSatisfy { $0.healthRating == nil || ["Avon", "Barkhamsted", "Canton", "Colebrook", "East Granby", "Farmington", "Granby", "Hartland", "New Hartford", "Simsbury"].contains($0.city ?? "") },
                      "Farmington Valley ratings only in its 10 towns")
        XCTAssertTrue(m.places.allSatisfy { $0.healthRating == nil || m.fvhdPages[$0.city ?? ""] != nil }, "every rated town links its ratings page")
        // hand-checked places stay in their guides with "Only licensed or confirmed places" on, and Pepe's with "Hide chains"
        func n(_ g: Guide) -> Int { m.list(g, sort: .name, search: "", here: nil).count }
        let lobster = n(.lobster), dairy = n(.dairy)
        XCTAssertEqual(lobster, m.count(.lobster), "a list without filters matches its Home card")
        m.filters.confirmedOnly = true
        XCTAssertEqual(n(.lobster), lobster)
        XCTAssertEqual(n(.dairy), dairy)
        m.filters = Filters(hideChains: true)
        XCTAssertTrue(m.list(.apizza, sort: .name, search: "", here: nil).contains { $0.name == "Frank Pepe Pizzeria Napoletana" && $0.city == "New Haven" })
        m.filters = Filters()
        // Spotlight: the original Frank Pepe (a chain of 8) is in, its branches aren't
        let spotlight = SpotlightIndexer.featured(m.places)
        XCTAssertTrue(spotlight.contains { $0.name == "Frank Pepe Pizzeria Napoletana" && $0.city == "New Haven" })
        XCTAssertFalse(spotlight.contains { $0.branchOf != nil && $0.isChain })
    }

    /// The raw file, before decoding (PlaceRecord ignores unknown keys, so a leak would decode silently).
    private func bundledJSON() throws -> [String: Any] {
        let url = try XCTUnwrap(Bundle(for: AppModel.self).url(forResource: "places", withExtension: "json") ?? Bundle.main.url(forResource: "places", withExtension: "json"))
        return try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [String: Any])
    }

    /// The app ships no Google-derived data: no rating, review, price or Google Maps field anywhere in the file.
    func testBundledDataHasNoRatingsOrReviews() throws {
        var bad: Set<String> = []
        func walk(_ v: Any) {
            if let d = v as? [String: Any] {
                for (k, x) in d {
                    let l = k.lowercased()
                    if ["rating", "ratings", "reviews", "price"].contains(l) || l.hasPrefix("gmap") || l.hasPrefix("review") { bad.insert(k) }
                    walk(x)
                }
            } else if let a = v as? [Any] {
                a.forEach(walk)
            }
        }
        walk(try bundledJSON())
        XCTAssertEqual(bad, [], "Google-style fields in places.json")
    }

    /// Every phone dials the US, and every website is a web address.
    func testBundledPhonesAndWebsites() throws {
        let places = try XCTUnwrap(try bundledJSON()["places"] as? [[String: Any]])
        let phones = places.compactMap { $0["ph"] as? String }
        XCTAssertFalse(phones.isEmpty)
        let badPhones = phones.filter { $0.range(of: #"^\+1[2-9]\d{9}$"#, options: .regularExpression) == nil }
        XCTAssertEqual(badPhones.count, 0, "not +1XXXXXXXXXX: \(badPhones.prefix(5))")
        let unscored = places.filter { $0["hc"] as? Int == 1 && $0["fs"] == nil }.compactMap { $0["n"] as? String }
        XCTAssertEqual(unscored.count, 0, "every hand-checked place has a featured score: \(unscored.prefix(5))")
        let sites = places.compactMap { $0["w"] as? String }
        let badSites = sites.filter { s in URL(string: s).map { !["http", "https"].contains($0.scheme?.lowercased() ?? "") } ?? true }
        XCTAssertEqual(badSites.count, 0, "not http(s): \(badSites.prefix(5))")
    }

    /// Ids are stable across rebuilds: saved places and Spotlight entries depend on it.
    func testBundledPinnedIds() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "ids-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertEqual(m.places.first { $0.name == "Frank Pepe Pizzeria Napoletana" && $0.address == "157 Wooster St" && $0.city == "New Haven" }?.id, Self.pepeID)
        XCTAssertEqual(m.places.first { $0.name == "Louis' Lunch" && $0.city == "New Haven" }?.id, Self.louisID)
        XCTAssertEqual(m.places.first { $0.name.lowercased().hasPrefix("abbott's lobster") && $0.city == "Groton" }?.id, Self.abbottsID)
    }
    static let pepeID = "0a0b976ee40f", louisID = "bdf91e152df9", abbottsID = "b2a5fbf14529"

    /// Natural searches on the real data.
    func testBundledSearch() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "search-\(UUID().uuidString)")!)
        await m.load()
        func ids(_ q: String) -> [String] { m.list(.all, sort: .name, search: q, here: nil).map(\.id) }
        XCTAssertFalse(ids("apizza new haven").isEmpty)
        XCTAssertEqual(ids("apizza in new haven"), ids("apizza new haven"))
        XCTAssertFalse(ids("mystic").isEmpty)
        XCTAssertEqual(ids("near mystic"), ids("mystic"))
        XCTAssertEqual(ids("pizza near me"), ids("pizza"))
        let preston = m.list(.all, sort: .name, search: "new preston", here: nil)
        XCTAssertFalse(preston.isEmpty)
        XCTAssertTrue(preston.allSatisfy { $0.village?.hasPrefix("New Preston") == true || $0.nameText.contains(" new preston") }, "the village, not Preston")
        for q in ["route 32", "ct 32"] {
            XCTAssertTrue(m.list(.all, sort: .name, search: q, here: nil).contains { ($0.address ?? "").contains("CT-32") }, "\(q) finds a CT-32 address")
        }
    }
}
