import glob
import re
import torch
import numpy as np
from typing import Any, Union, List
import time
from abc import ABC, abstractmethod
import sqlite3
from sentence_transformers import SentenceTransformer
import faiss
import os
import torch
import clip
from PIL import Image
import uuid
from PyPDF2 import PdfReader
from dataclasses import dataclass


class Pipeline(ABC):

    @abstractmethod
    def insert_file(self) -> int:
        pass

    @abstractmethod
    def commit(self) -> int :
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int) -> list[int] :
        pass

class TextPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :

        self.chunk_size = 256 # word chunk size
        
        self.db_connection = sqlite3.connect(sqlite_uri)
        self.db = self.db_connection.cursor()
        
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS text_table (
                faiss_id INTEGER PRIMARY KEY,
                file_id TEXT,
                path TEXT,
                text_data TEXT
            )
        ''')

        self.db_connection.commit()
        
        try :
            self.index = faiss.read_index(faiss_uri)
        
        except RuntimeError:
            self.index = faiss.IndexFlatL2(384)
            faiss.write_index(self.index, faiss_uri)

        self.faiss_uri = faiss_uri
        self.model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    
    def commit(self) :
        self.db_connection.commit()
        faiss.write_index(self.index, self.faiss_uri)


    @staticmethod
    def split_text(text: str, max_words: int = 256) -> list[str]:
        words = text.split()
        chunks = []
        chunk = ""
        for word in words:
            if len(chunk.split()) + len(word.split()) <= max_words:
                chunk += word + " "
            else:
                chunks.append(chunk.strip())
                chunk = word + " "
        
        if chunk:
            chunks.append(chunk.strip())
        
        return chunks

    @staticmethod
    def extract_text(path: str) -> str :
        text=""
        pdf_reader = PdfReader(path)

        for page in pdf_reader.pages :
            text+= page.extract_text()

        cleaned_text = re.sub(r'[^\w\s]', ' ', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        cleaned_text = cleaned_text.lower()
        return cleaned_text

    def encode_text(self, sentences: list[str]) -> list[torch.Tensor] | np.ndarray | torch.Tensor:
        embeddings = self.model.encode(sentences)
        return np.array(embeddings).reshape(-1, 384)


    def insert_file(self, path: str) -> [int, int]:
        file_ext = path.split('.')[-1]
        file_id = str(uuid.uuid4())

        text = self.extract_text(path)
        sentences = self.split_text(text, self.chunk_size)
        embeddings = self.encode_text(sentences)
        first_index = self.index.ntotal
        self.index.add(embeddings)
        last_index = self.index.ntotal

        for i, sentence in enumerate(sentences) :
            self.db.execute(
                "INSERT INTO text_table (faiss_id, file_id, path, text_data) VALUES (?, ?, ?, ?)",
                (first_index + i, file_id, path, sentence)
            )
        
        self.commit()
        return file_id, first_index, last_index
        
    def similarity_search(self, query: str, k: int) -> list[int]:
        '''
        Returns list of (faiss_id, file_id, path, text_data) and Distances ranked according to distances.
        
        '''
        
        query_embedding = self.model.encode([query])
        D, I = self.index.search(np.array(query_embedding).reshape(-1, 384), k)


        faiss_indices = list(I[0])

        Q = f"SELECT * FROM text_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"

        return self.db.execute(Q).fetchall() , D

class ImagePipeline(Pipeline) :
    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :
        self.db_connection = sqlite3.connect(sqlite_uri)
        self.db = self.db_connection.cursor()
        
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS image_table (
                faiss_id INTEGER PRIMARY KEY,
                file_id TEXT,
                path TEXT,
            )
        ''')

        self.db_connection.commit()
        
        try :
            self.index = faiss.read_index(faiss_uri)
        
        except RuntimeError:
            self.index = faiss.IndexFlatL2(384)
            faiss.write_index(self.index, faiss_uri)

        self.faiss_uri = faiss_uri
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

    def commit(self) :
        self.db_connection.commit()
        faiss.write_index(self.index, self.faiss_uri)


    def insert_file(self, path: str) -> tuple :
        image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
        file_id = str(uuid.uuid4())
        first_index = self.index.ntotal
        with torch.no_grad() :
            embeddings = self.model.encode_image(image)
            self.index.add(embeddings)

        self.db.execute(
           f"INSERT INTO image_table (faiss_id, file_id, path) VALUES ({first_index}, {file_id}, {path})", 
        )

        self.commit()

        return file_id, first_index


    def similarity_search(self, q: str, k: int, file: bool = False) -> list[int]:
        if not file :
            text = clip.tokenize([q]).to(self.device)
            text_embeds = self.model.encode_text(text)

            D, I = self.index.search(text_embeds, k)

            faiss_indices = list(I[0])

            Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"
            return self.db.execute(Q).fetchall(), D
        
        else :
            file_ext = q.split('.')[-1]
            if file_ext.lower() in ['png', 'jpg', 'jpeg'] :
               image = self.preprocess(Image.open(q)).unsqueeze(0).to(self.device)
               with torch.no_grad() :
                   embeddings = self.model.encode_image(image)
                   D, I = self.index.search(embeddings, k)
                   faiss_indices = list(I[0])
                   
                   Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"
                   
                   return self.db.execute(Q).fetchall(), D

class AudioPipeline(Pipeline):
    pass


class VideoPipeline(Pipeline):
    pass
class Store:
    def __init__(self) :
        self.__is_connected = False
        

    
    def connect(self, store_uri: str) :
        sql_uri = store_uri.split('.')[0] 
        self.master_db_connection = sqlite3.connect(sql_uri + ".db")
        self.master_db = self.master_db_connection.cursor()

        text_index = sql_uri + '_text.faiss'
        image_index = sql_uri + '_image.faiss'

        





    def multimodal_search(self, path: str, k: int) :
        pass
    
    def search(self,) :
        pass

    def commit(self) :
        pass

    def sql(self) :
        return self.db




text_pipeline = TextPipeline(faiss_uri='text.faiss', sqlite_uri='semantic.db')
# text_pipeline.insert_file('Problem Solving in Data Structures & Algorithms Using C ( PDFDrive ).pdf')
print(text_pipeline.similarity_search("How to reverse a linked list", 10))
# print(text_pipeline.ntotal)
# tick = time.time()
# embeds = text_pipeline.encode_text(["There are 7 wonders in the world", "I have a ball, and will play with dog", "a great pizza"])
# tock = time.time()
# print(shape, tock - tick)

# def list_images():
#     '''
#     This function lists only image files in a directory
#     Filters out only image files (JPEG, PNG, GIF, etc.)
#     '''
#     extensions = ["png","jpeg","jpg","svg","gif","pjp","avif","apng","webp","jfif","pjpeg"]
#     images_files = []
#     for e in extensions:
#         f = glob.glob(f"**/*.{e}",recursive=True)
#         if f:images_files.append(f)
#     return images_files

# # Test the function
# #call the list_image function to search for images in cwd and subdirectories
# images_list = list_images()

# #display the found images
# #additional conversion to str for better viewing experience
# for image in images_list:
#     img = str(image)[1:-1]
#     print(img)

