from dataclasses import dataclass
from typing import List


@dataclass
class ImageObject :
    uuid: str
    file_path: str
    distance: float

@dataclass 
class TextObject :
    uuid: str
    file_path: str
    chunks: List[str]
    distances: List[float]

@dataclass 
class AudioObject :
    uuid: str
    file_path: str
    chunks: List[str]
    distances: List[float]




@dataclass
class StoreObject :
    images : List[ImageObject] = []
    texts : List[TextObject] = []
    audios : List[AudioObject] = []