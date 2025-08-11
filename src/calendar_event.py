from hashlib import md5
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CalendarEvent:
  uid: str
  dtstart: datetime
  dtend: datetime
  last_modified: datetime
  summary: str | None = None
  description: str | None = None
  location: str | None = None
  parent_uid: str | None = None
  recurrence_id: str | None = None
  rrule: str | None = None

  @property
  def hash(self) -> str:
    raw = f"{self.summary}|{self.dtstart.isoformat()}|{self.dtend.isoformat()}|{self.description}|{self.location}|{self.rrule}"
    return md5(raw.encode('utf-8')).hexdigest()


  @property
  def is_recurring(self) -> bool:
    return self.rrule is not None and self.rrule != ""


  @property
  def rrule_str(self) -> str:
    if not self.rrule.startswith("RRULE:"):
      return "RRULE:" + self.rrule
    return self.rrule
  

  def __str__(self) -> str:
    return f"{self.uid}:{self.summary}"