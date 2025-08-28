
import asyncio
from typing import AsyncGenerator

from nicegui import ui


class ChatDemo:
  def __init__(self) -> None:
    self.container = ui.column().classes("w-full max-w-2xl")
    self.should_stop = False
    self.setup_ui()

  def setup_ui(self) -> None:
    with self.container:
      self.button = ui.button("Send message", on_click=self.handle_click)

  def handle_click(self) -> None:
    if self.button.text == "Send message":
        self.should_stop = False
        self.button.text = "Stop"
        asyncio.create_task(self.send())
    else:
        self.should_stop = True
        self.button.text = "Send message"

  async def mock_stream(self) -> AsyncGenerator[str, None]:
    """Simulate streaming response"""
    response = "Hello! This is a test message that should stream word by word."
    for word in response.split():
      yield word + " "
      await asyncio.sleep(0.1)

  async def send(self) -> None:
    with self.container:
      thinking_row = ui.row().classes("items-center")
      with thinking_row:
        ui.spinner("dots", size="lg", color="primary")
        ui.label("Thinking...")

      await asyncio.sleep(2)
      if self.should_stop:
        thinking_row.clear()
        return

      thinking_row.clear()

      with self.container:
        message = ui.chat_message(name="Bot", text_html=True)
        with message:
          content = ui.html("")

      response = ""
      async for chunk in self.mock_stream():
        if self.should_stop:
          break
        response += chunk
        content.set_content(response)

      self.button.text = "Send message"



class Chat:
  def __init__(self):
    self.container = ui.column()
    self.message_container = ui.row()
    self.input_container = ui.row()


