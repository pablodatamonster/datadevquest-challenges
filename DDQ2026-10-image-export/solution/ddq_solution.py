"""
DataDevQuest DDQ2026-10: Image Exports. One possible solution.

    1. EXPORT    download a Tableau view as PNG and SVG with the REST API
    2. DESCRIBE  send the PNG to Claude and get alt text + a short summary (JSON)
    3. SHIP      write that text into the SVG as <title> and <desc>
    4. REPEAT    do it once per filter value, e.g. one accessible SVG per Region

Two ways to run it:

    # Live, against your Tableau site (needs a .env file, see .env.example)
    python ddq_solution.py --view "Overview" --workbook "Superstore" --filter Region=Central,East,South,West

    # From files you already have (no Tableau site needed: start at step 2)
    python ddq_solution.py --png ../sample/oceanos-de-plastico.png --svg ../sample/oceanos-de-plastico.svg --lang es-AR

Human in the loop: the AI text is saved as <name>.json next to the SVG.
Edit it if anything is wrong, then run again with --reuse to ship your edited text
without calling the AI again.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

try:  # optional: read TABLEAU_* and ANTHROPIC_API_KEY from a .env file
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# --------------------------------------------------------------------------
# 1. EXPORT: Tableau REST API (Query View Image)
# --------------------------------------------------------------------------
@dataclass
class Tableau:
    server: str
    api: str
    token: str = ""
    site_id: str = ""

    @property
    def base(self) -> str:
        return f"{self.server.rstrip('/')}/api/{self.api}"

    def headers(self) -> dict:
        return {"X-Tableau-Auth": self.token, "Accept": "application/json"}

    def sign_in(self, pat_name: str, pat_secret: str, site: str) -> None:
        body = {"credentials": {"personalAccessTokenName": pat_name,
                                "personalAccessTokenSecret": pat_secret,
                                "site": {"contentUrl": site}}}
        r = requests.post(f"{self.base}/auth/signin", json=body,
                          headers={"Accept": "application/json"}, timeout=60)
        r.raise_for_status()
        creds = r.json()["credentials"]
        self.token, self.site_id = creds["token"], creds["site"]["id"]

    def sign_out(self) -> None:
        if self.token:
            requests.post(f"{self.base}/auth/signout", headers=self.headers(), timeout=60)

    def find_view(self, view_name: str, workbook_name: str | None = None) -> str:
        """Return the id of the view called view_name (optionally inside workbook_name)."""
        r = requests.get(f"{self.base}/sites/{self.site_id}/views",
                         params={"filter": f"name:eq:{view_name}", "pageSize": 1000},
                         headers=self.headers(), timeout=60)
        r.raise_for_status()
        views = r.json().get("views", {}).get("view", [])
        if workbook_name:
            wb = requests.get(f"{self.base}/sites/{self.site_id}/workbooks",
                              params={"filter": f"name:eq:{workbook_name}"},
                              headers=self.headers(), timeout=60)
            wb.raise_for_status()
            wb_ids = {w["id"] for w in wb.json().get("workbooks", {}).get("workbook", [])}
            views = [v for v in views if v.get("workbook", {}).get("id") in wb_ids]
        if not views:
            sys.exit(f"View '{view_name}' not found" + (f" in workbook '{workbook_name}'" if workbook_name else ""))
        if len(views) > 1:
            print(f"Note: {len(views)} views are called '{view_name}'; using the first. Add --workbook to choose.")
        return views[0]["id"]

    def view_image(self, view_id: str, fmt: str, filters: dict[str, str]) -> bytes:
        """Download the view as PNG (default) or SVG. Filters become vf_<field>=<value>."""
        params = {f"vf_{field}": value for field, value in filters.items()}
        if fmt == "svg":
            params["format"] = "SVG"          # needs REST API 3.29+ (Tableau Server 2026.2+)
        else:
            params["resolution"] = "high"     # sharper PNG for the AI to read
        r = requests.get(f"{self.base}/sites/{self.site_id}/views/{view_id}/image",
                         params=params, headers=self.headers(), timeout=300)
        r.raise_for_status()
        return r.content


# --------------------------------------------------------------------------
# 2. DESCRIBE: Claude reads the PNG
# --------------------------------------------------------------------------
LANGUAGE_NAMES = {"en": "British English", "en-gb": "British English", "en-us": "American English",
                  "es": "Spanish", "es-ar": "Argentinian Spanish", "es-es": "Spanish (Spain)",
                  "pt": "Portuguese", "pt-br": "Brazilian Portuguese", "fr": "French", "de": "German"}

PROMPT = """You are writing accessibility text for a data visualisation exported from Tableau.

Look at the image and return ONLY a JSON object with two keys:
- "alt": alt text of at most 150 characters. Say what kind of chart it is and its single main takeaway.
- "summary": 2 to 4 sentences with the key numbers a sighted reader would notice: totals, the largest and smallest values, notable trends.

Rules: write in {language}. Use only numbers you can read in the image; never guess.
Describe the chart exactly as it is: report its figures and claims as stated, even if they look wrong.
Do not fact-check, critique or comment on the data or the design, and add nothing outside the JSON.
{context}"""


def describe(png: bytes, lang: str, context: str = "") -> dict:
    import anthropic  # imported here so --reuse works without the SDK installed

    language = LANGUAGE_NAMES.get(lang.lower(), lang)
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=1024,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(png).decode()}},
            {"type": "text", "text": PROMPT.format(language=language, context=context)},
        ]}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    match = re.search(r"\{.*\}", text, flags=re.S)  # tolerate a sentence around the JSON
    if not match:
        sys.exit(f"Claude did not return JSON:\n{text}")
    data = json.loads(match.group(0))
    if len(data.get("alt", "")) > 150:
        print(f"Warning: alt text is {len(data['alt'])} characters (over 150). Review it before shipping.")
    return data


# --------------------------------------------------------------------------
# 3. SHIP: write the text into the SVG (code edits the file, not the AI)
# --------------------------------------------------------------------------
def ship(svg: str, alt: str, summary: str, lang: str) -> str:
    """Replace Tableau's placeholder <title>/<desc> (or add them) and mark the SVG as one accessible image."""
    title = f'<title id="alt">{html.escape(alt)}</title>'
    desc = f'<desc id="summary">{html.escape(summary)}</desc>'

    tag = re.search(r"<svg\b[^>]*>", svg)
    if not tag:
        sys.exit("This does not look like an SVG file (no <svg> tag found).")
    head, body = svg[:tag.end()], svg[tag.end():]

    # Tableau writes <title>TEMP_...</title><desc>Rendered by Tableau</desc> straight after <svg>.
    # Only the first of each belongs to the whole image, so replace just those.
    if re.search(r"<title\b[^>]*>.*?</title>", body, flags=re.S):
        body = re.sub(r"<title\b[^>]*>.*?</title>", lambda m: title, body, count=1, flags=re.S)
    else:
        body = "\n" + title + body
    if re.search(r"<desc\b[^>]*>.*?</desc>", body, flags=re.S):
        body = re.sub(r"<desc\b[^>]*>.*?</desc>", lambda m: desc, body, count=1, flags=re.S)
    else:
        body = body.replace(title, title + "\n" + desc, 1)

    # Accessibility attributes on the <svg> tag (drop old ones first so re-runs stay clean)
    head = re.sub(r'\s(role|aria-labelledby|lang)="[^"]*"', "", head)
    head = head[:-1] + f' role="img" aria-labelledby="alt summary" lang="{lang}">'
    return head + body


# --------------------------------------------------------------------------
# 4. Putting it together
# --------------------------------------------------------------------------
def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "view"


def process(name: str, png: bytes, svg: str, out_dir: Path, lang: str, reuse: bool, context: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.png").write_bytes(png)
    (out_dir / f"{name}.svg").write_text(svg, encoding="utf-8")
    json_path = out_dir / f"{name}.json"

    if reuse and json_path.exists():
        text = json.loads(json_path.read_text(encoding="utf-8"))
        print(f"[{name}] Reusing reviewed text from {json_path.name}")
    else:
        text = describe(png, lang, context)
        json_path.write_text(json.dumps(text, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{name}] alt ({len(text['alt'])} chars): {text['alt']}")
    print(f"[{name}] summary: {text['summary']}")
    accessible = out_dir / f"{name}-accessible.svg"
    accessible.write_text(ship(svg, text["alt"], text["summary"], lang), encoding="utf-8")
    print(f"[{name}] Saved {accessible}")
    return accessible


def parse_filter(value: str | None) -> tuple[str, list[str]] | None:
    """'Region=Central,East' -> ('Region', ['Central', 'East'])"""
    if not value:
        return None
    field, _, values = value.partition("=")
    return field.strip(), [v.strip() for v in values.split(",") if v.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="DDQ2026-10: export, describe and ship accessible SVGs.")
    src = p.add_argument_group("live: export from Tableau (settings in .env)")
    src.add_argument("--view", help="View (sheet or dashboard) name")
    src.add_argument("--workbook", help="Workbook name, if more than one view has that name")
    src.add_argument("--filter", help="Field=Value1,Value2,... one export per value, e.g. Region=East,West")
    files = p.add_argument_group("offline: start from files you already exported")
    files.add_argument("--png", type=Path)
    files.add_argument("--svg", type=Path)
    p.add_argument("--lang", default="en", help="Language for the text and the lang attribute (en, es-AR, ...)")
    p.add_argument("--out", type=Path, default=Path("output"), help="Output folder (default: output)")
    p.add_argument("--reuse", action="store_true", help="Ship the reviewed text in <name>.json instead of calling the AI")
    args = p.parse_args()

    if args.png and args.svg:  # offline mode
        name = slug(args.svg.stem)
        process(name, args.png.read_bytes(), args.svg.read_text(encoding="utf-8"),
                args.out, args.lang, args.reuse, "")
        return
    if not args.view:
        p.error("give --view (live) or both --png and --svg (offline)")

    tableau = Tableau(os.environ["TABLEAU_SERVER"], os.getenv("TABLEAU_API_VERSION", "3.29"))
    tableau.sign_in(os.environ["TABLEAU_PAT_NAME"], os.environ["TABLEAU_PAT_SECRET"], os.getenv("TABLEAU_SITE", ""))
    try:
        view_id = tableau.find_view(args.view, args.workbook)
        flt = parse_filter(args.filter)
        runs = [({flt[0]: v}, f"{slug(args.view)}-{slug(v)}") for v in flt[1]] if flt else [({}, slug(args.view))]
        for filters, name in runs:
            print(f"[{name}] Exporting PNG and SVG{' for ' + str(filters) if filters else ''}...")
            png = tableau.view_image(view_id, "png", filters)
            svg = tableau.view_image(view_id, "svg", filters).decode("utf-8")
            context = f"The view is filtered to {', '.join(f'{k} = {v}' for k, v in filters.items())}." if filters else ""
            process(name, png, svg, args.out, args.lang, args.reuse, context)
    finally:
        tableau.sign_out()


if __name__ == "__main__":
    main()
