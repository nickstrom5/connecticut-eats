import Foundation

/// The app's web pages and support address, in one place.
/// The site is GitHub Pages. Until the connecticut.eatsranked.com DNS record exists, links use the github.io address; once it
/// resolves (dig shows the CNAME) and Pages serves it, switch these with scripts/make-site.py's CUSTOM_DOMAIN. GitHub forwards
/// the old address, so builds that shipped with it keep working.
enum Links {
    static let base = "https://nickstrom5.github.io/connecticut-eats"
    static let site = URL(string: base + "/")!
    static let privacy = URL(string: base + "/privacy.html")!
    static let terms = URL(string: base + "/terms.html")!
    static let supportEmail = "work-with-nick@gmail.com"

    static var correctionEmail: URL {
        URL(string: "mailto:\(supportEmail)?subject=Connecticut%20Eats%20correction")!
    }
}
