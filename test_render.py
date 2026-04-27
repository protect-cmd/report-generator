"""Quick local test — renders template_3day.html with dummy data, no LLM call.

Opens in browser for content review. Use browser File > Print > Save as PDF for a
paginated preview. Chrome's headless print-to-PDF mishandles position:fixed across
page breaks; WeasyPrint on Railway is the authoritative renderer for headers/footers.
"""
import subprocess
from pathlib import Path

DUMMY_DATA = {
    "notice_date": "April 27, 2026",
    "notice_type_label": "Three (3)-Day Notice to Pay or Vacate",
    "statute_reference": "O.C.G.A. § 44-7-50(c), as amended by 2024 Ga. Laws Act 392 (HB 404)",
    "landlord_name": "Zeann Co",
    "landlord_address": "123 Main St, Atlanta, Georgia 30301",
    "tenant_names": ["Chris Movado", "Maria Movado"],
    "property_address": "123 Main St, Atlanta, Fulton County, Georgia 30301",
    "total_amount_owed": "$4,000.00",
    "total_amount_words": "FOUR THOUSAND DOLLARS AND ZERO CENTS",
    "deadline_date": "Thursday, May 1, 2026",
    "itemized_charges": [
        {"description": "Past Due Rent — March 2026", "amount": "$2,000.00"},
        {"description": "Past Due Rent — April 2026", "amount": "$2,000.00"},
    ],
    "body_paragraphs": [
        (
            "NOTICE IS HEREBY GIVEN to Chris Movado and Maria Movado that you are currently in default "
            "of the lease agreement governing the above-referenced premises due to your failure to pay "
            "rent when due. Pursuant to O.C.G.A. § 44-7-50(c), as amended by 2024 Ga. Laws Act 392, "
            "you are hereby served with this formal demand to either pay the full amount outstanding or "
            "vacate and surrender possession of the leased property."
        ),
        (
            "The total amount currently past due and owing as of the date of this notice is FOUR THOUSAND "
            "DOLLARS AND ZERO CENTS ($4,000.00), representing two (2) months of unpaid rent at $2,000.00 "
            "per month. You are required to pay this amount in full or vacate the premises within THREE (3) "
            "BUSINESS DAYS from the date of this notice, excluding Saturdays, Sundays, and state legal holidays."
        ),
        (
            "If you fail to pay the full amount owed or vacate the premises by the deadline stated above, "
            "the Landlord will proceed to file a Dispossessory Affidavit at the Magistrate Court in Fulton "
            "County, Georgia, and pursue all legal remedies available under Georgia law."
        ),
    ],
    "serving_instructions": (
        "HOW TO SERVE THIS NOTICE IN GEORGIA (O.C.G.A. § 44-7-50(d)):\n\n"
        "Step 1: Print two (2) copies of this notice — one for the tenant and one for your records.\n\n"
        "Step 2: Place the tenant's copy inside a sealed envelope. Do NOT leave the notice unsealed "
        "or folded and taped to the door. The statute requires a sealed envelope.\n\n"
        "Step 3: Post the sealed envelope conspicuously on the front door of the rental property. "
        "\"Conspicuously\" means it must be clearly visible — eye level on the door is recommended. "
        "Do not slide it under the door or leave it in a mailbox.\n\n"
        "Step 4: If your lease agreement specifies additional delivery methods (e.g., certified mail "
        "or email), you MUST also deliver the notice by those additional methods on the same day.\n\n"
        "Step 5: Document your service immediately. Take a dated photograph of the envelope posted "
        "on the door. Note the date and time of posting in writing.\n\n"
        "Step 6: Keep your copy of the notice and all documentation of service. You will need proof "
        "of service if you proceed to file a Dispossessory Affidavit.\n\n"
        "Step 7: Count THREE (3) BUSINESS DAYS from the date of posting (excluding Saturdays, Sundays, "
        "and federal holidays). If the tenant does not pay or vacate by the deadline, you may proceed "
        "to file a Dispossessory Affidavit at the Magistrate Court in the county where the property is located.\n\n"
        "IMPORTANT: Do not accept partial payment after serving this notice unless you intend to abandon "
        "the eviction. Consult an attorney before accepting any payment after this notice is served."
    ),
}

from jinja2 import Environment, FileSystemLoader, select_autoescape

base = Path(__file__).parent
templates_dir = base / "templates"
env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=select_autoescape(["html"]))
html = env.get_template("template_3day.html").render(**DUMMY_DATA)

html_path = base / "sample_output_3day.html"
html_path.write_text(html, encoding="utf-8")
print(f"Opened in browser: {html_path}")
print("To get a paginated PDF: File > Print > Save as PDF in your browser.")

subprocess.Popen(["explorer", str(html_path)])
