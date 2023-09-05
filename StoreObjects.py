from dataclasses import dataclass, field
from typing import List

@dataclass
class ImageObject:
    uuid: str
    file_path: str
    distance: float

    

@dataclass
class TextObject:
    uuid: str
    file_path: str
    chunks: List[str]
    distances: List[float]

@dataclass
class AudioObject:
    uuid: str
    file_path: str
    chunks: List[str]
    distances: List[float]

@dataclass
class StoreObject:
    images: List[ImageObject] = field(default_factory=list)
    texts: List[TextObject] = field(default_factory=list)
    audios: List[AudioObject] = field(default_factory=list)
