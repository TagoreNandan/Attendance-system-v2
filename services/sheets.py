import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client = gspread.authorize(creds)

# your sheet
MASTER_SHEET_ID = "1QP6ubHF66JGM4hUs14A_NdLzdAIdSMgZZJD1KDdSVQY"
ATTENDANCE_SHEET_ID = "1N7TfBsK5ta79VZOQQiEInlmVjib9lDHyikX_5ds9T9A"

sheet = client.open_by_key(MASTER_SHEET_ID).sheet1


# ---------- GET PHONE ----------
def get_parent_number(roll):

    records = sheet.get_all_records()

    for row in records:
        if row["roll"] == roll:
            return row["phone"]

    return None


# ---------- UPDATE REASON ----------
def update_reason(roll, reason, transcript):

    records = sheet.get_all_records()

    for i, row in enumerate(records):
        if row["roll"] == roll:

            row_index = i + 2  # header offset

            # Column 4 = Reason
            # Column 5 = Transcript
            sheet.update_cell(row_index, 4, reason)
            sheet.update_cell(row_index, 5, transcript)

            return True

    return False


def create_daily_sheet(name):

    sh = client.open_by_key(ATTENDANCE_SHEET_ID)  # MUST EXIST ALREADY

    try:
        return sh.worksheet(name)
    except Exception:
        ws = sh.add_worksheet(title=name, rows="1000", cols="10")
        ws.append_row(["roll", "subject", "section", "department", "reason", "transcript"])
        return ws

# ---------- FETCH DATA ----------
def list_all_sheets():
    sh = client.open("attendance_calls")
    return [{"title": ws.title} for ws in sh.worksheets()]

def get_sheet_data(title):
    sh = client.open("attendance_calls")
    try:
        ws = sh.worksheet(title)
        records = ws.get_all_records()

        cleaned = []
        for row in records:
            # Handle both old + new format safely
            cleaned.append({
                "roll": row.get("roll"),
                "reason": row.get("reason"),
                "transcript": row.get("transcript")
            })

        return cleaned
    except Exception:
        return []


def get_student_details(roll):

    records = sheet.get_all_values()  # 🔥 NOT get_all_records()

    headers = [h.strip().lower() for h in records[0]]

    try:
        roll_idx = headers.index("roll")
        phone_idx = headers.index("phone")
        dept_idx = headers.index("department")
        section_idx = headers.index("section")
        year_idx = headers.index("year")
    except ValueError:
        print("❌ HEADER MISMATCH:", headers)
        return None

    for row in records[1:]:
        if str(row[roll_idx]) == str(roll):
            return {
                "phone": str(row[phone_idx]).strip(),
                "department": str(row[dept_idx]).strip(),
                "section": str(row[section_idx]).strip(),
                "year": str(row[year_idx]).strip()
            }

    return None