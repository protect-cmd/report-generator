import logging
import os
import tempfile
import traceback

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from models.deliver_request import DeliverRequest
from models.intake_form import IntakeForm
from services.drive_service import build_drive_service, create_client_folder, download_pdf, file_id_from_url, get_shareable_url, upload_pdf
from services.email_service import send_client_delivery
from services.ghl_service import add_contact_note, move_opportunity_stage, update_contact_custom_field
from services.llm_service import generate_document
from services.pdf_service import generate_pdf
from utils.prompt_loader import load_prompt

load_dotenv(Path(__file__).parent / ".env", override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Eviction Command Document Generator")


@app.post("/generate")
async def generate(form: IntakeForm):
    form_data = form.model_dump()
    logger.info("Incoming form data: %s", form_data)

    # 1. Load prompt — 400 if state/notice_type not supported
    try:
        populated_prompt = load_prompt(form.state, form.notice_type, form_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Generate document via LLM — 500 if fails
    try:
        document_data = generate_document(populated_prompt)
    except Exception:
        logger.error("LLM generation failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Document generation failed")

    # 3. Convert to PDF — 500 if fails
    from utils.prompt_loader import NOTICE_TYPE_MAP  # noqa: PLC0415
    notice_key = NOTICE_TYPE_MAP.get(form.notice_type, "3day")
    pdf_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        generate_pdf(document_data, pdf_path, notice_key)
    except Exception:
        logger.error("PDF generation failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="PDF generation failed")

    # 4. Upload to Google Drive — 500 if fails, GHL not called
    try:
        drive_service = build_drive_service()
        parent_folder_id = os.environ.get("GOOGLE_DRIVE_PARENT_FOLDER_ID")
        folder_name = f"{form.contact_id}_{form.full_name}_{form.notice_type}"
        client_folder_id = create_client_folder(drive_service, parent_folder_id, folder_name)
        file_name = (
            f"{form.notice_type.replace(' ', '_')}"
            f"_{form.tenant_full_legal_name.replace(' ', '_')}.pdf"
        )
        file_id = upload_pdf(drive_service, pdf_path, client_folder_id, file_name)
        drive_url = get_shareable_url(file_id)
    except Exception as e:
        print(f"\n=== DRIVE ERROR ===\n{traceback.format_exc()}\n===================\n", flush=True)
        raise HTTPException(status_code=500, detail=f"Drive upload failed: {e}")
    finally:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except OSError:
                pass

    # 5. Save Drive URL to GHL custom field so Workflow 3 can pass it to /deliver
    ghl_api_key = os.environ.get("GHL_API_KEY")
    try:
        update_contact_custom_field(ghl_api_key, form.contact_id, "drive_document_url", drive_url)
    except Exception:
        logger.warning("GHL custom field update failed:\n%s", traceback.format_exc())

    # 6. Notify GHL — log warning and continue on failure (document is in Drive)
    stage_id = os.environ.get("GHL_PENDING_REVIEW_STAGE_ID")
    location_id = os.environ.get("GHL_LOCATION_ID")
    pipeline_id = os.environ.get("GHL_PIPELINE_ID")

    try:
        move_opportunity_stage(ghl_api_key, form.contact_id, pipeline_id, stage_id, location_id)
    except Exception:
        logger.warning("GHL stage move failed:\n%s", traceback.format_exc())

    try:
        add_contact_note(ghl_api_key, form.contact_id, drive_url, form.notice_type, form.state, form.county)
    except Exception:
        logger.warning("GHL note failed:\n%s", traceback.format_exc())

    return JSONResponse({"status": "success", "drive_url": drive_url})


@app.post("/deliver")
async def deliver(req: DeliverRequest):
    # 1. Download PDF from Drive
    try:
        drive_service = build_drive_service()
        file_id = file_id_from_url(req.drive_url)
        pdf_bytes = download_pdf(drive_service, file_id)
    except Exception:
        logger.error("Drive download failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve document from Drive")

    # 2. Send client delivery email
    pdf_filename = f"{req.notice_type.replace(' ', '_')}_{req.property_address.replace(' ', '_')}.pdf"
    sent = send_client_delivery(
        client_email=req.email,
        client_name=req.full_name,
        notice_type=req.notice_type,
        state=req.state,
        county=req.county,
        property_address=req.property_address,
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_filename,
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send delivery email")

    logger.info("Document delivered to %s for contact %s", req.email, req.contact_id)
    return JSONResponse({"status": "delivered", "contact_id": req.contact_id})
