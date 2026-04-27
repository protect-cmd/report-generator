import re

_NAVY = '#0A1628'
_GOLD = '#C89B3C'


def _clean(text: str) -> str:
    # Strip prompt instruction markers: "--- ANYTHING — INCLUDE VERBATIM ... ---"
    text = re.sub(r'---[^\n]*(?:INCLUDE VERBATIM|MANDATORY DISCLAIMER)[^\n]*---\n?', '', text, flags=re.IGNORECASE)
    # Strip END markers: "--- END DISCLAIMER ---", "--- END SERVING INSTRUCTIONS ---"
    text = re.sub(r'---\s+END\s+[^\n]+---\n?', '', text, flags=re.IGNORECASE)
    # Remove bullet lines whose value is N/A (e.g. "• Late Fees: N/A")
    text = re.sub(r'[•·]\s+[^\n]+:\s+N/A\n?', '', text)
    # Fix single-decimal dollar amounts: $3,000.0 → $3,000.00
    text = re.sub(r'(\$[\d,]+\.\d)(?!\d)', r'\g<1>0', text)
    # Convert bare "---" separator lines to a placeholder we'll replace with <hr>
    text = re.sub(r'(?m)^---+\s*$', '__HR__', text)
    return text


def _split_sections(text: str):
    """Return (main_notice, disclaimer, serving_instructions) as strings."""
    # Disclaimer starts at "IMPORTANT NOTICE:"
    disc = re.search(r'IMPORTANT NOTICE:', text, re.IGNORECASE)
    if not disc:
        return text.strip(), '', ''

    main = text[:disc.start()].strip()
    rest = text[disc.start():]

    # Serving instructions start at "HOW TO SERVE"
    serve = re.search(r'HOW TO SERVE THIS NOTICE', rest, re.IGNORECASE)
    if not serve:
        return main, rest.strip(), ''

    disclaimer = rest[:serve.start()].strip()
    serving = rest[serve.start():].strip()
    return main, disclaimer, serving


def _to_html(text: str) -> str:
    """Convert cleaned plain text to HTML, preserving line breaks and converting __HR__."""
    text = text.replace('__HR__', '<hr class="divider">')
    return text


def generate_pdf(document_text: str, output_path: str) -> str:
    cleaned = _clean(document_text)
    main_notice, disclaimer, serving = _split_sections(cleaned)

    main_html = _to_html(main_notice)
    disc_html = (
        f'<div class="disclaimer-box">{disclaimer}</div>'
        if disclaimer else ''
    )
    serve_html = (
        f'<div class="serving-box">'
        f'<div class="serving-label">Serving Instructions</div>'
        f'{serving}'
        f'</div>'
        if serving else ''
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  /* ── Page setup — margins reserve space for fixed header + footer ── */
  @page {{
    size: letter;
    margin: 72px 0 52px 0;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.85;
    color: #1a1a1a;
    background: #fff;
  }}

  /* ── Fixed header — repeats on every page ── */
  .doc-header {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 60px;
    background: {_NAVY};
    border-bottom: 3px solid {_GOLD};
    padding: 0 56px;
    overflow: hidden;
  }}

  .doc-header-logo {{
    float: left;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 15.5pt;
    font-weight: 700;
    color: #fff;
    line-height: 60px;
    letter-spacing: 0.2px;
  }}

  .doc-header-logo span {{ color: {_GOLD}; }}

  .doc-header-meta {{
    float: right;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7pt;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 0.9px;
    line-height: 1.55;
    text-align: right;
    padding-top: 13px;
  }}

  /* ── Fixed footer — repeats on every page ── */
  .doc-footer {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 40px;
    background: {_NAVY};
    border-top: 2px solid {_GOLD};
    padding: 0 56px;
    overflow: hidden;
  }}

  .doc-footer-brand {{
    float: left;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8.5pt;
    font-weight: 700;
    color: {_GOLD};
    line-height: 40px;
  }}

  .doc-footer-contact {{
    float: right;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8pt;
    color: rgba(255,255,255,0.4);
    line-height: 40px;
  }}

  /* ── Main document body ── */
  .doc-body {{
    padding: 44px 56px 36px;
    white-space: pre-line;
  }}

  /* LLM uses <center> for the title block */
  center {{
    display: block;
    text-align: center;
    font-weight: 700;
    font-size: 12.5pt;
    color: {_NAVY};
    line-height: 1.5;
    letter-spacing: 0.2px;
  }}

  hr.divider {{
    border: none;
    border-top: 1px solid #d8d0bc;
    margin: 28px 0;
  }}

  /* ── Disclaimer box ── */
  .disclaimer-box {{
    margin: 32px 0 20px;
    padding: 14px 18px;
    background: #f8f6f1;
    border-left: 3px solid {_GOLD};
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8.5pt;
    line-height: 1.65;
    color: #555;
    white-space: pre-line;
  }}

  /* ── Serving instructions box ── */
  .serving-box {{
    margin: 20px 0 0;
    padding: 18px 22px;
    background: #f0f4f8;
    border: 1px solid #c4d0dc;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9.5pt;
    line-height: 1.75;
    color: #1a2a3a;
    white-space: pre-line;
  }}

  .serving-label {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    color: {_NAVY};
    border-bottom: 2px solid {_GOLD};
    padding-bottom: 6px;
    margin-bottom: 14px;
  }}
</style>
</head>
<body>

  <div class="doc-header">
    <div class="doc-header-logo">Eviction<span>Command</span></div>
    <div class="doc-header-meta">Document Preparation Service<br>Attorney-Reviewed · County-Specific</div>
  </div>

  <div class="doc-footer">
    <div class="doc-footer-brand">EvictionCommand.com</div>
    <div class="doc-footer-contact">(888) 322-4034 · alex@evictioncommand.com</div>
  </div>

  <div class="doc-body">
    {main_html}
    {disc_html}
    {serve_html}
  </div>

</body>
</html>"""

    from weasyprint import HTML  # noqa: PLC0415
    HTML(string=html).write_pdf(output_path)
    return output_path
