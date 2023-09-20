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


@dataclass
class FileObject:
    uuid: str
    file_path: str
    file_type : str


@dataclass
class BaseTextObjects:
    def __init__(self, objects=[]):
        self.objects = objects
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.objects):
            current_object = self.objects[self.index]
            self.index += 1
            return current_object
        raise StopIteration

    def chunks(self):
        all_chunks = []
        all_dist = []

        for obj in self.objects:
            all_chunks.extend(obj.chunks)
            all_dist.extend(obj.distances)

        pairs = list(zip(all_chunks, all_dist))

        sorted_pairs = sorted(pairs, key=lambda pair: pair[1])
        sorted_chunks = [pair[0] for pair in sorted_pairs]

        return sorted_chunks

    

class TextObjects(BaseTextObjects):
    def __repr__(self) :
        return f"TextObjects containing {len(self.objects)} documents and {len(self.chunks())} chunks"

class AudioObjects(BaseTextObjects):
    def __repr__(self) :
        return f"AudioObjects containing {len(self.objects)} documents and {len(self.chunks())} chunks"


class ImageObjects:
    def __init__(self, image_objects: List[ImageObject] = []):
        self.image_objects = image_objects
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.image_objects):
            current_image_object = self.image_objects[self.index]
            self.index += 1
            return current_image_object
        raise StopIteration
    
    def __repr__(self) -> str:
        return f"ImageObjects containing {len(self.objects)} documents"

    
