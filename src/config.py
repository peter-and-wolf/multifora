from pydantic_settings import BaseSettings
from pydantic import ConfigDict


# SYSTEM_PROMPT = 'Ты – моя операционная система. Реши поставленную задачу, используя доступные тебе инструменты'
SYSTEM_PROMPT = 'Ты – мой личный ассистент. Реши поставленную задачу, используя доступные тебе инструменты'

class Settings(BaseSettings):
  deepseek_model: str
  deepseek_api_key: str
  google_credentials_file: str
  google_token_file: str


  model_config = ConfigDict(
    env_file='.env',
    env_file_encoding='utf-8',
  )


settings = Settings()
