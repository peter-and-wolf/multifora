import pprint
from typing import Protocol

from nicegui import ui

from utils import (
  quote_tokens, 
  dict2args
)

class UIChatStep(Protocol):
  def show(self):
    pass


class UITextStep:
  def __init__(self, text: str):
    self.text = text
  
  def show(self):
    ui.markdown(self.text)  


class UIModelResponseStep:
  def __init__(self, text: str):
    self.text = text
  
  def show(self):
    with ui.column().classes('w-full'):
      ui.label('Ответ модели:')
      ui.markdown(quote_tokens(self.text))


class UIModelResponseJSONStep:
  def __init__(self, text: dict):
    self.text = text.replace('\\u27ea', '⟪').replace('\\u27eb', '⟫')
  
  def show(self):
    with ui.column().classes('w-full'):
      ui.label('Ответ модели:').classes('text-gray-600 font-semibold')
      ui.code(self.text, language='json')


class UIToolCallStep:
  def __init__(self, name: str, args: str, result: str):
    self.name = name
    self.args = args  
    self.result = result
  

  def show(self):
    with ui.column().classes('w-full grow'):
      ui.label('Инструмент:').classes('text-gray-600 font-semibold')
      ui.code(f'{self.name}({dict2args(self.args)})').classes('py-8 w-full break-words')  
      ui.label('Результат:').classes('text-gray-600 font-semibold')
      ui.markdown(pprint.pformat(self.result))


async def show_step(title: str, icon: str, step: UIChatStep):
  with ui.expansion(value=True).classes('max-w-xl self-stretch') as exp:
    with exp.add_slot('header'):
      with ui.row().classes('items-center justify-start'):
        ui.icon(icon, size='sm', color='primary')
        ui.label(f'{title}').classes('mr-3 text-base text-blue-950')
    step.show()
  ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
