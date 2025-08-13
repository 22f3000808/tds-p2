from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Any, List
import uvicorn
import os
import requests
import json
import base64
import mimetypes

# Load environment variables
load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
if not AIPIPE_API_KEY:
    raise EnvironmentError("AIPIPE_API_KEY not set in .env")

AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Flexible output schema
class ResearchResponse(BaseModel):
    answers: Any  # Can be list, string, dict, etc.

# Helper: detect if file is image
def is_image(content_type: str, filename: str) -> bool:
    if content_type and content_type.startswith("image/"):
        return True
    guessed, _ = mimetypes.guess_type(filename)
    return guessed and guessed.startswith("image/")

# AIPipe call
def call_aipipe_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Data Analyst that helps solve data analysis problems. "
                    "Respond in this strict JSON format:\n"
                    "{ \"answers\": [\"...\"] } or { \"answers\": \"...\" }"
                ),
            },
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Endpoint that handles multiple/single files & text
@app.post("/api/")
async def analyse_files_and_text(
    files: List[UploadFile] = File([]),
    file: Optional[UploadFile] = File(None),
    query: Optional[str] = Form(None)
):
    prompts = []

    # Combine both single & multiple files into one list
    all_files = []
    if file:
        all_files.append(file)
    if files:
        all_files.extend(files)

    print(f"DEBUG: Received {len(all_files)} files")
    print(f"DEBUG: Query: {query}")

    # Process uploaded files
    for f in all_files:
        contents = await f.read()
        if is_image(f.content_type, f.filename):
            encoded = base64.b64encode(contents).decode("utf-8")
            prompts.append(f"Image file '{f.filename}' (base64): {encoded}")
        else:
            try:
                decoded_text = contents.decode("utf-8")
                prompts.append(f"Text/Other file '{f.filename}':\n{decoded_text}")
            except UnicodeDecodeError:
                encoded = base64.b64encode(contents).decode("utf-8")
                prompts.append(f"Binary file '{f.filename}' in base64: {encoded}")

    # Include plain text query if provided
    if query:
        prompts.append(f"User query:\n{query}")

    if not prompts:
        return {"error": "No files or query provided."}

    # Merge into one combined prompt
    final_prompt = "\n\n".join(prompts)

    try:
        ai_response = call_aipipe_api(final_prompt)
        json_data = json.loads(ai_response)

        # Ensure answers is always a list
        if isinstance(json_data.get("answers"), str):
            json_data["answers"] = [json_data["answers"]]

        parsed = ResearchResponse.model_validate(json_data)
        return parsed

    except Exception as e:
        return {
            "error": "Failed to process response from AIPipe.",
            "raw_response": ai_response if 'ai_response' in locals() else None,
            "exception": str(e)
        }

# Run locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



# Original code for reference
# Uncomment the following lines to use the original code


# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from typing import Optional, Any
# import uvicorn
# import os
# import requests
# import json
# import base64

# # Load environment variables
# load_dotenv()

# AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
# if not AIPIPE_API_KEY:
#     raise EnvironmentError("AIPIPE_API_KEY not set in .env")

# AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"

# app = FastAPI()

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Flexible output schema
# class ResearchResponse(BaseModel):
#     answers: Any  # Can be list, string, dict, etc.

# # AIPipe call
# def call_aipipe_api(prompt: str) -> str:
#     headers = {
#         "Authorization": f"Bearer {AIPIPE_API_KEY}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are a Data Analyst that helps solve data analysis problems. "
#                     "Respond in this strict JSON format:\n"
#                     "{ \"answers\": [\"...\"] } or { \"answers\": \"...\" }"
#                 ),
#             },
#             {"role": "user", "content": prompt}
#         ]
#     }

#     response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
#     response.raise_for_status()
#     return response.json()["choices"][0]["message"]["content"]

# # Endpoint
# @app.post("/api/")
# async def analyse_txt_file(
#     file: Optional[UploadFile] = File(None),
#     query: Optional[str] = Form(None)
# ):
#     if file:
#         contents = await file.read()

#         # Detect image and convert to base64
#         if file.content_type and file.content_type.startswith("image/"):
#             encoded = base64.b64encode(contents).decode("utf-8")
#             query = f"Please analyze this image in base64 format:\n{encoded}"
#         else:
#             query = contents.decode("utf-8")

#     elif not query:
#         return {"error": "No input provided. Please upload a file or submit a text query."}

#     try:
#         ai_response = call_aipipe_api(query)
#         json_data = json.loads(ai_response)

#         # If "answers" is string, convert to list for uniform handling
#         if isinstance(json_data.get("answers"), str):
#             json_data["answers"] = [json_data["answers"]]

#         parsed = ResearchResponse.model_validate(json_data)
#         return parsed

#     except Exception as e:
#         return {
#             "error": "Failed to process response from AIPipe.",
#             "raw_response": ai_response if 'ai_response' in locals() else None,
#             "exception": str(e)
#         }

# # Run locally
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
