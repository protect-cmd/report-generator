"""Smoke-tests all three templates with dummy data."""
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

base = Path(__file__).parent
env = Environment(
    loader=FileSystemLoader(str(base / "templates")),
    autoescape=select_autoescape(["html"]),
)

# ── 3060day ──────────────────────────────────────────────────────────────────
data_3060 = {
    "notice_date": "April 28, 2026",
    "notice_type_label": "60-Day Notice to Vacate",
    "statute_reference": "O.C.G.A. § 44-7-7",
    "is_month_to_month": True,
    "landlord_name": "Zeann Co",
    "landlord_address": "123 Main St, Atlanta, Georgia 30301",
    "tenant_names": ["Chris Movado"],
    "property_address": "123 Main St, Atlanta, Fulton County, Georgia 30301",
    "move_out_date": "June 27, 2026",
    "body_paragraphs": [
        (
            "NOTICE IS HEREBY GIVEN to Chris Movado that the month-to-month tenancy for the "
            "above-referenced premises is hereby terminated effective sixty (60) calendar days "
            "from the date of this notice. You are required to vacate and surrender possession "
            "of the premises on or before June 27, 2026."
        ),
        (
            "This notice is issued pursuant to O.C.G.A. § 44-7-7. No cause for termination is "
            "required under Georgia law for a month-to-month tenancy. You are expected to remove "
            "all personal property and return possession of the premises in a clean and undamaged "
            "condition on or before the move-out date stated above."
        ),
        (
            "If you fail to vacate by the required date, the Landlord will file a Dispossessory "
            "Affidavit with the Magistrate Court of Fulton County, Georgia, and pursue all "
            "available legal remedies."
        ),
    ],
    "serving_instructions": (
        "HOW TO SERVE THIS NOTICE IN GEORGIA (O.C.G.A. § 44-7-7 — Best Practice):\n\n"
        "Step 1: Print three (3) copies of this notice.\n\n"
        "Step 2: CERTIFIED MAIL — Mail one copy via USPS Certified Mail with Return Receipt "
        "Requested to the tenant at the rental property address. Keep the receipt and green card.\n\n"
        "Step 3: FIRST-CLASS MAIL — Mail a second copy via regular first-class mail on the same day.\n\n"
        "Step 4: DOOR POSTING — Post a third copy in a sealed envelope on the front door on the same day.\n\n"
        "Step 5: Document everything. Photograph the posted notice. Write down dates and tracking numbers.\n\n"
        "Step 6: Count sixty (60) CALENDAR DAYS from the date of service. Weekends and holidays are included.\n\n"
        "IMPORTANT: Accepting rent after serving this notice may constitute renewal of the tenancy "
        "and could invalidate this notice. Consult an attorney before accepting any payment."
    ),
}

html_3060 = env.get_template("template_3060day.html").render(**data_3060)
out_3060 = base / "sample_output_3060day.html"
out_3060.write_text(html_3060, encoding="utf-8")
print(f"3060day: {out_3060}")

# ── UD ────────────────────────────────────────────────────────────────────────
data_ud = {
    "notice_date": "April 28, 2026",
    "filing_package_label": "Georgia Dispossessory Filing Package",
    "doc2_label": "Dispossessory Affidavit",
    "doc3_label": "Affidavit of Service",
    "court_descriptor": "Magistrate Court",
    "state": "Georgia",
    "county": "Fulton",
    "statute_reference": "O.C.G.A. § 44-7-49 through § 44-7-59",
    "landlord_name": "Zeann Co",
    "landlord_address": "123 Main St, Atlanta, Georgia 30301",
    "tenant_names": ["Chris Movado", "Maria Movado"],
    "property_address": "123 Main St, Atlanta, Fulton County, Georgia 30301",
    "reason_for_eviction": "Nonpayment",
    "lease_start_date": "January 1, 2025",
    "lease_end_date": None,
    "is_month_to_month": True,
    "monthly_rent": "$2,000.00",
    "underlying_notice": {
        "notice_type_label": "Three (3)-Day Notice to Pay or Vacate",
        "statute_reference": "O.C.G.A. § 44-7-50(c), as amended by 2024 Ga. Laws Act 392",
        "deadline_date": "Thursday, May 1, 2026",
        "total_amount_owed": "$4,000.00",
        "total_amount_words": "FOUR THOUSAND DOLLARS AND ZERO CENTS",
        "itemized_charges": [
            {"description": "Past Due Rent — March 2026", "amount": "$2,000.00"},
            {"description": "Past Due Rent — April 2026", "amount": "$2,000.00"},
        ],
        "violation_description": None,
        "body_paragraphs": [
            (
                "NOTICE IS HEREBY GIVEN to Chris Movado and Maria Movado that you are currently "
                "in default of your lease agreement due to failure to pay rent when due. You are "
                "hereby demanded to pay the full amount owed or vacate the premises within THREE "
                "(3) BUSINESS DAYS from the date of this notice."
            ),
        ],
    },
    "affidavit": {
        "grounds": [
            "Failure to pay rent in the total amount of $4,000.00, representing two (2) months "
            "of unpaid rent at $2,000.00 per month.",
            "Tenant(s) failed to comply with the prior demand for possession served on April 28, 2026.",
        ],
        "prior_demand_date": "April 28, 2026",
        "prior_demand_method": "3-Day Notice to Pay or Vacate posted on door per O.C.G.A. § 44-7-50(d)",
        "amount_owed": "$4,000.00",
        "body_paragraphs": [
            (
                "1. I am the Landlord / authorized agent of the Landlord for the premises located "
                "at 123 Main St, Atlanta, Fulton County, Georgia 30301 (the \"Premises\")."
            ),
            (
                "2. Chris Movado and Maria Movado (\"Tenant\") entered into a lease agreement for "
                "the Premises commencing January 1, 2025, at a monthly rent of $2,000.00."
            ),
            (
                "3. Tenant has failed to pay rent for March 2026 and April 2026, resulting in a "
                "total arrearage of $4,000.00 as of the date of this Affidavit."
            ),
            (
                "4. On April 28, 2026, Affiant made a written demand for payment or possession "
                "by serving a 3-Day Notice to Pay or Vacate per O.C.G.A. § 44-7-50(c). "
                "Tenant has refused or failed to comply."
            ),
        ],
    },
    "filing_instructions": (
        "FULTON COUNTY MAGISTRATE COURT — SPECIFIC INSTRUCTIONS:\n\n"
        "Location: 185 Central Ave SW, Suite TG100, Atlanta, GA 30303\n"
        "Hours: Monday–Friday, 8:30 AM – 5:00 PM\n\n"
        "Filing fee: Approximately $80 for the Dispossessory Affidavit plus $35 per named defendant "
        "for Sheriff service. Confirm exact fees with the clerk before arriving.\n\n"
        "Fulton County allows online filing through their e-filing portal for represented parties. "
        "Self-represented landlords should file in person at the clerk's window.\n\n"
        "After filing, the Sheriff's Civil Division will serve the Summons and Affidavit on the tenant. "
        "The tenant has 7 calendar days from service to file an answer."
    ),
}

html_ud = env.get_template("template_ud.html").render(**data_ud)
out_ud = base / "sample_output_ud.html"
out_ud.write_text(html_ud, encoding="utf-8")
print(f"UD:      {out_ud}")

subprocess.Popen(["explorer", str(out_3060)])
subprocess.Popen(["explorer", str(out_ud)])
print("\nBoth opened in browser. File > Print > Save as PDF for paginated preview.")
