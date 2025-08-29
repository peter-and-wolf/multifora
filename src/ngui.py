import os
import asyncio
from datetime import datetime
from dataclasses import dataclass
import time
import json
from typing import (
  TypedDict,
  Sequence,
  Annotated,
  Callable
)

from langgraph.runtime import get_runtime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
  BaseMessage,
  SystemMessage,
  HumanMessage,
  ToolMessage,
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
from masking import Masker
from compendium import Compendium
import tools
from db import db, db_tree

from nicegui import ui

from config import (
  SYSTEM_PROMPT,
  USER_AVATAR, 
  AGENT_AVATAR,
  settings
)

from ui_steps import (
  UITextStep,
  UIToolCallStep,
  UIModelResponseStep,
  UIModelResponseJSONStep,
  show_step
)


@ui.refreshable
def compendium_tree():
  ui.tree(tools.comp.as_tree(), label_key='label')


@dataclass
class Context:
  llm: BaseChatModel
  masker: Masker
  message_container: ui.element


class AgentState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], add_messages]


async def mask(state: AgentState) -> AgentState:
  runtime = get_runtime(Context)
  state['messages'][0].content = runtime.context.masker.mask(
    state['messages'][0].content
  )
  with runtime.context.message_container:

    await show_step(
      title='Маскирую запрос', 
      icon='ti-lock',
      step=UITextStep(
        text=state['messages'][0].content
      )
    )
  
  compendium_tree.refresh()
  
  return {'messages': state['messages']}


async def unmask(state: AgentState) -> AgentState:
  runtime = get_runtime(Context)
  response = runtime.context.masker.unmask(
    state['messages'][-1].content
  )
  with runtime.context.message_container:
    await show_step(
      title='Снимаю маски', 
      icon='ti-unlock',
      step=UITextStep(
        text=response
      )
    )
  return {'messages': [response]}


async def call_model(state: AgentState) -> AgentState:
  runtime = get_runtime(Context)
  system_promt = SystemMessage(content=SYSTEM_PROMPT)
  prompt = [system_promt] + list(state['messages'])
  response = await runtime.context.llm.ainvoke(prompt)
  with runtime.context.message_container:
    if response.tool_calls:
      answer = json.dumps(response.tool_calls, indent=2)
      await show_step(
        title='Вызываю модель',
        icon='ti-wand',
        step=UIModelResponseJSONStep(
          text=answer
        )
      )      
    else:
      await show_step(
        title='Вызываю модель',
        icon='ti-wand',
        step=UIModelResponseStep(
          text=response.text()
        )
      )
  
  return {'messages': [response]}   


async def call_tool(state: AgentState):
  runtime = get_runtime(Context)
  tools_by_name = {tool.name: tool for tool in tools.tools}
  outputs = []
  for tool_call in state["messages"][-1].tool_calls:
    tool_result = await tools_by_name[tool_call['name']].ainvoke(tool_call['args'])

    with runtime.context.message_container:
      tool_name = tools_by_name[tool_call["name"]].name
      await show_step(
        title='Вызываю инструмент',
        icon='ti-plug',
        step=UIToolCallStep(
          name=tool_name,
          args=tool_call["args"],
          result=tool_result
        )
      )

      # Update the compendium anyway
      compendium_tree.refresh()
      
      outputs.append(
        ToolMessage(
          content=json.dumps(tool_result),
          name=tool_call["name"],
          tool_call_id=tool_call["id"],
        )
      )
  return {"messages": outputs}


async def carry_on(state: AgentState) -> bool:
  messages = state["messages"]
  last_message = messages[-1]

  # Если последнее сообщение от AI и содержит вызовы инструментов - продолжаем
  if isinstance(last_message, AIMessage) and last_message.tool_calls:
    return True

  # Иначе заканчиваем
  return False


class Service:
  def __init__(self, container: ui.element, input_element: ui.element) -> None:
    self.container = container
    self.input_element = input_element

    self.llm = get_llm('gigachat') #.bind_tools(tools.tools)
    self.tools = []
    self.graph = StateGraph(AgentState)
    self.graph.add_node('masker', mask)
    self.graph.add_node('unmasker', unmask)
    self.graph.add_node('llm', call_model)
    self.graph.add_node('tools', call_tool)
  
    self.graph.add_edge(START, 'masker')
    self.graph.add_edge('masker', 'llm')
    self.graph.add_conditional_edges(
      'llm', carry_on, {True: 'tools', False: 'unmasker'}
    )

    self.graph.add_edge('tools', 'llm')
    self.graph.add_edge('unmasker', END)
    self.masker = Masker(comp=tools.comp)
    self.app = self.graph.compile()


  def get_message(self) -> str:
    msg = self.input_element.value
    self.input_element.value = ''
    return msg
  

  def connect_tool(self, on: bool, tool: Callable) -> None:
    tidx = -1
    for i, t in enumerate(self.tools):
      if t == tool:
        tidx = i
        break
    if tidx >= 0:
      self.tools.pop(tidx)
    if on:
      self.tools.append(tool) 

    self.llm = self.llm.bind_tools(self.tools)


  async def invoke(self) -> None:
    with self.container:
      message = self.get_message()
      ui.chat_message(
        text=message,
        name='User',
        stamp=datetime.now().strftime('%H:%M'),
        sent=True,
        avatar=USER_AVATAR
      )
      with ui.chat_message(
        name='Agent',
        sent=False,
        avatar=AGENT_AVATAR
      ).props('bg-color=blue-2') as agent_message:
        spinner = ui.spinner(type='dots')
        result = await self.app.ainvoke(
          input={
            'messages': [
              HumanMessage(
                content=message
              )
            ]
          },
          context=Context(
            llm=self.llm, 
            masker=self.masker,
            message_container=agent_message
          )
        )
        agent_message.remove(spinner)
      print(result)
      if result:
        ui.chat_message(
          text=result['messages'][-1].content,
          name='Agent',
          stamp=datetime.now().strftime('%H:%M'),
          sent=False,
          avatar=AGENT_AVATAR
        )
  
    ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')


def make_callback(service: Service, fn: str, *args, **kwargs):
  async def cb(e) -> None:
    if fn == 'invoke':
      await service.invoke(*args, **kwargs)
    elif fn == 'connect_tool':
      service.connect_tool(e.value, *args, **kwargs)
    else:
      raise ValueError(f'Unknown function {fn}')
  return cb


@ui.page('/')
def page_layout():
  
  with ui.header(elevated=True).style('background-color: #3874c8').classes(
      'flex items-center justify-start pl-0 pr-2 py-2'):
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu') \
      .props('flat color=white') \
        .classes('ml-0')
    ui.label('Homomorphic Agent').classes('ml-0')
    ui.space()
    ui.button(on_click=lambda: right_drawer.toggle(), icon='menu') \
      .props('flat color=white') \
      .classes('ml-0')


  with ui.left_drawer(bottom_corner=True).style('background-color: #ebf1fa').props('bordered') as left_drawer:
    with ui.column().classes('w-full h-full flex'):
      with ui.column().classes('gap-0 w-full grow'):
        with ui.row().classes('w-full gap-0 item-center'):
          ui.button(icon='ti-trash', on_click=lambda: (tools.comp.clear(), compendium_tree.refresh())).props('flat')
          ui.label('Компендиум').classes('self-center text-sm font-medium text-gray-700')
        with ui.scroll_area().classes('w-full h-full'):
          compendium_tree()

      ui.separator().classes('grow-0')
  
      with ui.column().classes('gap-0 w-full p-0 grow'):
        ui.label('База Данных').classes('px-3 py-2 text-sm font-medium text-gray-700')
        with ui.scroll_area().classes('w-full h-full'):
          ui.tree(db_tree, label_key='id').expand()

  svc: Service = None
  chat_feed = ui.column().classes('max-w-xl text-wrap')

  with ui.footer().classes('bg-white'):
    with ui.row().classes('w-full no-wrap items-start'):
      with ui.avatar():
        ui.image(USER_AVATAR)
      text = ui.input(placeholder='message') \
        .props('rounded outlined input-class=mx-3') \
        .classes('w-full')#.classes('w-3/4')
      svc = Service(chat_feed, text)
      text.on('keydown.enter', make_callback(svc, fn='invoke'))

  with ui.right_drawer(bottom_corner=True).style('background-color: #ebf1fa').props('bordered') as right_drawer:
    with ui.scroll_area().classes('w-full h-full flex'):
      ui.label('Инструменты').classes('px-3 py-2 text-sm font-medium text-gray-700')
      for t in tools.tools:
        with ui.column().classes('w-full gap-0'):
          with ui.row().classes('w-full gap-0 items-center'):
            ui.switch(value=False, on_change=make_callback(svc, fn='connect_tool', tool=t))
            ui.label(t.name)
          ui.label(t.description).classes('text-xs font-light px-3')


ui.add_head_html('<link href="https://cdn.jsdelivr.net/themify-icons/0.1.2/css/themify-icons.css" rel="stylesheet" />', shared=True)

ui.run()

