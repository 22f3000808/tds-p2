from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import uvicorn
import os
import requests
import json

# Load environment variables
load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
if not AIPIPE_API_KEY:
    raise EnvironmentError("AIPIPE_API_KEY not set in .env")

AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"  # adjust as needed

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output Schema
class ResearchResponse(BaseModel):
    actual_answers: list[str]
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

# Helper to call AIPipe API
def call_aipipe_api(query: str) -> str:
    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-3.5-turbo",  # Or any model AIPipe supports
        "messages": [
            {"role": "system", "content": (
                "You are a Data Analyst that helps solve data analysis problems. "
                "Respond in this strict JSON format:\n"
                "{ \"actual_answers\": [\"...\"], \"topic\": \"...\", \"summary\": \"...\", \"sources\": [\"...\"], \"tools_used\": [\"...\"] }"
            )},
            {"role": "user", "content": query}
        ]
    }

    response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Endpoint
@app.post("/api/")
async def analyse_txt_file(
    file: Optional[UploadFile] = File(None),
    query: Optional[str] = Form(None)
):
    if file:
        contents = await file.read()
        query = contents.decode("utf-8")
    elif not query:
        return {"error": "No input provided. Please upload a file or submit a text query."}

    try:
        ai_response = call_aipipe_api(query)
        json_data = json.loads(ai_response)

        # Convert actual_answers to list if it's a string
        if isinstance(json_data.get("actual_answers"), str):
            json_data["actual_answers"] = [json_data["actual_answers"]]

        parsed = ResearchResponse.model_validate(json_data)
        return parsed

    except Exception as e:
        return {
            "error": "Failed to process response from AIPipe.",
            "raw": ai_response if 'ai_response' in locals() else None,
            "exception": str(e)
        }

# Run
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



# from fastapi import *
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from typing import Optional
# import uvicorn
# import os
# import requests

# # Load environment variables
# load_dotenv()

# AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
# if not AIPIPE_API_KEY:
#     raise EnvironmentError("AIPIPE_API_KEY not set in .env")

# AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"  # adjust as needed

# app = FastAPI()

# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Output Schema
# class ResearchResponse(BaseModel):
#     actual_answers: str
#     topic: str
#     summary: str
#     sources: list[str]
#     tools_used: list[str]

# # Helper to call AIPipe API
# def call_aipipe_api(query: str) -> str:
#     headers = {
#         "Authorization": f"Bearer {AIPIPE_API_KEY}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "model": "gpt-3.5-turbo",  # Or any model AIPipe supports
#         "messages": [
#             {"role": "system", "content": (
#                 "You are a Data Analyst that helps solve data analysis problems. "
#                 "Respond in this strict JSON format:\n"
#                 "{ \"actual_answers\": ..., \"topic\": ..., \"summary\": ..., \"sources\": [...], \"tools_used\": [...] }"
#             )},
#             {"role": "user", "content": query}
#         ]
#     }

#     response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
#     response.raise_for_status()  # will raise error if not 200
#     return response.json()["choices"][0]["message"]["content"]

# # Endpoint
# @app.post("/api/")
# async def analyse_txt_file(
#     file: Optional[UploadFile] = File(None),
#     query: Optional[str] = Form(None)
# ):
#     if file:
#         contents = await file.read()
#         query = contents.decode("utf-8")
#     elif not query:
#         return {"error": "No input provided. Please upload a file or submit a text query."}

#     try:
#         ai_response = call_aipipe_api(query)
#         parsed = ResearchResponse.model_validate_json(ai_response)
#         return parsed
#     except Exception as e:
#         return {
#             "error": "Failed to process response from AIPipe.",
#             "raw": ai_response if 'ai_response' in locals() else None,
#             "exception": str(e)
#         }

# # Run
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

