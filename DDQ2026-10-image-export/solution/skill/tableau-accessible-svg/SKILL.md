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
- Do not add notes, caveats or follow-up questions about the content.

The full skill, with its scripts (ship_svg.py and export_tableau.py), is at https://github.com/pablodatamonster/datadevquest-challenges/tree/main/DDQ2026-10-image-export/solution/skill

## Tone

The people using this are the DataFam: Tableau users sharing their work. Keep every message short, warm and encouraging, like a helpful friend at a user group.

- Lead with what is ready, then the one next step. Never lead with what is missing.
- Never say "I can't", "unfortunately", "I'm unable to" or "there's no connection". Ask for what you need as a friendly next step.
- No technical detail the user did not ask for (tokens, connections, flags such as `--lang`).
- British English unless the user writes otherwise. No emojis.

Good: "Here's the text for your viz. Tweak anything you like, then add the SVG version and I'll make it accessible."
Good: "If you're happy with the text, please upload the SVG version of your visualisation and I'll do the rest."
Good: "Done! Your accessible SVG is ready."

## 1. Get the PNG and the SVG of the same view

Use the first option that is available:

1. **Files the user attached or pointed to.** Use them as they are.
2. **Tableau MCP is connected.** Call `get-view-image` twice for the same view: once with format PNG (to read) and once with format SVG (to ship). SVG needs Tableau Server 2026.2+ (REST API 3.29+).
3. **Python and a Tableau Personal Access Token are available** (for example in Claude Code, with a `.env` file). Use `scripts/export_tableau.py`, which signs in, finds the view and downloads both formats. Its functions can be imported: `Tableau.sign_in`, `find_view` and `view_image(view_id, "png" | "svg", {"Region": "West"})`.

If you only have the PNG, do not stop: write the text first (step 2) and ask for the SVG in the review form (step 3). If you only have the SVG, ask for the PNG in one friendly line: "Could you add the PNG version of your viz too? I read the picture to write the text."

## 2. Describe the PNG

Look at the PNG and write:

- **alt**: at most 150 characters. The kind of chart and its single main takeaway.
- **summary**: 2 to 4 sentences with the key numbers a sighted reader would notice.

Write in the language of the visualisation unless the user asks for another (British English for English unless told otherwise). Only use numbers you can read in the image; if a label is too small to read, leave it out rather than guess. Describe what the chart says, not whether it is right. Do not read the SVG to describe the chart: Tableau draws text as shapes, so the SVG holds no readable labels.

## 3. Let the user review and edit

Write one short line before the form, such as "Here's the text for your viz. Tweak anything you like, then make it accessible." Then show the text as an editable form so the user can change it in place.

**When an inline widget tool is available** (in Claude.ai: `show_widget`, after loading its `elicitation` module with `read_me`), render this form. Fill the two textareas with your text (escape `&`, `<` and `>` as HTML entities) and keep the SVG upload group only when you do not have the SVG yet. Emit the two SVG icons exactly as written.

```html
<form class="elicit">
  <div class="elicit-header">
    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M11.586 2a1.5 1.5 0 0 1 1.06.44l2.914 2.914a1.5 1.5 0 0 1 .44 1.06V16.5a1.5 1.5 0 0 1-1.5 1.5h-9a1.5 1.5 0 0 1-1.492-1.347L4 16.5v-13A1.5 1.5 0 0 1 5.5 2zM5.5 3a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h9a.5.5 0 0 0 .5-.5V7h-2.5A1.5 1.5 0 0 1 11 5.5V3zm7.04 10.304a.5.5 0 0 1 .92.392c-.295.69-.871 1.304-1.66 1.304-.487 0-.892-.234-1.2-.574-.309.34-.713.574-1.2.574-.486 0-.892-.233-1.2-.574-.31.34-.714.574-1.2.574a.5.5 0 0 1 0-1c.212 0 .52-.18.74-.696l.034-.067a.5.5 0 0 1 .886.067c.221.516.528.696.74.696.213 0 .52-.18.74-.696l.035-.067a.5.5 0 0 1 .885.067c.22.516.527.696.74.696s.519-.18.74-.696m0-4a.5.5 0 0 1 .92.392c-.295.69-.871 1.304-1.66 1.304-.487 0-.892-.234-1.2-.574-.309.34-.713.574-1.2.574-.486 0-.892-.233-1.2-.574-.31.34-.714.574-1.2.574a.5.5 0 0 1 0-1c.212 0 .52-.18.74-.696l.034-.067a.5.5 0 0 1 .886.067c.221.516.528.696.74.696.213 0 .52-.18.74-.696l.035-.067a.5.5 0 0 1 .885.067c.22.516.527.696.74.696s.519-.18.74-.696M12 5.5a.5.5 0 0 0 .5.5h2.293L12 3.207z"/></svg>
    <span>Accessible text details</span>
  </div>
  <div class="elicit-body">
    <div class="elicit-group">
      <label class="elicit-question">Happy with the alt text? Edit anything you like (up to 150 characters)</label>
      <textarea class="elicit-textarea" data-name="alt" rows="2">ALT TEXT HERE</textarea>
    </div>
    <div class="elicit-group">
      <label class="elicit-question">And the summary a screen reader will read out?</label>
      <textarea class="elicit-textarea" data-name="summary" rows="5">SUMMARY HERE</textarea>
    </div>
    <div class="elicit-group">
      <label class="elicit-question">Last step: add the SVG version of your viz. Choose the file below or drag it into the chat (Worksheet or Dashboard &gt; Export Image &gt; SVG)</label>
      <div class="elicit-files" data-name="svg">
        <label class="elicit-dropzone">
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M16.5 13a.5.5 0 0 1 .5.5v2a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 15.5v-2a.5.5 0 0 1 1 0v2a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5v-2a.5.5 0 0 1 .5-.5M10 3a.5.5 0 0 1 .374.168l4 4.5.059.082a.5.5 0 0 1-.732.65l-.075-.068L10.5 4.814V13.5a.5.5 0 0 1-1 0V4.814L6.374 8.332a.5.5 0 0 1-.748-.664l4-4.5.08-.071A.5.5 0 0 1 10 3"/></svg>
          <span>Choose SVG file</span>
          <input type="file" accept=".svg,image/svg+xml">
        </label>
      </div>
    </div>
  </div>
  <div class="elicit-footer">
    <button type="button" class="elicit-skip">Skip</button>
    <button type="button" class="elicit-submit">Make it accessible</button>
  </div>
</form>
```

The user's edited text comes back as their next message (labels `Alt` and `Summary`, long values repeated in full under `--- Full content ---`), with the SVG attached if they added one. The SVG may also arrive as a file dragged into the chat instead of through the form: treat it the same way. Use their text exactly as sent. If the alt text is now over 150 characters, ship it anyway and mention the count in one friendly line.

If they skip the form or reply in plain text, use the text from their reply, or your original text if they simply said it looks good.

**When there is no widget tool** (for example in Claude Code), show the alt text with its character count and the summary as two short quoted blocks, then: "Happy with these? Change any words in your reply, or say 'looks good'." If you still need the SVG, add: "Please upload the SVG version of your visualisation too and I'll do the rest."

If the user asked you to run without stopping, skip the review and ship straight away.

## 4. Ship

Save the approved text as JSON and run the script:

```bash
echo '{"alt": "...", "summary": "..."}' > text.json
python scripts/ship_svg.py view.svg text.json view-accessible.svg --lang en-GB
```

The script replaces Tableau's placeholder `<title>TEMP_...</title>` and `<desc>Rendered by Tableau</desc>`, adds `role="img"`, `aria-labelledby` and `lang` to the `<svg>` tag, checks the result is valid XML and reports how many lines changed (expect 3). Use the language tag of the text, such as `en-GB`, `es-AR` or `pt-BR`.

If the script is not available, make exactly these edits with code (a short Python string replacement), never by retyping the file: replace the first `<title>...</title>` with `<title id="alt">ALT</title>`, the first `<desc>...</desc>` with `<desc id="summary">SUMMARY</desc>` (XML-escaped), and add ` role="img" aria-labelledby="alt summary" lang="xx"` to the opening `<svg>` tag.

For several filter values (for example one SVG per Region), repeat steps 1 to 4 per value and name the files after the value.

## 5. Hand over

Give the user the accessible SVG with one short, happy line, then one tip: the text works when the SVG is placed inline in a page or opened on its own. If they embed it with `<img src="...svg">`, browsers ignore the title inside the file, so they should also add the alt text to the tag: `<img src="..." alt="...">`.
