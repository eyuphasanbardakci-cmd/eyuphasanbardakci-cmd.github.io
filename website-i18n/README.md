# LocaleArc website translations

The public site has six complete interface languages: English, Turkish,
German, Spanish, French and Brazilian Portuguese. Each has a product page,
privacy policy and terms page. English keeps the existing root URLs used by
Google verification; other languages have explicit /tr/, /de/, /es/,
/fr/ and /pt-br/ routes. The previous Turkish sections and their anchors
remain available on the English pages for older app links.

source-messages.json contains complete English HTML paragraphs and UI labels.
The five locale JSON files translate those same stable keys. The templates
folder preserves the layout and legacy Turkish sections.
In the app workspace, output goes to docs; in the website repository it goes
to the repository root, matching the existing GitHub Pages configuration.
Edit a message and its translations together when the public copy changes;
the policy effective date is not changed merely by translating it.

Run with Python 3.9+ and lxml:

    python3 website-i18n/build.py
    python3 website-i18n/verify.py

The builder rejects missing translations, changed markup/URLs, altered code
literals and changed numeric facts. It generates static HTML, alternate
language links, a sitemap and robots.txt. Visitors can use the language menu
without JavaScript or cookies; switching languages preserves the type of
page. prepare_catalog.py was the initial migration helper and must not be
run over generated output during normal copy updates.
