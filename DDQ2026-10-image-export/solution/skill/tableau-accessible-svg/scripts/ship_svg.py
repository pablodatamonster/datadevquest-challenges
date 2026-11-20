"""
Write alt text and a summary into a Tableau SVG export so screen readers can read it.

    python ship_svg.py input.svg text.json output.svg --lang en-GB

text.json: {"alt": "...", "summary": "..."}
Only the <svg> tag and Tableau's placeholder <title>/<desc> change; the drawing is untouched.
"""
import argparse, html, json, re, sys
import xml.etree.ElementTree as ET


def ship(svg: str, alt: str, summary: str, lang: str) -> str:
    title = f'<title id="alt">{html.escape(alt)}</title>'
    desc = f'<desc id="summary">{html.escape(summary)}</desc>'
    tag = re.search(r"<svg\b[^>]*>", svg)
    if not tag:
        sys.exit("No <svg> tag found: is this an SVG file?")
    head, body = svg[:tag.end()], svg[tag.end():]
    if re.search(r"<title\b[^>]*>.*?</title>", body, flags=re.S):
        body = re.sub(r"<title\b[^>]*>.*?</title>", lambda m: title, body, count=1, flags=re.S)
    else:
        body = "\n" + title + body
    if re.search(r"<desc\b[^>]*>.*?</desc>", body, flags=re.S):
        body = re.sub(r"<desc\b[^>]*>.*?</desc>", lambda m: desc, body, count=1, flags=re.S)
    else:
        body = body.replace(title, title + "\n" + desc, 1)
    head = re.sub(r'\s(role|aria-labelledby|lang)="[^"]*"', "", head)
    head = head[:-1] + f' role="img" aria-labelledby="alt summary" lang="{lang}">'
    return head + body


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("svg"); p.add_argument("text_json"); p.add_argument("out")
    p.add_argument("--lang", default="en")
    a = p.parse_args()
    text = json.load(open(a.text_json, encoding="utf-8"))
    original = open(a.svg, encoding="utf-8").read()
    result = ship(original, text["alt"], text["summary"], a.lang)
    ET.fromstring(result.encode("utf-8"))  # fail loudly if the result is not valid XML
    changed = sum(1 for x, y in zip(original.splitlines(), result.splitlines()) if x != y)
    open(a.out, "w", encoding="utf-8").write(result)
    print(f"Saved {a.out} ({changed} line(s) changed, alt text {len(text['alt'])} characters)")
