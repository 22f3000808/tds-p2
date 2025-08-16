
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import base64
import json
from PIL import Image
import pytesseract
import io
import base64

from tools import (
    is_csv, is_image, analyze_csv_bytes, analyze_image_bytes, call_aipipe_api,
    maybe_base64_to_image_response
)

app = FastAPI(title="Data Analyst Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/")
async def analyse_files_and_text(
    files: List[UploadFile] = File([]),
    file: Optional[UploadFile] = File(None),
    query: Optional[str] = Form(None)
):
    all_files: List[UploadFile] = []
    if file:
        all_files.append(file)
    if files:
        all_files.extend(files)

    txt_files, csv_files, img_files, other_files = [], [], [], []
    for f in all_files:
        if is_csv(f.content_type, f.filename):
            csv_files.append(f)
        elif is_image(f.content_type, f.filename):
            img_files.append(f)
        elif f.filename.lower().endswith(".txt"):
            txt_files.append(f)
        else:
            other_files.append(f)

    file_summaries = []
    effective_query = query or None

    # --- Handle text files ---
    texts = []
    for f in txt_files:
        raw = await f.read()
        try:
            txt = raw.decode("utf-8").strip()
            texts.append(txt)
            file_summaries.append({
                "filename": f.filename,
                "type": "text",
                "content_preview": txt[:2000]
            })
            if not effective_query:
                effective_query = txt
        except Exception as e:
            file_summaries.append({"filename": f.filename, "type": "text", "error": str(e)})

    # --- Handle CSV files ---
    if csv_files:
        for f in csv_files:
            contents = await f.read()
            try:
                csv_result = analyze_csv_bytes(contents)
                return csv_result  # directly return CSV analysis
            except Exception as e:
                file_summaries.append({"filename": f.filename, "type": "csv", "error": str(e)})

    # --- Handle Images ---
    images_b64 = []
    ocr_texts = []
    for f in img_files:
        raw = await f.read()
        try:
            img = Image.open(io.BytesIO(raw))
            ocr_text = pytesseract.image_to_string(img).strip()
            b64 = base64.b64encode(raw).decode("utf-8")

            images_b64.append(b64)
            if ocr_text:
                ocr_texts.append(ocr_text)

            file_summaries.append({
                "filename": f.filename,
                "type": "image",
                "ocr_text_preview": ocr_text[:200],
                "base64_len": len(b64)
            })
        except Exception as e:
            file_summaries.append({"filename": f.filename, "type": "image", "error": str(e)})

    # --- Build final query ---
    if not effective_query:
        effective_query = "\n\n".join(texts + ocr_texts) or "Please analyze these files."

    # --- Call AIPipe ---
    ai_reply = call_aipipe_api(prompt=effective_query, image_b64_list=images_b64)

    # Try parsing
    try:
        img_resp = maybe_base64_to_image_response(ai_reply)
        if img_resp:
            return img_resp
        try:
            return json.loads(ai_reply)
        except Exception:
            return {"answers": ai_reply}
    except Exception as e:
        return {"error": "Failed to process AIPipe response", "exception": str(e), "file_summaries": file_summaries}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

