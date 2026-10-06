"""Render complete, static pages for the six LocaleArc interface languages."""
import collections
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from lxml import etree, html

ROOT = Path(__file__).resolve().parent
DOCS = ROOT.parent / "docs" if (ROOT.parent / "docs" / "CNAME").exists() else ROOT.parent
ORIGIN = "https://localearc.com"
PAGES = {"home": "", "privacy": "privacy/", "terms": "terms/"}
LANGUAGES = {
    "en": ("en", "English"),
    "tr": ("tr", "Türkçe"),
    "de": ("de", "Deutsch"),
    "es": ("es", "Español"),
    "fr": ("fr", "Français"),
    "pt-br": ("pt-BR", "Português (Brasil)"),
}

def route(locale, page):
    prefix = "" if locale == "en" else locale + "/"
    return "/" + prefix + PAGES[page]

def fragment(value):
    return html.fragment_fromstring(value, create_parent="div")

def markup_signature(value):
    return [
        (node.tag, tuple(sorted(node.attrib.items())))
        for node in fragment(value).iterdescendants()
    ]

def validate_translations(source, translated, locale):
    missing = set(source) - set(translated)
    extra = set(translated) - set(source)
    if missing or extra:
        raise ValueError(f"{locale}: missing keys {sorted(missing)}, extra keys {sorted(extra)}")
    for key, original in source.items():
        value = translated[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{locale}: empty translation {key}")
        if markup_signature(original) != markup_signature(value):
            raise ValueError(f"{locale}: changed HTML or link attributes in {key}")
        original_code = fragment(original).xpath(".//code/text()")
        if original_code != fragment(value).xpath(".//code/text()"):
            raise ValueError(f"{locale}: changed literal code in {key}")
        if collections.Counter(re.findall(r"\d+", original)) != collections.Counter(re.findall(r"\d+", value)):
            raise ValueError(f"{locale}: changed numeric facts in {key}")

def set_inner_html(node, value):
    content = fragment(value)
    for child in list(node):
        node.remove(child)
    node.text = content.text
    for child in list(content):
        node.append(child)

def localized_link(value, page, locale):
    if not value or value.startswith(("#", "mailto:", "tel:", "data:")):
        return value
    absolute = urlsplit(urljoin(ORIGIN + route("en", page), value))
    if absolute.netloc != "localearc.com":
        return value
    path = absolute.path
    for target, suffix in PAGES.items():
        if path.rstrip("/") == ("/" + suffix).rstrip("/"):
            path = route(locale, target)
            break
    return urlunsplit(("", "", path, absolute.query, absolute.fragment))

def add_language_menu(tree, translated, locale, page):
    nav = tree.xpath("//nav[contains(concat(' ', normalize-space(@class), ' '), ' site-nav ')]")[0]
    menu = etree.SubElement(nav, "details", {"class": "language-menu"})
    summary = etree.SubElement(menu, "summary", {"aria-label": translated["ui.choose_language"]})
    summary.text = LANGUAGES[locale][1]
    options = etree.SubElement(menu, "nav", {
        "class": "language-options",
        "aria-label": translated["ui.language_label"],
    })
    for choice, (tag, label) in LANGUAGES.items():
        attributes = {"href": route(choice, page), "lang": tag, "hreflang": tag, "aria-label": label}
        if choice == locale:
            attributes["aria-current"] = "true"
        link = etree.SubElement(options, "a", attributes)
        link.text = label

def render(locale, page, translated):
    tree = html.document_fromstring((ROOT / "templates" / (page + ".html")).read_text())
    if locale != "en":
        for node in tree.xpath("//*[@lang='tr']"):
            node.drop_tree()
    tree.set("lang", LANGUAGES[locale][0])
    for node in tree.xpath("//*[@data-i18n-html]"):
        set_inner_html(node, translated[node.attrib.pop("data-i18n-html")])
    for node in tree.iter():
        for attribute in list(node.attrib):
            if attribute.startswith("data-i18n-"):
                actual = attribute.removeprefix("data-i18n-")
                node.set(actual, translated[node.attrib.pop(attribute)])
        for attribute in ("href", "src"):
            if node.get(attribute):
                node.set(attribute, localized_link(node.get(attribute), page, locale))
    head = tree.find("head")
    canonical = ORIGIN + route(locale, page)
    tree.xpath("//link[@rel='canonical']")[0].set("href", canonical)
    tree.xpath("//meta[@property='og:url']")[0].set("content", canonical)
    tree.xpath("//meta[@property='og:title']")[0].set("content", tree.xpath("//title")[0].text_content())
    for node in tree.xpath("//link[@rel='alternate' and @hreflang]"):
        node.getparent().remove(node)
    for choice, (tag, _) in LANGUAGES.items():
        etree.SubElement(head, "link", {"rel": "alternate", "hreflang": tag, "href": ORIGIN + route(choice, page)})
    etree.SubElement(head, "link", {"rel": "alternate", "hreflang": "x-default", "href": ORIGIN + route("en", page)})
    add_language_menu(tree, translated, locale, page)
    output = DOCS / route(locale, page).lstrip("/") / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = etree.tostring(tree, method="html", encoding="unicode", doctype="<!doctype html>")
    output.write_text("\n".join(line.rstrip() for line in rendered.splitlines()) + "\n")
    return output

def main():
    source = json.loads((ROOT / "source-messages.json").read_text())
    translations = {"en": source}
    for locale in LANGUAGES:
        if locale == "en":
            continue
        translations[locale] = json.loads((ROOT / (locale + ".json")).read_text())
        validate_translations(source, translations[locale], locale)
    generated = []
    for locale, translated in translations.items():
        for page in PAGES:
            generated.append(render(locale, page, translated))
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    xhtml = "http://www.w3.org/1999/xhtml"
    sitemap = etree.Element("{" + namespace + "}urlset", nsmap={None: namespace, "xhtml": xhtml})
    for locale in LANGUAGES:
        for page in PAGES:
            entry = etree.SubElement(sitemap, "{" + namespace + "}url")
            etree.SubElement(entry, "{" + namespace + "}loc").text = ORIGIN + route(locale, page)
            for choice, (tag, _) in LANGUAGES.items():
                etree.SubElement(entry, "{" + xhtml + "}link", {
                    "rel": "alternate", "hreflang": tag, "href": ORIGIN + route(choice, page)
                })
            etree.SubElement(entry, "{" + xhtml + "}link", {
                "rel": "alternate", "hreflang": "x-default", "href": ORIGIN + route("en", page)
            })
    (DOCS / "sitemap.xml").write_bytes(etree.tostring(sitemap, encoding="utf-8", xml_declaration=True, pretty_print=True))
    (DOCS / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://localearc.com/sitemap.xml\n")
    print(f"Rendered {len(generated)} pages in {len(LANGUAGES)} languages; HTML, links, code and numeric facts preserved.")

if __name__ == "__main__":
    main()
