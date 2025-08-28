import asyncio
from typing import (
  TypedDict,
  Sequence,
  Annotated,
)
from dataclasses import dataclass
import panel as pn
from langgraph.runtime import get_runtime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
  BaseMessage,
  SystemMessage,
  HumanMessage,
  AIMessage
)
from langgraph.graph.message import add_messages
from langgraph.graph import (
  StateGraph, 
  END, 
  START
)
from langgraph.prebuilt import ToolNode

from llm import get_llm
from config import settings, SYSTEM_PROMPT
from masking import Masker
from compendium import Compendium
import tools
import utils


@dataclass
class Context:
  llm: BaseChatModel
  masker: Masker


class AgentState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], add_messages]


async def mask(state: AgentState) -> AgentState:
  print('masking.....')
  print(state['messages'])
  runtime = get_runtime(Context)
  state['messages'][0].content = runtime.context.masker.mask(
    state['messages'][0].content
  )
  return {'messages': state['messages']}


async def unmask(state: AgentState) -> AgentState:
  print('unmasking.....')
  runtime = get_runtime(Context)
  state['messages'][0].content = runtime.context.masker.mask(
    state['messages'][-1].content
  )
  return {'messages': state['messages']}


async def call_model(state: AgentState) -> AgentState:
  print('calling model.....')
  runtime = get_runtime(Context)
  system_promt = SystemMessage(content=SYSTEM_PROMPT)
  prompt = [system_promt] + list(state['messages'])
  response = await runtime.context.llm.ainvoke(prompt)
  return {'messages': [response]}   


async def carry_on(state: AgentState) -> bool:
  messages = state["messages"]
  last_message = messages[-1]

  # Если последнее сообщение от AI и содержит вызовы инструментов - продолжаем
  if isinstance(last_message, AIMessage) and last_message.tool_calls:
    return True

  # Иначе заканчиваем
  return False


@utils.how_long('seconds')
async def main():
  masker = Masker(comp=comp)

  tools = [
    show_schedule, 
    current_datetime, 
    relationships, 
    age, 
    compare
  ]

  llm = get_llm('gigachat').bind_tools(tools)

  graph = StateGraph(AgentState)
  graph.add_node('masker', mask)
  graph.add_node('unmasker', unmask)
  graph.add_node('llm', call_model)
  graph.add_node('tools', ToolNode(tools=tools))
  
  graph.add_edge(START, 'masker')
  graph.add_edge('masker', 'llm')
  graph.add_conditional_edges(
    'llm', carry_on, {True: 'tools', False: 'unmasker'}
  )
  graph.add_edge('tools', 'llm')
  graph.add_edge('unmasker', END)


  #user_promt = masker.mask('Как связаны между собой Аркадий Стругацкий и Борис Стругацкий?')
  #user_promt = masker.mask('Какие отношения были между Аркадием Стругацким и Борисом Стругацким?')
  #user_promt = masker.mask('Кто старше Петр Емельянов или Александр Митрофанов?')
  #print(f'Prompt: {user_promt}')


  app = graph.compile()
  result = await app.ainvoke(
    input={
      'messages': [
        HumanMessage(
          content='Кто старше Петр Емельянов или Александр Митрофанов?'
        )
      ]
    },
    context=Context(
      llm=llm, 
      masker=masker
    )
  )

  print("\n\n=== REASONING ===")

  for i, msg in enumerate(result["messages"]):
    print(f"{i+1}. {type(msg).__name__}: {getattr(msg, 'content', None)}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
      print(f"   Tool calls: {msg.tool_calls}")

  for msg in reversed(result["messages"]):
    if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
      print(f"\n=== Финальный ответ ===")
      print(msg.content)

      print("\n\n=== Открытый ответ ===")
      print(masker.unmask(msg.content))
      break
    else:
      print("\n=== Финальный ответ не найден ===")

  print("\n\n=== Compendium ===")
  print(comp)


if __name__ == '__main__':
  asyncio.run(main())
