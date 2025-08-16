# tools.py
"""
Helper utilities for the Data Analyst Agent:
- CSV analysis functions (analyze_csv_bytes) returning the grader schema
- Image OCR and lightweight image analysis (analyze_image_bytes)
- Utilities: is_csv, is_image, fig_to_base64_png_uri, pick_* heuristics
- call_aipipe_api for fallback LLM processing
"""


import io
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import io
import base64
import math
import mimetypes
import os
import requests

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pandas.api.types import CategoricalDtype
from PIL import Image, ImageStat
import pytesseract

from dotenv import load_dotenv
load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
AIPIPE_API_URL = os.getenv("AIPIPE_API_URL", "https://aipipe.org/openrouter/v1/chat/completions")

if not AIPIPE_API_KEY:
    # we won't raise here to allow unit tests, but callers should check
    pass



def is_image(content_type: Optional[str], filename: str) -> bool:
    # Common image extensions (lowercase)
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"}
    
    # Check content type if provided
    if content_type and content_type.lower().startswith("image/"):
        return True
    
    # Check MIME type based on filename
    guessed, _ = mimetypes.guess_type(filename)
    if guessed and guessed.startswith("image/"):
        return True
    
    # Fallback: check file extension manually
    for ext in image_extensions:
        if filename.lower().endswith(ext):
            return True
    
    return False



def is_csv(content_type: Optional[str], filename: str) -> bool:
    """
    Return True only for actual CSV/TSV files.
    - Prefer file extension check (.csv, .tsv)
    - Accept common CSV/TSV MIME types
    - DO NOT treat 'text/plain' as CSV
    """
    name = (filename or "").lower()
    if name.endswith(".csv") or name.endswith(".tsv"):
        return True

    ct = (content_type or "").lower()
    csv_mimes = {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",          # many browsers use this for .csv
        "text/tab-separated-values",
        "application/tab-separated-values",
    }
    return ct in csv_mimes



def fig_to_base64_png_uri(fig, max_bytes: int = 100_000) -> str:
    """
    Save a matplotlib figure to PNG base64 data URI, trying multiple DPIs to keep under max_bytes.
    """
    last_data = None
    for dpi in (150, 120, 110, 100, 90, 80):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.1)
        data = buf.getvalue()
        last_data = data
        if len(data) <= max_bytes:
            b64 = base64.b64encode(data).decode("utf-8")
            return f"data:image/png;base64,{b64}"
    b64 = base64.b64encode(last_data).decode("utf-8")
    return f"data:image/png;base64,{b64}"





def analyze_csv_bytes(csv_bytes: bytes) -> Dict[str, Any]:
    """
    Generic CSV analyzer (works for any kind of data).
    Returns:
      - basic info: shape, columns, dtypes
      - summary stats for numeric columns
      - top categories for categorical columns
      - detected datetime ranges
      - correlation heatmap (if multiple numeric cols)
      - example row preview
    """
    df = pd.read_csv(io.BytesIO(csv_bytes))

    results: Dict[str, Any] = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_summary": {},
        "categorical_summary": {},
        "datetime_summary": {},
        "preview": df.head(5).to_dict(orient="records"),
        "plots": {}
    }

    # --- Numeric columns ---
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    for col in num_cols:
        results["numeric_summary"][col] = {
            "count": int(df[col].count()),
            "mean": float(df[col].mean()) if df[col].count() > 0 else None,
            "median": float(df[col].median()) if df[col].count() > 0 else None,
            "std": float(df[col].std()) if df[col].count() > 0 else None,
            "min": float(df[col].min()) if df[col].count() > 0 else None,
            "max": float(df[col].max()) if df[col].count() > 0 else None,
        }

        # Histogram plot
        fig = plt.figure(figsize=(6, 4))
        df[col].dropna().hist(bins=20)
        plt.title(f"Histogram of {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        results["plots"][f"{col}_hist"] = fig_to_base64_png_uri(fig)
        plt.close(fig)

    # --- Categorical columns ---
    cat_cols = [c for c in df.columns if df[c].dtype == object or isinstance(df[c].dtype, CategoricalDtype)]
    for col in cat_cols:
        vc = df[col].value_counts().head(10)
        results["categorical_summary"][col] = vc.to_dict()

        # Bar chart of top categories
        if not vc.empty:
            fig = plt.figure(figsize=(6, 4))
            vc.plot(kind="bar")
            plt.title(f"Top categories in {col}")
            plt.xlabel(col)
            plt.ylabel("Count")
            results["plots"][f"{col}_bar"] = fig_to_base64_png_uri(fig)
            plt.close(fig)

    # --- Datetime columns ---
    for col in df.columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() > 0.7:
                results["datetime_summary"][col] = {
                    "min": str(parsed.min()),
                    "max": str(parsed.max()),
                }
        except Exception:
            pass

    # --- Correlation heatmap ---
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig = plt.figure(figsize=(6, 5))
        plt.imshow(corr, cmap="coolwarm", interpolation="none")
        plt.colorbar()
        plt.xticks(range(len(num_cols)), num_cols, rotation=45, ha="right")
        plt.yticks(range(len(num_cols)), num_cols)
        plt.title("Correlation Heatmap")
        results["plots"]["correlation_heatmap"] = fig_to_base64_png_uri(fig)
        plt.close(fig)

    return results


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Basic image analysis:
    - Runs OCR (pytesseract) and returns extracted text.
    - Returns basic image stats (size, mode, mean brightness).
    - Returns small thumbnail as base64 URI (helps LLM or UI).
    """
    try:
        im = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {"error": f"Failed to open image: {e}"}

    # Basic image metadata
    width, height = im.size
    mode = im.mode

    # Brightness mean
    try:
        stat = ImageStat.Stat(im.convert("L"))
        mean_brightness = float(stat.mean[0])
    except Exception:
        mean_brightness = None

    # OCR (text extraction)
    try:
        ocr_text = pytesseract.image_to_string(im)
    except Exception as e:
        ocr_text = f"[OCR error: {e}]"

    # Thumbnail (small)
    try:
        thumb = im.copy()
        thumb.thumbnail((400, 400))
        buf = io.BytesIO()
        thumb.save(buf, format="PNG")
        thumb_b = buf.getvalue()
        thumb_b64 = base64.b64encode(thumb_b).decode("utf-8")
        thumb_uri = f"data:image/png;base64,{thumb_b64}"
    except Exception:
        thumb_uri = None

    return {
        "width": width,
        "height": height,
        "mode": mode,
        "mean_brightness": mean_brightness,
        "ocr_text": ocr_text,
        "thumbnail": thumb_uri,
    }


def ocr_image_bytes(contents: bytes) -> str:
    """Extract text from image using pytesseract."""
    img = Image.open(io.BytesIO(contents))
    text = pytesseract.image_to_string(img)
    return text.strip()


def maybe_base64_to_image_response(ai_reply: str):
    """
    If ai_reply looks like base64-encoded PNG/JPEG, return StreamingResponse with image.
    Otherwise return None.
    """
    try:
        # base64 strings often start with 'iVBORw0' (PNG) or '/9j/' (JPEG)
        if ai_reply.strip().startswith(("iVBOR", "/9j/")):
            img_bytes = base64.b64decode(ai_reply)
            return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
    except Exception:
        pass
    return None


def call_aipipe_api(prompt: str, image_b64_list: Optional[List[str]] = None, model: str = "gpt-3.5-turbo") -> str:
    if not AIPIPE_API_KEY:
        raise EnvironmentError("AIPIPE_API_KEY not configured in environment")

    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json",
    }

    user_content = [{"type": "text", "text": prompt}]
    if image_b64_list:
        for b64 in image_b64_list:
            user_content.append({"type": "image_base64", "image_base64": b64})

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Data Analyst that helps solve data analysis problems. "
                "Extract insights, perform analysis, image processing, and other tasks. "
                "Respond in this strict JSON format:\n"
                "{ \"answers\": [\"...\"] } or { \"answers\": \"...\" }"
            ),
        },
        {"role": "user", "content": user_content},
    ]

    payload = {"model": model, "messages": messages}
    resp = requests.post(AIPIPE_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)



# def call_aipipe_api(prompt: str, image_b64: str , model: str = "gpt-3.5-turbo") -> str:
'''
def call_aipipe_api(prompt: str, image_b64: str , model: str = "gpt-3.5-turbo") -> str:
    """
    Sends a prompt to AIPipe and returns the assistant content.
    Caller must ensure AIPIPE_API_KEY is present in env.
    """
    if not AIPIPE_API_KEY:
        raise EnvironmentError("AIPIPE_API_KEY not configured in environment")

    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json",
    }

    if image_b64:
        messages = [
            {"role": "system", "content": 
                "You are a Data Analyst that helps solve data analysis problems. "
                "Extract insights, perform analysis,image processing, and other tasks."
                "and Respond in this strict JSON format:\n"
                "{ \"answers\": [\"...\"] } or { \"answers\": \"...\" }"},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_base64", "image_base64": image_b64}
                # {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]}
        ]
    else:
        messages = [
            {"role": "system", "content": 
                "You are a Data Analyst that helps solve data analysis problems. "
                "Extract insights, perform analysis,image processing, and other tasks."
                "and Respond in this strict JSON format:\n"
                "{ \"answers\": [\"...\"] } or { \"answers\": \"...\" }"},
            {"role": "user", "content": prompt}
        ]

    payload = {
        "model": model,
        "messages": messages,
        # keep other fields adjustable if needed
    }
    resp = requests.post(AIPIPE_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Best-effort extract
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)
'''

# from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
# from langchain_community.utilities import WikipediaAPIWrapper
# from langchain.tools import Tool
# from datetime import datetime

# def save_to_txt(data: str, filename: str = "research_output.txt"):
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"

#     with open(filename, "a", encoding="utf-8") as f:
#         f.write(formatted_text)
    
#     return f"Data successfully saved to {filename}"

# save_tool = Tool(
#     name="save_text_to_file",
#     func=save_to_txt,
#     description="Saves structured research data to a text file.",
# )

# search = DuckDuckGoSearchRun()
# search_tool = Tool(
#     name="search",
#     func=search.run,
#     description="Search the web for information",
# )

# api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
# wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
