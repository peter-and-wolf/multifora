from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatYandexGPT

from config import settings


def get_llm(model_name: str) -> BaseChatModel:
    if model_name == 'deepseek':
      return ChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_model, 
      )
    elif model_name == 'gigachat':
      return GigaChat(
        credentials=settings.gigachat_api_key, 
        model=settings.gigachat_model, 
        verify_ssl_certs=False, 
      )
    elif model_name == 'yandexgpt':
      return ChatYandexGPT(
        api_key=settings.yandexgpt_api_key, 
        model_uri=settings.yandexgpt_model, 
      ) 
    elif model_name == 'openrouter':
      return ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=settings.openrouter_api_key, 
        model=settings.openrouter_model, 
      )
    else:
      raise ValueError(f'Unknown model name: {model_name}') 