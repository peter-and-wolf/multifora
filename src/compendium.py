import pprint
from enum import StrEnum
from dataclasses import dataclass, asdict


class PIIKind(StrEnum):
  PERSON = 'PERSON'
  EMAIL = 'EMAIL'
  NUMBER = 'NUMBER'
  RELATIONSHIP = 'RELATIONSHIP'
  LOCATION = 'LOCATION'


@dataclass
class Substitution:
  text: str
  lemma: str
  kind: PIIKind
  token: str


class Compendium:
  def __init__(self):
    self.dictionary: dict[str, Substitution] = {}


  def add(self, substitution: Substitution):
    self.dictionary[substitution.token] = substitution


  def __repr__(self) -> str:
    return pprint.pformat(self.dictionary)
  

  def reconstruct(self, text: str) -> str:
    for token, substitution in self.dictionary.items():
      text = text.replace(token, substitution.text)
    return text
  

  def get(self, token: str) -> Substitution:
    return self.dictionary.get(token)
  
  
  def as_dict(self) -> dict:
    return {k: asdict(v) for k, v in self.dictionary.items()}
  
  def as_tree(self) -> dict:
    tree = []
    for i, (k, v) in enumerate(self.dictionary.items()):
      tree.append({
        'id': k, 
        'label': k,
        'children': [
          {'id': f'text{i}', 'label': 'text', 'children': [{'id': f'text_c{i}', 'label': v.text}]},
          {'id': f'lemma{i}', 'label': 'lemma','children': [{'id': f'lemma_c{i}', 'label': v.lemma}]},
          {'id': f'kind{i}', 'label': 'kind', 'children': [{'id': f'kind_c{i}', 'label': v.kind}]}
        ]
      })
    return tree
  
    
        
   

