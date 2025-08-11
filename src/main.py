import os
import asyncio
from typing import (
  TypedDict,
  Sequence,
  Annotated,
)
from dataclasses import dataclass
from langchain_deepseek import ChatDeepSeek
from langgraph.runtime import get_runtime
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

from config import settings, SYSTEM_PROMPT
from tools import show_schedule, current_datetime
import utils


@dataclass
class Context:
  llm: ChatDeepSeek


class AgentState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], add_messages]


async def model_call(state: AgentState) -> AgentState:
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
  tools = [show_schedule, current_datetime]

  llm = ChatDeepSeek(
    model=settings.deepseek_model, 
    api_key=settings.deepseek_api_key
  ).bind_tools(tools)

  graph = StateGraph(AgentState)
  graph.add_node('agent', model_call)
  tool_node = ToolNode(tools=tools)
  graph.add_node('tools', tool_node)

  graph.add_edge(START, 'agent')
  graph.add_conditional_edges(
    'agent', carry_on, {True: 'tools', False: END}
  )
  graph.add_edge('tools', 'agent')

  app = graph.compile()
  result = await app.ainvoke(
    input={
      'messages': [
        HumanMessage(
          content="Какое сегодня число?"
        )
      ]
    },
    context=Context(llm=llm)
  )

  for i, msg in enumerate(result["messages"]):
    print(f"{i+1}. {type(msg).__name__}: {getattr(msg, 'content', None)}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
      print(f"   Tool calls: {msg.tool_calls}")

  for msg in reversed(result["messages"]):
    if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
      print(f"\n=== Финальный ответ ===")
      print(msg.content)
      break
    else:
      print("\n=== Финальный ответ не найден ===")


if __name__ == '__main__':
  asyncio.run(main())
