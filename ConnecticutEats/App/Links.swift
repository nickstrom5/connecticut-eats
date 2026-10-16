import Foundation

/// The app's web pages and support address, in one place.
/// The site is GitHub Pages at connecticut.eatsranked.com (scripts/make-site.py's CUSTOM_DOMAIN). GitHub forwards the old
/// github.io/connecticut-eats address to it.
enum Links {
    static let base = "https://connecticut.eatsranked.com"
    static let site = URL(string: base + "/")!
    static let privacy = URL(string: base + "/privacy.html")!
    static let terms = URL(string: base + "/terms.html")!
    static let supportEmail = "work-with-nick@gmail.com"

    static var correctionEmail: URL {
        URL(string: "mailto:\(supportEmail)?subject=Connecticut%20Eats%20correction")!
    }

    /// "Report a problem with this listing": the place's name and town in the subject, its id and address in the body.
    static func problemEmail(for p: Place) -> URL {
        let subject = "Connecticut Eats: problem with \(p.name), \(p.placeName ?? "Connecticut")"
        let body = "What's wrong with this listing (closed, moved, wrong name or details)?\n\n\n\(p.name)\n\(p.fullAddress)\nId: \(p.id)"
        var allowed = CharacterSet.urlQueryAllowed
        allowed.remove(charactersIn: "&=+?#")
        func enc(_ s: String) -> String { s.addingPercentEncoding(withAllowedCharacters: allowed) ?? "" }
        return URL(string: "mailto:\(supportEmail)?subject=\(enc(subject))&body=\(enc(body))") ?? correctionEmail
    }
}
