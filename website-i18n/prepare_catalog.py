"""Freeze the current public copy into translatable, complete HTML units."""
import hashlib
import json
import re
from pathlib import Path
from lxml import etree, html

ROOT = Path(__file__).resolve().parent
DOCS = ROOT.parent / "docs"
PAGES = {"home": "index.html", "privacy": "privacy/index.html", "terms": "terms/index.html"}
MESSAGES = {"ui.language_label": "Language", "ui.choose_language": "Choose language"}

def inner_html(node):
    return (node.text or "") + "".join(
        etree.tostring(child, method="html", encoding="unicode", with_tail=True)
        for child in node
    )

def key_for(value):
    key = "text." + hashlib.sha256(value.encode()).hexdigest()[:14]
    if key in MESSAGES and MESSAGES[key] != value:
        raise ValueError("Translation key collision")
    MESSAGES[key] = value
    return key

def main():
    (ROOT / "templates").mkdir(parents=True, exist_ok=True)
    for page, filename in PAGES.items():
        tree = html.document_fromstring((DOCS / filename).read_text())
        for node in tree.xpath("//a[contains(concat(' ',normalize-space(@class),' '),' language-link ')] | //nav[contains(@class,'policy-nav')]/a[@href='#tr']"):
            node.drop_tree()
        for node in tree.xpath("//nav[contains(@class,'footer-links')]/a"):
            if "Gizlilik" in node.text_content():
                node.text = "Privacy"
            elif "Koşullar" in node.text_content():
                node.text = "Terms"
        for node in tree.iter():
            if not isinstance(node.tag, str) or node.xpath("ancestor-or-self::*[@lang='tr']"):
                continue
            for attribute in ("aria-label", "alt"):
                if node.get(attribute):
                    node.set("data-i18n-" + attribute, key_for(node.get(attribute)))
            if node.tag == "meta" and node.get("name") == "description":
                node.set("data-i18n-content", key_for(node.get("content")))
            if node.xpath("ancestor::*[@data-i18n-html]"):
                continue
            is_block = node.tag in {"title", "h1", "h2", "h3", "p", "li"} or (
                node.tag == "div" and "notice" in node.get("class", "").split()
            )
            is_label = node.tag in {"a", "strong", "span"} and not len(node)
            if (is_block or is_label) and re.search(r"[A-Za-z]", node.text_content()):
                value = re.sub(r"\s+", " ", inner_html(node)).strip()
                node.set("data-i18n-html", key_for(value))
        (ROOT / "templates" / (page + ".html")).write_text(
            etree.tostring(tree, method="html", encoding="unicode", doctype="<!doctype html>") + "\n"
        )
    (ROOT / "source-messages.json").write_text(
        json.dumps(MESSAGES, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"{len(MESSAGES)} complete translation units prepared.")

if __name__ == "__main__":
    main()
