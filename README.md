# AI Attendance Calling Automation System

## Overview

An AI-powered attendance automation system that automatically calls parents of absent students, records their responses, transcribes the conversation using Whisper AI, classifies the reason for absence, and stores the results in Google Sheets.

This project was developed as a mini-project to automate attendance follow-ups and reduce manual effort for faculty.

---

## Features

### Faculty Dashboard

* Enter subject, department, section, and year
* Select absent student roll numbers
* Trigger automated parent calls

### Automated Voice Calls

* Uses Twilio Voice API
* Calls parent phone numbers stored in Google Sheets
* Plays a pre-recorded attendance inquiry message

### AI Speech Processing

* Records parent responses
* Converts speech to text using Faster-Whisper
* Automatically classifies absence reasons

### Reason Classification

Detects categories such as:

* SICK
* TRAVEL
* FUNCTION
* BUSY
* CALLBACK
* NOT_INTERESTED
* OTHER

### Attendance Reports

* Stores transcripts and classified reasons
* Creates daily worksheets automatically
* Displays historical records through the dashboard

---

## Tech Stack

### Backend

* Python
* FastAPI

### Voice Processing

* Twilio Voice API
* Faster-Whisper

### Data Storage

* Google Sheets API
* gspread

### Frontend

* HTML
* CSS
* JavaScript

### Deployment Tools

* ngrok
* Uvicorn

---

## Project Structure

```text
Attendance-system-mini-project--main/

├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── services/
│   ├── caller.py
│   ├── sheets.py
│   └── __init__.py
│
├── main.py
├── generate_audio.py
├── question.mp3
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Setup

### Clone Repository

```bash
git clone https://github.com/TagoreNandan/Attendance-system-mini-project-
cd Attendance-system-mini-project-
```

### Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
TWILIO_SID=YOUR_TWILIO_ACCOUNT_SID
TWILIO_TOKEN=YOUR_TWILIO_AUTH_TOKEN
TWILIO_PHONE=YOUR_TWILIO_PHONE_NUMBER
```

---

## Google Sheets Setup

1. Create a Google Cloud Service Account
2. Enable Google Sheets API
3. Download service account credentials
4. Save as:

```text
credentials.json
```

5. Share the Google Sheet with:

```text
service-account-email@project.iam.gserviceaccount.com
```

---

## Running the Application

### Start FastAPI

```bash
python -m uvicorn main:app --reload
```

### Start ngrok

```bash
ngrok http 8000
```

### Update ngrok URL

Replace the ngrok URL inside:

```python
services/caller.py
main.py
```

with your latest ngrok forwarding URL.

---

## Workflow

1. Faculty selects absent students.
2. System fetches parent phone numbers from Google Sheets.
3. Twilio initiates calls.
4. Parent response is recorded.
5. Whisper transcribes audio.
6. AI classifies absence reason.
7. Results are saved to Google Sheets.
8. Dashboard displays transcripts and classifications.

---

## Example Output

| Roll Number | Reason | Transcript                                              |
| ----------- | ------ | ------------------------------------------------------- |
| 23E51A0517  | SICK   | Child is suffering from fever and admitted to hospital. |

---

## Future Improvements

* Multi-language support
* LLM-based reason classification
* SMS notifications
* Analytics dashboard
* Cloud deployment
* Role-based authentication

---

## Author

Tagore Nandan

Computer Science Engineering

Hyderabad Institute of Technology and Management

Built using FastAPI, Twilio, Google Sheets, and Whisper AI.
