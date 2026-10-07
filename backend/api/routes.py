from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.database import get_db, SessionLocal
from db.models import Tender, Bidder, Criterion, Verdict, AuditLog, Vendor
from workers.tasks import process_tender_async, evaluate_bidder_async
import shutil
import os
import json
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_ROOT", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

def log_event(db: Session, entity_type: str, entity_id: int, action: str, actor: str = "api", reason: str = None, old_value=None, new_value=None):
    db.add(AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        actor=actor,
        reason=reason
    ))

async def save_upload_chunked(upload: UploadFile, dest_path: str) -> int:
    size = 0
    with open(dest_path, "wb") as f:
        while True:
            chunk = await upload.read(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                f.close()
                os.remove(dest_path)
                raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")
            f.write(chunk)
    return size

def compute_bidder_score(verdicts: list, criteria: list) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    criteria_map = {c["id"]: c for c in criteria}
    for v in verdicts:
        c = criteria_map.get(v.criterion_id)
        if not c: continue
        weight = c.get("weight", 1.0)
        score = {"pass": 1.0, "review_needed": 0.5, "fail": 0.0}.get(v.status, 0.0)
        confidence = v.confidence or 0.0
        weighted_sum += score * weight * confidence
        total_weight += weight
    return round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

def is_disqualified(verdicts: list, criteria: list) -> bool:
    criteria_map = {c["id"]: c for c in criteria}
    for v in verdicts:
        c = criteria_map.get(v.criterion_id)
        if c and c.get("type") == "mandatory" and v.status == "fail":
            return True
    return False

@router.post("/upload/tender")
async def upload_tender(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    new_tender = Tender(title=file.filename, status="uploaded")
    db.add(new_tender)
    db.commit()
    db.refresh(new_tender)

    tender_dir = os.path.join(UPLOAD_DIR, f"tender_{new_tender.id}")
    os.makedirs(tender_dir, exist_ok=True)
    file_path = os.path.join(tender_dir, f"{uuid.uuid4().hex}{ext}")

    size = await save_upload_chunked(file, file_path)
    new_tender.file_path = file_path
    log_event(db, "tender", new_tender.id, "tender_uploaded", new_value={"size": size})
    db.commit()

    process_tender_async.delay(new_tender.id)
    return {"id": new_tender.id, "status": "processing"}

@router.get("/tenders")
async def list_tenders(db: Session = Depends(get_db)):
    return db.query(Tender).all()

@router.get("/tenders/{id}/criteria")
async def get_criteria(id: int, db: Session = Depends(get_db)):
    return db.query(Criterion).filter(Criterion.tender_id == id).all()

@router.post("/upload/bidder")
async def upload_bidder(tender_id: int = Form(...), vendor_name: str = Form(...), files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
    if not vendor:
        vendor = Vendor(name=vendor_name)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

    new_bidder = Bidder(tender_id=tender_id, vendor_id=vendor.id, status="uploaded")
    db.add(new_bidder)
    db.commit()
    db.refresh(new_bidder)

    bidder_dir = os.path.join(UPLOAD_DIR, f"bidder_{new_bidder.id}")
    os.makedirs(bidder_dir, exist_ok=True)
    for f in files:
        f_path = os.path.join(bidder_dir, f.filename)
        await save_upload_chunked(f, f_path)

    new_bidder.folder_path = bidder_dir
    db.commit()
    evaluate_bidder_async.delay(new_bidder.id)
    return {"id": new_bidder.id, "status": "processing"}

@router.get("/tenders/{id}/scorecard")
async def get_scorecard(id: int, db: Session = Depends(get_db)):
    bidders = db.query(Bidder).filter(Bidder.tender_id == id).all()
    criteria = db.query(Criterion).filter(Criterion.tender_id == id).all()
    c_dicts = [{"id": c.id, "text": c.text, "type": c.type, "weight": c.weight} for c in criteria]
    
    matrix = []
    for b in bidders:
        verdicts = db.query(Verdict).filter(Verdict.bidder_id == b.id).all()
        matrix.append({
            "bidder_id": b.id,
            "vendor_name": b.vendor.name,
            "score": compute_bidder_score(verdicts, c_dicts),
            "disqualified": is_disqualified(verdicts, c_dicts),
            "verdicts": verdicts
        })
    return {"tender_id": id, "criteria": criteria, "bidders": matrix}

@router.get("/tenders/{id}/stream")
async def stream_status(id: int):
    async def event_generator():
        while True:
            db = SessionLocal()
            try:
                tender = db.query(Tender).filter(Tender.id == id).first()
                if not tender: break
                bidders = db.query(Bidder).filter(Bidder.tender_id == id).all()
                yield f"data: {json.dumps({'tender_status': tender.status, 'bidders': [{'id': b.id, 'status': b.status} for b in bidders]})}\n\n"
                if tender.status in ["completed", "failed"]: break
            finally: db.close()
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.patch("/verdicts/{id}/review")
async def review_verdict(id: int, status: str, reason: str, actor: str, db: Session = Depends(get_db)):
    v = db.query(Verdict).filter(Verdict.id == id).first()
    if not v: raise HTTPException(404, "Verdict not found")
    v.status = status
    v.is_human_reviewed = True
    log_event(db, "verdict", id, "human_review", actor=actor, reason=reason)
    db.commit()
    return {"status": "ok"}

@router.get("/tenders/{id}/audit")
async def get_audit(id: int, db: Session = Depends(get_db)):
    return db.query(AuditLog).filter(AuditLog.entity_id == id).all()
