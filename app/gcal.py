from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.models import Allocation, Block, Event

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS = Path("credentials.json")
TOKEN = Path("token.json")
CALENDAR_NAME = "backtiming"
TAG = "backtimingEvent"


def available() -> bool:
    return CREDENTIALS.exists()


def service():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def calendars(svc) -> list[dict]:
    return svc.calendarList().list().execute().get("items", [])


def own_calendar_id(svc) -> str:
    for cal in calendars(svc):
        if cal.get("summary") == CALENDAR_NAME:
            return cal["id"]
    return svc.calendars().insert(body={"summary": CALENDAR_NAME}).execute()["id"]


def busy(start: datetime, end: datetime) -> list[Block]:
    svc = service()
    own = own_calendar_id(svc)
    items = [{"id": c["id"]} for c in calendars(svc) if c["id"] != own]
    body = {"timeMin": start.isoformat(), "timeMax": end.isoformat(), "items": items}
    result = svc.freebusy().query(body=body).execute()
    return [Block(**b) for cal in result["calendars"].values() for b in cal.get("busy", [])]


def push(event: Event, allocations: list[Allocation]) -> int:
    svc = service()
    cal = own_calendar_id(svc)
    old = svc.events().list(calendarId=cal, privateExtendedProperty=f"{TAG}={event.id}", maxResults=2500).execute()
    for item in old.get("items", []):
        svc.events().delete(calendarId=cal, eventId=item["id"]).execute()
    for a in allocations:
        body = {
            "summary": f"{a.title} · {event.title}",
            "start": {"dateTime": a.start.isoformat()},
            "end": {"dateTime": a.end.isoformat()},
            "extendedProperties": {"private": {TAG: str(event.id)}},
        }
        svc.events().insert(calendarId=cal, body=body).execute()
    return len(allocations)
