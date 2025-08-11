from typing import Any
from os import path
from functools import cache

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from google.auth.transport.requests import Request # type: ignore
from datetime import datetime, timezone

from calendar_event import CalendarEvent
from config import google_config  


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service(token_file: str) -> Any:
  creds = None
  if path.exists(token_file):
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
      with open(token_file, "w") as token:
        token.write(creds.to_json())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        google_config.credentials_file, 
        SCOPES
      )

      creds = flow.run_local_server(
        port=8080,
        access_type="offline",
        prompt="consent",
        open_browser=False  
      )

      with open(token_file, "w") as token:
       token.write(creds.to_json())
    
  return build("calendar", "v3", credentials=creds)


class GoogleCalendar:
  def __init__(self, token_file: str, calendar_name: str):
    self.service = get_service(token_file)
    self.calendar_name = calendar_name
    self.calendar_id = self._get_calendar_id()

  
  def name(self) -> str:
    return f'GoogleCalendar: {self.calendar_name}'


  def _get_calendar_id(self) -> str:
    page_token = None
    while True:
      calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
      for calendar_entry in calendar_list.get("items", []):
        summary = calendar_entry.get("summary")
        calendar_id = calendar_entry.get("id")
        if summary == self.calendar_name:
          return calendar_id
      page_token = calendar_list.get("nextPageToken")
      if not page_token:
        break

    raise ValueError(f"Calendar with name {self.calendar_name} not found")


  @cache
  def fetch_events(self, from_date: datetime) -> dict[str, CalendarEvent]:
    events_result = self.service.events().list(
      calendarId=self.calendar_id,
      timeMin=from_date.isoformat().replace("+00:00", "Z"),
      showDeleted=False,
      singleEvents=False,  
      maxResults=2500,
      orderBy='updated'
    ).execute()

    events =  {}
    for event in events_result.get("items", []):
      if 'start' not in event or 'end' not in event:
        continue

      start = event['start'].get('dateTime') or event['start'].get('date')
      end = event['end'].get('dateTime') or event['end'].get('date')
      last_modified = event.get('updated')
      recurrence = event.get('recurrence', [])
      rrule = recurrence[0].lstrip('RRULE:') if recurrence else ""

      calendar_event = CalendarEvent(
        uid=event['id'],  
        summary=event.get('summary', ''),
        dtstart=datetime.fromisoformat(start).astimezone(timezone.utc),
        dtend=datetime.fromisoformat(end).astimezone(timezone.utc),
        last_modified=datetime.fromisoformat(last_modified).astimezone(timezone.utc),
        description=event.get('description', ''),
        location=event.get('location', ''),
        rrule=rrule
      )

      #print(event.get('recurringEventId', None))
      #print(event)

      events[event['id']] = calendar_event

    return events


  def create_event(self, event: CalendarEvent) -> str:
    body = {
      'summary': event.summary,
      'description': event.description,
      'location': event.location,
      'start': {'dateTime': event.dtstart.isoformat(), 'timeZone': 'UTC'},
      'end': {'dateTime': event.dtend.isoformat(), 'timeZone': 'UTC'},
    }

    if event.is_recurring:
      body['recurrence'] = [event.rrule_str]

    created = self.service.events().insert(
      calendarId=self.calendar_id, 
      body=body
    ).execute()

    return created['id']


  def delete_event(self, event_id: str):
    self.service.events().delete(
      calendarId=self.calendar_id,
      eventId=event_id
    ).execute()


  def update_event(self, event_id: str, event: CalendarEvent) -> None:

    if event.parent_uid is not None:
      print('RECURRENT EXCEPTION!!!')
      return      

    body = {
      'summary': event.summary,
      'description': event.description,
      'location': event.location,
      'start': {'dateTime': event.dtstart.isoformat(), 'timeZone': 'UTC'},
      'end': {'dateTime': event.dtend.isoformat(), 'timeZone': 'UTC'},
    }

    if event.is_recurring:
      body['recurrence'] = [event.rrule_str]

    self.service.events().update(
      calendarId=self.calendar_id,
      eventId=event_id,
      body=body
    ).execute()


  def __str__(self) -> str:
    return self.name()
    

def main():
  calendar = GoogleCalendar(
    google_config.token_file,
    google_config.calendar_name
  )
  events = calendar.fetch_events(datetime.now(timezone.utc))
  print('\n\n')
  for key, event in events.items(): 
    print(f"{key}: {event}")  


if __name__ == "__main__":
  main()  
  