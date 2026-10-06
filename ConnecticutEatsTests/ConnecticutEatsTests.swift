import XCTest
import CoreLocation
@testable import ConnecticutEats

@MainActor
final class ConnecticutEatsTests: XCTestCase {

    /// A tiny data file with the same shape as Resources/places.json.
    private func sampleModel() async throws -> AppModel {
        let json = """
        {"v":1,"generated":"2026-10-05","cities":["New Haven","Groton","Stonington","Meriden","Hartford","Canton","New Britain"],"villages":["Mystic","Noank"],
         "cuisines":["Pizza","Seafood","Burgers","Bar & Pub","American & Other"],"brands":["Dunkin'"],"hosts":["Foxwoods","Mohegan Sun"],
         "tags":["apizza","lobster","clams","steamed","hotdog","dairy","diner","polish"],"sources":["official","meta","AllThePlaces","DAC","research"],
         "count":9,"count_restaurants":8,
         "calibration":{"hartford":{"Meta, confidence 0.95+":{"n":258,"matched":0.674},"Meta, 0.90-0.95":{"n":83,"matched":0.398}}},
         "places":[
          {"id":"a","n":"Frank Pepe Pizzeria Napoletana","c":0,"cu":0,"t":2,"s":0,"j":1,"lk":"Restaurant Liquor","hc":1,"k":1,"g":1,"h":1,"ip":90,"a":"157 Wooster St","z":"06511","la":41.3029,"lo":-72.9171,"f":1925,"dish":"white clam pie","jbf":"America's Classics 1999"},
          {"id":"b","n":"Modern Apizza","c":0,"cu":0,"t":1,"s":1,"hc":1,"k":1,"g":1,"ip":70,"a":"874 State St","la":41.3175,"lo":-72.9067,"f":1934},
          {"id":"c","n":"Abbott's Lobster in the Rough","c":1,"vi":1,"cu":1,"t":1,"s":1,"hc":1,"k":6,"seas":1,"sea":"May to October","ip":60,"a":"117 Pearl St","la":41.3196,"lo":-71.9897,"dish":"hot buttered lobster roll"},
          {"id":"d","n":"Ted's Restaurant","c":3,"cu":2,"t":1,"s":1,"hc":1,"k":24,"g":8,"ip":65,"a":"1046 Broad St","la":41.5530,"lo":-72.8018,"f":1959},
          {"id":"e","n":"Dunkin'","c":4,"cu":4,"t":1,"s":2,"b":0,"ch":400,"la":41.7637,"lo":-72.6851},
          {"id":"f","n":"Mystic Diner","c":2,"vi":0,"cu":4,"t":0,"s":1,"g":64,"a":"10 Main St","la":41.354,"lo":-71.966},
          {"id":"g","n":"Cumberland Farms","c":4,"cu":4,"t":1,"s":1,"v":1,"la":41.77,"lo":-72.68},
          {"id":"h","n":"Bobby's Burgers","c":4,"cu":2,"t":1,"s":1,"host":1,"la":41.49,"lo":-72.09},
          {"id":"i","n":"ABC Pizza & Restaurant","c":5,"cu":0,"t":1,"s":1,"a":"9 River St","la":41.82,"lo":-72.92,"fv":{"r":"A","d":"2026-04-29"}}
         ]}
        """
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("places-test.json")
        try json.data(using: .utf8)!.write(to: url)
        let model = AppModel(defaults: UserDefaults(suiteName: "test-\(UUID().uuidString)")!)
        await model.load(from: url)
        XCTAssertTrue(model.isLoaded, model.loadError ?? "")
        return model
    }

    func testDecodesAndHidesNonRestaurantsByDefault() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.places.count, 9)
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
        XCTAssertEqual(ids("🍕"), [], "nothing searchable typed means no results, not everything")
        XCTAssertEqual(ids("!!! ?"), [])
    }

    func testNearestSort() async throws {
        let m = try await sampleModel()
        let green = CLLocation(latitude: 41.3083, longitude: -72.9279)
        let near = m.list(.nearMe, sort: .nearest, search: "", here: green)
        XCTAssertEqual(near.first?.id, "a", "Pepe's is closest to the New Haven Green")
    }

    func testFiltersSavedPlacesAndLabels() async throws {
        let m = try await sampleModel()
        m.filters.hideChains = true
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Dunkin'" })
        m.filters = Filters(confirmedOnly: true)
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.id == "f" }, "single listings drop out")
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
        XCTAssertEqual(PlaceDetailView.date("2026-04-29").isEmpty, false)
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
        XCTAssertGreaterThan(m.count(.icons), 80)
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
    }
}
