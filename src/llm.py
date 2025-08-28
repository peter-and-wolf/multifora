from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat

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
    else:
      raise ValueError(f'Unknown model name: {model_name}') 