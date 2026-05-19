"""Convert Markdown assessment reports to polished self-contained HTML."""
from __future__ import annotations

import re
from pathlib import Path

import markdown

# Google Fonts loaded via <link> in <head> (not @import inside <style>)
# so it works correctly in self-contained HTML and browser-print-to-PDF.
_GOOGLE_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800'
    "&family=Inter:wght@300;400;500;600;700&display=swap\" rel=\"stylesheet\">"
)

_CSS = """
:root {
    /* Headstorm brand */
    --hs-primary:       #e75b27;
    --hs-primary-dark:  #c94a1e;
    --hs-primary-soft:  #fdece3;
    --hs-secondary:     #1a2b4c;
    --hs-accent:        #00b2e3;

    --hs-bg:            #ffffff;
    --hs-bg-surface:    #f7f5f2;
    --hs-bg-cream:      #fbf8f4;

    --hs-text:          #1a2b4c;
    --hs-text-secondary:#4b5563;
    --hs-text-muted:    #8a93a3;
    --hs-text-inverse:  #ffffff;

    --hs-border:        #e6e2dc;

    --hs-font-heading:  'Montserrat', sans-serif;
    --hs-font-body:     'Inter', sans-serif;

    /* Maturity level colours */
    --l1: #ef4444;
    --l2: #f59e0b;
    --l3: #3b82f6;
    --l4: #10b981;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html { background: var(--hs-bg); }

body {
    font-family: var(--hs-font-body);
    font-size: 11.5pt;
    line-height: 1.6;
    color: var(--hs-text);
    background: var(--hs-bg);
    max-width: 7.2in;
    margin: 0 auto;
    padding: 0.5in 0.5in 0.75in;
    position: relative;
}

/* Orange left-edge brand bar */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 8px;
    height: 100%;
    background: var(--hs-primary);
    z-index: 1000;
}

/* ── Typography ─────────────────────────────────────────── */

h1, h2, h3, h4, h5, h6 {
    font-family: var(--hs-font-heading);
    color: var(--hs-secondary);
    line-height: 1.2;
    letter-spacing: -0.01em;
}

h1 {
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 0.6em 0;
    padding-bottom: 0.2em;
}

h1::after {
    content: '';
    display: block;
    width: 60px;
    height: 4px;
    background: var(--hs-primary);
    border-radius: 2px;
    margin-top: 0.4em;
}

/* Sub-line under the h1 (team / date) */
h1 + p {
    color: var(--hs-text-secondary);
    font-size: 0.95em;
    margin-bottom: 1.6em;
}

h2 {
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--hs-secondary);
    margin: 1.6em 0 0.5em;
    padding-bottom: 0.25em;
    border-bottom: 2px solid var(--hs-primary);
}

h3 {
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--hs-primary);
    margin: 1.3em 0 0.3em;
}

h4 {
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--hs-secondary);
    margin: 1em 0 0.2em;
}

p { margin: 0.5em 0 0.8em; }

strong {
    color: var(--hs-primary);
    font-weight: 700;
}

em {
    color: var(--hs-text-secondary);
    font-style: italic;
}

/* Overall score highlight — class injected by Python post-processing */
p.score-highlight {
    font-size: 1.15em;
    font-family: var(--hs-font-heading);
    font-weight: 600;
    background: var(--hs-primary-soft);
    border-left: 5px solid var(--hs-primary);
    padding: 0.6em 1em;
    border-radius: 0 0.4rem 0.4rem 0;
    margin: 1em 0;
}

/* ── Lists ──────────────────────────────────────────────── */

ul, ol {
    margin: 0.4em 0 1em 0.3em;
    padding-left: 1.3em;
}

li { margin-bottom: 0.35em; }

li::marker {
    color: var(--hs-primary);
    font-weight: 700;
}

/* ── Blockquotes ────────────────────────────────────────── */

blockquote {
    border: none;
    border-left: 5px solid var(--hs-primary);
    background: var(--hs-bg-cream);
    padding: 0.9em 1.3em;
    margin: 1.2em 0;
    border-radius: 0 0.4rem 0.4rem 0;
    font-style: normal;
    font-size: 1.02em;
    color: var(--hs-secondary);
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(26,43,76,0.05);
}

blockquote strong { color: var(--hs-primary); }

/* ── Code ───────────────────────────────────────────────── */

code {
    font-family: 'SF Mono', ui-monospace, Menlo, Monaco, monospace;
    font-size: 0.88em;
    background: var(--hs-bg-surface);
    color: var(--hs-primary-dark);
    padding: 0.12em 0.4em;
    border-radius: 0.25rem;
    border: 1px solid var(--hs-border);
}

pre {
    background: var(--hs-secondary);
    border-radius: 0.5rem;
    padding: 1em 1.2em;
    border-left: 5px solid var(--hs-primary);
    box-shadow: 0 4px 12px rgba(26,43,76,0.12);
    overflow-x: auto;
    margin: 1em 0;
}

pre code {
    background: transparent;
    color: #f1efea;
    padding: 0;
    border: none;
    font-size: 0.9em;
    line-height: 1.45;
}

/* ── Tables ─────────────────────────────────────────────── */

table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.92em;
    margin: 1em 0 1.3em;
    background: var(--hs-bg);
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(26,43,76,0.08);
    line-height: 1.4;
}

th {
    background: var(--hs-secondary);
    color: var(--hs-text-inverse);
    font-family: var(--hs-font-heading);
    font-weight: 600;
    font-size: 0.82em;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.55em 1em;
    text-align: left;
    border: none;
}

td {
    padding: 0.45em 1em;
    border-bottom: 1px solid var(--hs-border);
    vertical-align: middle;
}

tr:last-child td { border-bottom: none; }

tr:nth-child(even) td { background: var(--hs-bg-cream); }

/* Dimension header rows in the score matrix */
td strong { color: var(--hs-primary); }

td code {
    background: rgba(231,91,39,0.08);
    color: var(--hs-primary-dark);
    border-color: rgba(231,91,39,0.2);
}

/* ── Horizontal rules ───────────────────────────────────── */

hr {
    border: none;
    border-top: 1px solid var(--hs-border);
    margin: 2em 0;
}

/* ── Print / PDF ────────────────────────────────────────── */

@media print {
    body {
        max-width: none;
        margin: 0;
        padding: 0;
        font-size: 10.5pt;
    }

    body::before { display: none; }

    h1 { page-break-before: auto; break-before: auto; }
    h2, h3, h4 { page-break-after: avoid; break-after: avoid; }

    pre, blockquote, table { page-break-inside: avoid; break-inside: avoid; }

    hr { display: none; }

    a { color: var(--hs-primary); border-bottom: none; }

    pre {
        white-space: pre-wrap;
        overflow-wrap: break-word;
        overflow-x: visible;
    }
}
"""


def _inject_score_highlight(html: str) -> str:
    """Add .score-highlight class to the overall maturity score paragraph.

    Targets the paragraph that begins with <strong>Overall Maturity:
    so print/PDF renderers that lack :has() support still style it correctly.
    """
    return re.sub(
        r'(<p>)(<strong>Overall Maturity:)',
        r'<p class="score-highlight">\2',
        html,
    )


def md_to_html(md_path: Path, html_path: Path) -> None:
    """Convert a Markdown report to a self-contained HTML file."""
    md_text = md_path.read_text()

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "attr_list"],
    )

    html_body = _inject_score_highlight(html_body)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Maturity Assessment Report</title>
{_GOOGLE_FONTS_LINK}
<style>
{_CSS}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html)
