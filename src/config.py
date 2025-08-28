from pydantic_settings import BaseSettings
from pydantic import ConfigDict


SYSTEM_PROMPT = (
  "Дословно сохраняй любые подстроки, заключённые в скобки ⟪ и ⟫ и начинающиеся с 'PII:'."
  "Не переводить, не склонять, не нормализовать и не изменять эти подстроки вообще." 
  "Используй только доступные тебе инструменты для выполнения задачи."
)

USER_AVATAR = "https://robohash.org/panso?set=set4"
AGENT_AVATAR = "https://robohash.org/quixote"


class Settings(BaseSettings):
  deepseek_model: str
  deepseek_api_key: str
  gigachat_model: str
  gigachat_api_key: str
  google_credentials_file: str
  google_token_file: str


  model_config = ConfigDict(
    env_file='.env',
    env_file_encoding='utf-8',
  )


settings = Settings()
