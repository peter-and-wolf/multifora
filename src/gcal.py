import asyncio
import json
from pprint import pprint
from typing import Any
from os import path
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from google.auth.transport.requests import Request # type: ignore
from aiogoogle import Aiogoogle 
from aiogoogle.auth.creds import (
  UserCreds,
  ClientCreds
)

from config import settings 


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_client_creds() -> ClientCreds:
  with open(settings.google_credentials_file, "r") as f:
    creds = json.load(f)
    return ClientCreds(
      client_id=creds['installed']['client_id'],
      client_secret=creds['installed']['client_secret'],
      scopes=SCOPES
    )


def get_creds() -> tuple[UserCreds, ClientCreds]:
  creds = None
  if path.exists(settings.google_token_file):
    creds = Credentials.from_authorized_user_file(settings.google_token_file, SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
      with open(settings.google_token_file, "w") as token:
        token.write(creds.to_json())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        settings.google_credentials_file, 
        SCOPES
      )

      creds = flow.run_local_server(
        port=8080,
        access_type="offline",
        prompt="consent",
        open_browser=False  
      )

      with open(settings.google_token_file, "w") as token:
       token.write(creds.to_json())
  return (
    UserCreds(
      access_token=creds.token,
      refresh_token=creds.refresh_token,
      expires_at=creds.expiry
    ),
    ClientCreds(
      client_id=creds.client_id,
      client_secret=creds.client_secret,
      scopes=creds.scopes
    )
  )
  
async def list_events(calendar_id: str, from_date: datetime):
  user_creds, client_creds = get_creds()
  async with Aiogoogle(user_creds=user_creds, client_creds=client_creds) as aiogoogle:
    calendar_service = await aiogoogle.discover("calendar", "v3")
    pages = await aiogoogle.as_user(
      calendar_service.events.list(
        calendarId=calendar_id,
        #timeMin=from_date.isoformat().replace("+00:00", "Z"),
      ), 
      full_res=True
    )
    async for page in pages:
      pprint.pprint(page)


async def get_calendar_id(calendar_name: str) -> str:
  user_creds, client_creds = get_creds()
  async with Aiogoogle(user_creds=user_creds, client_creds=client_creds) as aiogoogle:
    calendar_service = await aiogoogle.discover("calendar", "v3")
    pages = await aiogoogle.as_user(
      calendar_service.calendarList.list(), 
      full_res=True
    )
    async for page in pages:
      for calendar in page['items']:
        if calendar['summary'] == calendar_name:
          pprint(calendar['id'])
          return calendar['id']
      raise ValueError(f'Calendar {calendar_name} not found')
    

if __name__ == "__main__":
   asyncio.run(get_calendar_id(
     calendar_name='Bloom'
   ))



    
  