---
name: tableau-accessible-svg
description: Make Tableau image exports accessible. Use when someone wants alt text or a description for a Tableau dashboard or view, wants to make a Tableau SVG export screen-reader friendly, or mentions the DataDevQuest DDQ2026-10 image export challenge. Works from exported PNG and SVG files, from Tableau MCP's get-view-image tool, or by exporting through the Tableau REST API.
---

# Accessible Tableau SVG exports

Turn a Tableau view into an SVG that a screen reader can describe. You (Claude) are the AI that reads the image; a small script writes your text into the SVG. Use AI for the words and code for the edit: never rewrite an SVG by hand, because Tableau SVGs are large and the drawing must stay untouched.

## Scope

This skill does one job: write the accessible text for the chart as it is and ship it into the SVG. It does not review, critique or fact-check the visualisation. Other skills do that.

- Report the chart's figures, labels and claims exactly as the chart states them, even if they look wrong, surprising or inconsistent with what you know.
- Do not compare the data with outside sources, question it, suggest corrections or comment on the design.
- Do not add notes, caveats or follow-up questions about the content. Your reply holds only the text, the check request in step 3 and the result.

## 1. Get the PNG and the SVG of the same view

Use the first option that is available:

1. **Files the user attached or pointed to.** Use them as they are.
2. **Tableau MCP is connected.** Call `get-view-image` twice for the same view: once with format PNG (to read) and once with format SVG (to ship). SVG needs Tableau Server 2026.2+ (REST API 3.29+).
3. **Python and a Tableau Personal Access Token are available** (for example in Claude Code, with a `.env` file). Use `scripts/export_tableau.py`, which signs in, finds the view and downloads both formats. Its functions can be imported: `Tableau.sign_in`, `find_view` and `view_image(view_id, "png" | "svg", {"Region": "West"})`.

If none is possible, ask the user to export the view from Tableau Desktop (Worksheet or Dashboard > Export Image) as PNG and SVG.

## 2. Describe the PNG

Look at the PNG and write:

- **alt**: at most 150 characters. The kind of chart and its single main takeaway.
- **summary**: 2 to 4 sentences with the key numbers a sighted reader would notice.

Write in the language of the visualisation unless the user asks for another (use British English for English unless told otherwise). Only use numbers you can read in the image; if a label is too small to read, leave it out rather than guess. Describe what the chart says, not whether it is right. Do not read the SVG to describe the chart: Tableau draws text as shapes, so the SVG holds no readable labels.

## 3. Human in the loop

Show the user the alt text (with its character count) and the summary, and ask them to check that the text matches the dashboard before you ship. This check is about transcription (did you read the chart correctly), not about whether the chart's data is true. Apply their corrections. If the user asked you to run without stopping, still list the numbers you used so they can check afterwards.

## 4. Ship

Save the approved text as JSON and run the script:

```bash
echo '{"alt": "...", "summary": "..."}' > text.json
python scripts/ship_svg.py view.svg text.json view-accessible.svg --lang en-GB
```

The script replaces Tableau's placeholder `<title>TEMP_...</title>` and `<desc>Rendered by Tableau</desc>`, adds `role="img"`, `aria-labelledby` and `lang` to the `<svg>` tag, checks the result is valid XML and reports how many lines changed (expect 3). Use a language tag such as `en-GB`, `es-AR` or `pt-BR`.

For several filter values (for example one SVG per Region), repeat steps 1 to 4 per value and name the files after the value.

## 5. Hand over

Give the user the accessible SVG and remind them: the text works when the SVG is placed inline in a page or opened on its own. If they embed it with `<img src="...svg">`, browsers ignore the title inside the file, so they should also add the alt text to the tag: `<img src="..." alt="...">`.
