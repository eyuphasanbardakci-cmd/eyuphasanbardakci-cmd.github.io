"""Crawl generated pages before publication: URLs, languages and deep links."""
from collections import Counter
from urllib.parse import urljoin, urlsplit
from lxml import html
from build import DOCS, LANGUAGES, ORIGIN, PAGES, route

def local_file(path):
    target = DOCS / path.lstrip("/")
    return target / "index.html" if path.endswith("/") or target.is_dir() else target

def main():
    links = 0
    for locale, (tag, _) in LANGUAGES.items():
        for page in PAGES:
            pathname = route(locale, page)
            file = local_file(pathname)
            tree = html.document_fromstring(file.read_text())
            assert tree.get("lang") == tag, file
            assert tree.xpath("//title/text()"), file
            assert tree.xpath("//link[@rel='canonical']/@href") == [ORIGIN + pathname], file
            alternate = dict(zip(
                tree.xpath("//link[@rel='alternate']/@hreflang"),
                tree.xpath("//link[@rel='alternate']/@href")
            ))
            assert alternate == {
                **{lang_tag: ORIGIN + route(choice, page) for choice, (lang_tag, _) in LANGUAGES.items()},
                "x-default": ORIGIN + route("en", page),
            }, file
            menu = tree.xpath("//nav[@class='language-options']/a")
            assert len(menu) == 6, file
            assert {link.get("href") for link in menu} == {route(choice, page) for choice in LANGUAGES}, file
            assert [link.get("href") for link in menu if link.get("aria-current") == "true"] == [pathname], file
            active = tree.xpath("//nav[@class='site-nav']/a[@aria-current='page']/@href")
            assert active == [pathname], file
            ids = tree.xpath("//@id")
            assert all(count == 1 for count in Counter(ids).values()), file
            assert not tree.xpath("//@*[starts-with(name(), 'data-i18n-')]"), file
            if page == "privacy":
                assert "https://www.googleapis.com/auth/youtube.force-ssl" in tree.text_content(), file
                assert "RevenueCat" in tree.text_content(), file
                assert tree.xpath("//*[@id='purchases']"), file
            for node in tree.xpath("//*[@href or @src]"):
                for attribute in ("href", "src"):
                    value = node.get(attribute)
                    if not value or value.startswith(("mailto:", "tel:", "data:")):
                        continue
                    target = urlsplit(urljoin(ORIGIN + pathname, value))
                    if target.netloc != "localearc.com":
                        continue
                    destination = local_file(target.path)
                    assert destination.is_file(), (file, value, destination)
                    if target.fragment and destination.suffix == ".html":
                        remote = html.document_fromstring(destination.read_text())
                        assert remote.xpath("//*[@id=$fragment]", fragment=target.fragment), (file, value)
                    links += 1
    print(f"Verified 18 complete pages, six same-page language choices per page, hreflang/canonical metadata and {links} internal links/assets/anchors.")

if __name__ == "__main__":
    main()
