import os
from pprint import pprint
from datetime import datetime, UTC
from langchain_core.tools import tool


@tool
async def add(a: int, b: int) -> int:
  ''' Складывает два целых числа и возвращает результат. '''
  return a + b


@tool  
async def list_files() -> list:
  ''' Возвращает список файлов в текущей папке. '''
  return os.listdir(".")


class Toolchain:
  def __init__(self, name: str):
    self.name = name

  @tool
  async def add(self, x: int, y: int):
    ''' Складывает два целых числа и возвращает результат. '''
    pprint(f'{self.name}: {x} + {y} = {x + y}')
    return x + y

  @tool
  async def list_files(self):
    ''' Возвращает список файлов в текущей папке. '''
    pprint(f'{self.name}: {os.listdir('.')}')
    return os.listdir('.')

tc = Toolchain('Toolchain')

async def current_datetime() -> datetime:
  ''' Возвращает текущее всемирное координированное время (UTC) в формате ISO 8601. '''
  pprint(f'TOOL CALLED')
  return datetime.now(UTC).isoformat()


async def show_schedule(from_date: datetime, to_date: datetime):
  ''' Показывает расписание на указанный период. '''
  pprint(f'TOOL CALLED')
  pprint(f'{tc.name}: {from_date} - {to_date}')

