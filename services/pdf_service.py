import html as _html

from weasyprint import HTML


def generate_pdf(document_text: str, output_path: str) -> str:
    safe_text = _html.escape(document_text).replace("\n", "<br>")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.6;
    margin: 1in;
    color: #000;
  }}
  h1 {{ font-size: 14pt; text-align: center; text-transform: uppercase; }}
  .disclaimer {{
    font-size: 10pt;
    border-top: 1px solid #000;
    margin-top: 40px;
    padding-top: 10px;
    color: #333;
  }}
  .serving-instructions {{
    font-size: 10pt;
    margin-top: 20px;
    padding: 10px;
    border: 1px solid #ccc;
  }}
</style>
</head>
<body>
  {safe_text}
</body>
</html>"""

    HTML(string=html_content).write_pdf(output_path)
    return output_path
