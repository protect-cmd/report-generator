import re


def generate_pdf(document_text: str, output_path: str) -> str:
    # Convert --- separator lines to styled hr elements
    body = re.sub(r'(?m)^---+$', '<hr class="divider">', document_text)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: letter;
    margin: 0;
  }}

  * {{
    box-sizing: border-box;
  }}

  body {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #1a1a1a;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }}

  /* ── Header ── */
  .doc-header {{
    background: #0A1628;
    border-bottom: 3px solid #C89B3C;
    padding: 18px 56px;
    overflow: hidden;
  }}

  .doc-header-logo {{
    float: left;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 16pt;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.3px;
  }}

  .doc-header-logo span {{
    color: #C89B3C;
  }}

  .doc-header-meta {{
    float: right;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7.5pt;
    color: rgba(255, 255, 255, 0.45);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    line-height: 1.7;
    text-align: right;
    padding-top: 4px;
  }}

  /* ── Body ── */
  .doc-body {{
    padding: 48px 56px 40px;
    white-space: pre-line;
  }}

  /* LLM outputs <center> for the title block */
  center {{
    display: block;
    text-align: center;
    font-weight: 700;
    font-size: 12.5pt;
    color: #0A1628;
    line-height: 1.5;
    margin-bottom: 6px;
    letter-spacing: 0.2px;
  }}

  hr.divider {{
    border: none;
    border-top: 1px solid #d4c9b0;
    margin: 28px 0;
  }}

  /* ── Footer ── */
  .doc-footer {{
    background: #0A1628;
    border-top: 3px solid #C89B3C;
    padding: 13px 56px;
    overflow: hidden;
  }}

  .doc-footer-brand {{
    float: left;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    font-weight: 700;
    color: #C89B3C;
  }}

  .doc-footer-contact {{
    float: right;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8pt;
    color: rgba(255, 255, 255, 0.4);
    text-align: right;
  }}
</style>
</head>
<body>
  <div class="doc-header">
    <div class="doc-header-logo">Eviction<span>Command</span></div>
    <div class="doc-header-meta">Document Preparation Service<br>Attorney-Reviewed · County-Specific</div>
  </div>

  <div class="doc-body">{body}</div>

  <div class="doc-footer">
    <div class="doc-footer-brand">EvictionCommand.com</div>
    <div class="doc-footer-contact">(888) 322-4034 · alex@evictioncommand.com</div>
  </div>
</body>
</html>"""

    from weasyprint import HTML  # noqa: PLC0415
    HTML(string=html_content).write_pdf(output_path)
    return output_path
