"""Email composition: placeholders, postscript, valid HTML."""

from bs4 import BeautifulSoup

import content
from charts import ChartEntry

TEMPLATE = "[TITLE] [NAME],\n\nAlles Gute!\n\n[SENDER]"


def test_feminine_salutation():
    text = content.fill_placeholders(TEMPLATE, "Anna", "f", "Chris")
    assert text.startswith("Liebe Anna,")


def test_masculine_salutation():
    text = content.fill_placeholders(TEMPLATE, "Ben", "m", "Chris")
    assert text.startswith("Lieber Ben,")


def test_no_placeholder_survives():
    text = content.fill_placeholders(TEMPLATE, "Anna", "f", "Chris")
    for token in ("[TITLE]", "[NAME]", "[SENDER]"):
        assert token not in text


def test_postscript_with_and_without_links():
    entries = [
        ChartEntry("Song A", "Artist A", "https://open.spotify.com/a"),
        ChartEntry("Song B & C", "Artist B", None),
    ]
    ps = content.render_postscript("5.3.1990", entries)
    assert "5.3.1990" in ps
    assert '<a href="https://open.spotify.com/a">' in ps
    assert "Song B &amp; C" in ps  # escaped, and rendered without a link
    assert ps.count("<li>") == 2 and ps.count("<a ") == 1


def test_postscript_empty_without_entries():
    assert content.render_postscript("5.3.1990", []) == ""


def test_compose_html_structure():
    greeting = content.fill_placeholders(TEMPLATE, "Anna", "f", "Chris")
    ps = content.render_postscript(
        "5.3.1990", [ChartEntry("T", "A", "https://open.spotify.com/t")])
    html_body = content.compose_html(greeting, ps, "test-cid")

    assert "\n" not in html_body.split("<body>")[1].split("<ul>")[0]
    soup = BeautifulSoup(html_body, "html.parser")
    assert soup.find("img")["src"] == "cid:test-cid"
    assert soup.find("ul") is not None
    assert "Liebe Anna," in soup.get_text()
    # the legacy composer emitted a malformed '</p' - guard against it
    assert "</p " not in html_body and "</p<" not in html_body


def test_compose_html_without_postscript():
    html_body = content.compose_html("Hallo", "", "cid-x")
    assert "<ul>" not in html_body
    assert 'src="cid:cid-x"' in html_body


def test_review_subject_names_person_and_address():
    subject = content.review_subject("Anna", "anna@example.org")
    assert subject == "Geburtstagsmail für Anna (anna@example.org)"


def test_routing_block_shows_escaped_plain_text_address():
    block = content.render_routing_block("A & B", "a+b@example.org")
    assert "A &amp; B" in block
    assert "a+b@example.org" in block
    assert "&lt;a+b@example.org&gt;" in block  # not a live angle-tag
    assert "mailto:" not in block
    assert "Diesen Kasten vor dem Weiterleiten entfernen." in block


def test_routing_block_is_visually_separated():
    block = content.render_routing_block("Anna", "anna@example.org")
    soup = BeautifulSoup(block, "html.parser")
    style = soup.find("div")["style"]
    assert "border" in style and "background" in style


def test_compose_html_places_routing_block_first():
    block = content.render_routing_block("Anna", "anna@example.org")
    html_body = content.compose_html("Hallo", "", "cid-x", block)
    body_content = html_body.split("<body>")[1]
    assert body_content.startswith(block)


def test_compose_html_unchanged_without_routing_block():
    # FR-006: the greeting document must stay byte-identical to the
    # pre-feature composer output when no leading block is given
    html_body = content.compose_html("Liebe Anna,\nAlles Gute!", "", "cid-x")
    assert html_body == (
        '<html><head><meta charset="utf-8"></head><body>'
        "<p>Liebe Anna,<br>Alles Gute!</p>"
        '<p><img src="cid:cid-x"></p>'
        "</body></html>"
    )


def test_stripping_routing_block_restores_original_document():
    block = content.render_routing_block("Anna", "anna@example.org")
    with_block = content.compose_html("Hallo", "", "cid-x", block)
    without_block = content.compose_html("Hallo", "", "cid-x")
    assert with_block.replace(block, "") == without_block
