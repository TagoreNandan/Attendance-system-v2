from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from services.sheets import get_parent_number, create_daily_sheet, list_all_sheets, get_sheet_data
from services.caller import trigger_call
from services.sheets import get_student_details

import requests
import os
from dotenv import load_dotenv
load_dotenv()

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from faster_whisper import WhisperModel
from difflib import get_close_matches
from datetime import datetime
from twilio.twiml.voice_response import VoiceResponse
from urllib.parse import quote, parse_qs

# -------------------- INIT --------------------
call_results = {}
app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("frontend/index.html")

@app.get("/results")
def get_results():
    return call_results

# -------------------- SHEETS API --------------------

@app.get("/api/worksheets")
def api_list_worksheets():
    return list_all_sheets()

@app.get("/api/worksheets/{title}")
def api_get_worksheet(title: str):
    return get_sheet_data(title)

# -------------------- GOOGLE SHEETS --------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client = gspread.authorize(creds)

# -------------------- MODEL --------------------

model = WhisperModel("base", compute_type="int8")

# -------------------- INTENT DETECTION --------------------

def detect_reason(text):
    text = text.lower()

    sick_keywords = [
        "fever", "sick", "ill", "hospital", "doctor",
        "medicine", "vomit", "cough", "cold", "headache"
    ]

    travel_keywords = [
        "travel", "travelling", "journey", "trip",
        "out of station", "bus", "train",
        "flight", "village", "native", "tour", "vacation"
    ]

    function_keywords = [
        "marriage", "wedding", "function",
        "ceremony", "festival", "pooja"
    ]

    busy_keywords = [
        "busy", "call later", "not free", "later",
        "in a meeting", "right now busy"
    ]

    not_interested_keywords = [
        "not interested", "don't call", "stop calling",
        "wrong number", "not needed"
    ]

    callback_keywords = [
        "call back", "call tomorrow", "call in evening",
        "call after", "later today"
    ]

    scores = {
        "SICK": 0,
        "TRAVEL": 0,
        "FUNCTION": 0,
        "BUSY": 0,
        "NOT_INTERESTED": 0,
        "CALLBACK": 0
    }

    def count_matches(keywords, label):
        for word in keywords:
            if word in text:
                scores[label] += 1

    count_matches(sick_keywords, "SICK")
    count_matches(travel_keywords, "TRAVEL")
    count_matches(function_keywords, "FUNCTION")
    count_matches(busy_keywords, "BUSY")
    count_matches(not_interested_keywords, "NOT_INTERESTED")
    count_matches(callback_keywords, "CALLBACK")

    # 🔥 Priority override (important)
    if scores["NOT_INTERESTED"] > 0:
        return "NOT_INTERESTED"

    if scores["CALLBACK"] > 0:
        return "CALLBACK"

    if scores["BUSY"] > 0:
        return "BUSY"

    # Otherwise pick best match
    best_reason = max(scores, key=scores.get)

    if scores[best_reason] == 0:
        return "OTHER"

    return best_reason

# -------------------- START CALLS --------------------

@app.post("/start-calls")
def start_calls(data: dict):

    subject = data.get("subject") or "UNKNOWN"
    department = (data.get("department") or "UNKNOWN").strip()

    # 🔥 Normalize section (e.g., "Section A" → "A")
    section_raw = data.get("section") or "UNKNOWN"
    section = section_raw.replace("Section", "").strip()

    # 🔥 Normalize year (e.g., "B.Tech 3rd Year" → "3")
    year_raw = str(data.get("year") or "").strip().lower()
    # ✅ Robust year extraction
    if "1" in year_raw:
        year = "1"
    elif "2" in year_raw:
        year = "2"
    elif "3" in year_raw:
        year = "3"
    elif "4" in year_raw:
        year = "4"
    else:
        year = ""
    
    print("YEAR RAW:", year_raw)
    print("NORMALIZED YEAR:", year)
    print("FULL DATA RECEIVED:", data)

    rolls = data.get("rolls") or []

    results = []

    for roll in rolls:

        student = get_student_details(roll)

        # ❌ Invalid roll
        if not student:
            results.append({"roll": roll, "status": "Invalid Roll"})
            continue

        # ❌ Missing phone
        if not student.get("phone"):
            results.append({"roll": roll, "status": "No Number"})
            continue

        # 🔍 Normalize sheet values too (safety)
        student_dept = str(student.get("department", "")).strip()
        student_section = str(student.get("section", "")).strip()
        student_year = str(student.get("year", "")).strip()

        # ❌ Validation mismatch
        if (
            student_dept != department or
            student_section != section or
            student_year != year
        ):
            print("❌ MISMATCH DEBUG:")
            print("UI:", department, section, year, "| RAW:", year_raw)
            print("SHEET:", student_dept, student_section, student_year)

            results.append({
                "roll": roll,
                "status": "Mismatch (Dept/Section/Year)"
            })
            continue

        # ✅ VALID → trigger call
        phone = student["phone"]

        trigger_call(phone, roll, subject, section)

        call_results[roll] = {
            "status": "Calling",
            "reason": "Pending",
            "transcript": "",
            "retry_count": 0
        }

        results.append({"roll": roll, "status": "Calling"})

    return {"results": results}

# -------------------- AUDIO --------------------

@app.get("/question-audio")
def question_audio():
    return FileResponse("question.mp3", media_type="audio/mpeg")

# -------------------- RECORDING --------------------

@app.post("/recording")
async def recording(request: Request):

    print("🔥 RECORDING HIT")

    body = await request.body()
    parsed = parse_qs(body.decode())

    recording_url = parsed.get("RecordingUrl", [None])[0]

    if not recording_url:
        print("❌ Recording URL NOT FOUND")
        return Response(content="<Response></Response>", media_type="application/xml")

    print("🎙 Recording URL:", recording_url)

    roll = request.query_params.get("roll")
    subject = request.query_params.get("subject") or "UNKNOWN"
    section = request.query_params.get("section") or "UNKNOWN"
    department = request.query_params.get("department") or "UNKNOWN"

    date = datetime.now().strftime("%Y-%m-%d")
    sheet_name = f"{date}_{department}_{subject}_{section}"

    print("📊 WRITING TO SHEET:", sheet_name)

    # Download audio
    audio = requests.get(
        recording_url + ".wav",
        auth=(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
    )

    with open("temp.wav", "wb") as f:
        f.write(audio.content)

    # Transcribe
    segments, _ = model.transcribe("temp.wav")
    text = "".join([seg.text for seg in segments]).strip()

    print("🔥 TRANSCRIPT:", text)

    reason = detect_reason(text)

    # ✅ UPDATE UI DATA
    call_results[roll] = {
        "status": "Completed",
        "reason": reason,
        "transcript": text
    }

    # Save to sheet
    sheet = create_daily_sheet(sheet_name)
    print("APPENDING:", [roll, subject, section, department, reason])
    sheet.append_row([
    roll,
    subject,
    section,
    department,
    reason,
    text
])

    return Response(content="<Response></Response>", media_type="application/xml")

# -------------------- TWIML --------------------

@app.api_route("/twiml", methods=["GET", "POST"])
async def twiml(request: Request):

    roll = request.query_params.get("roll")
    subject = request.query_params.get("subject")
    section = request.query_params.get("section")
    department = request.query_params.get("department")

    BASE_URL = "https://untakable-dylan-jazziest.ngrok-free.dev"

    # Encode params
    subject_encoded = quote(subject)
    section_encoded = quote(section)
    department_encoded = quote(department)

    action_url = f"{BASE_URL}/recording?roll={roll}&subject={subject_encoded}&section={section_encoded}&department={department_encoded}"

    response = VoiceResponse()

    response.say("Please tell the reason for absence after the beep.")

    response.record(
        action=action_url,
        method="POST",
        max_length=30,
        timeout=5,
        play_beep=True
    )

    response.pause(length=2)

    print("🔥 TWIML SENT")

    return Response(content=str(response), media_type="application/xml")