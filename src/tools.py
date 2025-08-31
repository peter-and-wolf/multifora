import os
import functools
from pprint import pprint
from datetime import datetime, UTC
from langchain_core.tools import tool
from compendium import (
  Compendium, 
  Substitution,
  PIIKind
)
from masking import make_token
from db import db

comp = Compendium()

def log_tool(func):
  @functools.wraps(func)
  async def wrapper(*args, **kwargs):
    print()
    print(f'=== calling tool: {func.__name__} ===')
    print(f'positional: {args}') 
    print(f'keyword - {kwargs}')
    result = await func(*args, **kwargs)
    print(f'returned: {result}')
    return result
  return wrapper


@tool
@log_tool
async def add(a: int, b: int) -> int:
  ''' Складывает два целых числа и возвращает результат. '''
  return a + b


@tool  
@log_tool
async def list_files() -> list:
  ''' Возвращает список файлов в текущей папке. '''
  return os.listdir(".")


@tool
@log_tool
async def current_datetime() -> datetime:
  ''' Возвращает текущее всемирное координированное время (UTC) в формате ISO 8601. '''
  return datetime.now(UTC).isoformat()


@tool
@log_tool
async def show_schedule(from_date: datetime, to_date: datetime):
  ''' Показывает расписание на указанный период c from_date до to_date. '''
  pprint(f'schedule: {from_date} - {to_date}')


@tool
@log_tool
async def relationships(t1: str, t2: str) -> str:
  ''' Возвращает информацию о связях или отношениях между двумя 
  объектами t1 и t2, которые заданы строками в формате "⟪PII:*⟫"
  Возвращаемое значение – строка в формате ⟪PII:RELATIONSHIP:*⟫.
  '''
  token = make_token(PIIKind.RELATIONSHIP)
  comp.add(Substitution(
    text='братьями',
    lemma='братья',
    kind=PIIKind.RELATIONSHIP,
    token=token
  ))
  return f'{t1} и {t2} являются {token}'


@tool
@log_tool
async def user_name() -> str:
  ''' Возвращает имя текущего пользователя.
  '''
  return 'Емельянов Петр Николаевич'


@tool
@log_tool
async def age(t: str) -> str:
  ''' Возвращает информацию о возрасте объекта t, который задан строками 
  в формате "⟪PII:PERSON:*⟫". Возвращаемое значение – строка, включающая 
  возраст в формате "⟪PII:NUMBER:*⟫. ВАЖНО: на множестве объектов "⟪PII:NUMBER:*⟫" не определено отношение 
  порядка, ты не можешь сравнивать их напрямую".
  '''
  if s := comp.get(t):
    if age := db['age'].get(s.lemma):
      token = make_token(PIIKind.NUMBER)
      comp.add(Substitution(
        text=str(age),
        lemma=str(age),
        kind='NUMBER',
        token=token
      ))
      return f'возраст {t} – {token} лет'
  return f'возраст {t} неизвестен'


@tool
@log_tool
async def compare(t1: str, t2: str) -> str:
  ''' Сравнивает два объекта t1 и t2, которые заданы строками 
  в формате "⟪PII:NUMBER:*⟫". Возвращает строку "GREATER", если t1 больше t2, 
  "EQUAL", если t1 равен t2, и "LESS", если t1 меньше t2, "UNKNOWN", если t1 и t2 
  не являются числами.
  '''
  if s1 := comp.get(t1):
    if s2 := comp.get(t2):
      if s1.kind == s2.kind == 'NUMBER':
        n1 = int(s1.text)
        n2 = int(s2.text)
        if n1 > n2:
          return 'GREATER'
        elif n1 == n2:
          return 'EQUAL'
        else:
          return 'LESS'

  return 'UNKNOWN'


@tool
@log_tool
async def sort(tl: list[str], reverse: bool = False) -> list[str]:
  ''' Сортирует список объектов, заданых строками в формате "⟪PII:NUMBER:*⟫", 
  в порядке возрастания или убывания. Если reverse=False, то сортирует в порядке возрастания, 
  если reverse=True, то сортирует в порядке убывания. Возвращает отсортированный список объектов 
  в формате "⟪PII:NUMBER:*⟫". 
  '''
  pairs = []
  for t in tl:
    if s := comp.get(t):
      pairs.append((t, int(s.lemma)))
    else:
      return 'Сортировку выполнить не удалось'
     
  return [p[0] for p in sorted(pairs, key=lambda x: x[1])]


@tool
@log_tool
async def city_area(tс: str) -> str:
  ''' Возвращает информацию о площади географического объекта tс (например, города), который 
  задан строкой в формате "⟪PII:LOCATION:*⟫". Возвращаемое значение – строка, включающая площадь 
  в формате "⟪PII:NUMBER:*⟫" ВАЖНО: на множестве объектов "⟪PII:NUMBER:*⟫" не определено отношение 
  порядка, ты не можешь сравнивать их напрямую.
  '''
  if c := comp.get(tс):
    if area := db['cities'].get(c.lemma):
      token = make_token(PIIKind.NUMBER)
      comp.add(Substitution(
        text=str(area),
        lemma=str(area),
        kind='NUMBER',
        token=token
      ))
      return f'площадь {tс} – {token}'
  return f'площадь {tс} неизвестна'


tools = [
  #add,
  #list_files,
  #current_datetime,
  #show_schedule,
  #relationships,
  user_name,
  age,
  city_area,
  compare,
  sort
]


