import re
import uuid
from presidio_analyzer import (
  AnalyzerEngine,
  RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from pymorphy3 import MorphAnalyzer

from compendium import (
  Substitution,
  Compendium,
  PIIKind
)


def create_analyzer() -> AnalyzerEngine:
  provider = NlpEngineProvider(
    nlp_configuration={
      'nlp_engine_name': 'spacy',
      'models': [
        {'lang_code': 'ru', 'model_name': 'ru_core_news_md'}
      ],
  })
  nlp_engine = provider.create_engine()
  return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=['ru'])


def make_token(kind: PIIKind) -> str:
  tok = str(uuid.uuid4())[:8]
  return f'⟪PII:{kind}:{tok}⟫'
  

class Masker:
  def __init__(self, comp: Compendium):
    self.morph = MorphAnalyzer()
    self.analyzer = create_analyzer()
    self.comp = comp


  def mask(self, text: str) -> str:
    spans: list[RecognizerResult] = self.analyzer.analyze(
      text=text,
      entities=[
        'PERSON', 'EMAIL_ADDRESS', 'LOCATION'
      ],
      language='ru',
    )

    return self._replace(text, spans)
  

  def unmask(self, text: str) -> str:
    return self.comp.reconstruct(text)
  

  def compendium_dict(self) -> dict:
    return self.comp.as_dict()
  

  def compendium_tree(self) -> dict:
    return self.comp.as_tree()  
  

  def _lemmatize(self, text: str) -> str:
    lemmas = []
    for w in text.split():
      lemmas.append(self.morph.parse(w)[0].normal_form)
    return ' '.join(lemmas)
  

  def _replace(self, text: str, spans: list[RecognizerResult]) -> str:
    curr = 0
    chunks = []
    for s in spans:
      chunks.append(text[curr:s.start])
      token = make_token(PIIKind(s.entity_type))
      self.comp.add(
        Substitution(
          text=text[s.start: s.end],
          lemma=self._lemmatize(text[s.start: s.end]),
          kind=PIIKind(s.entity_type),
          token=token,
        )
      )
      chunks.append(token)
      curr = s.end
    chunks.append(text[curr:])
    return ''.join(chunks)


if __name__ == "__main__":

  text = (
    "Как связаны между собой Аркадий Стругацкий и Борис Стругацкий?"
  )

  comp = Compendium()
  masker = Masker(comp)
  masked = masker.mask(text)
  print(masked)
  print(comp)  



   