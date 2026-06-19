import requests
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv(override=True)

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")

BASE_URL = "https://untakable-dylan-jazziest.ngrok-free.dev"


def trigger_call(to, roll, subject, section):

    if not str(to).startswith('+'):
        to = '+' + str(to)

    if not str(TWILIO_FROM).startswith('+'):
        from_number = '+' + str(TWILIO_FROM)
    else:
        from_number = TWILIO_FROM

    # ✅ ENCODE VALUES
    subject_encoded = quote(subject)
    section_encoded = quote(section)
    department_encoded = quote("CSE")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Calls.json"

    data = {
        "To": to,
        "From": from_number,
        "Url": f"{BASE_URL}/twiml?roll={roll}&subject={subject_encoded}&section={section_encoded}&department={department_encoded}"
    }

    response = requests.post(
        url,
        data=data,
        auth=(TWILIO_SID, TWILIO_TOKEN)
    )

    print("TWILIO RESPONSE:", response.text)

    return response.json()