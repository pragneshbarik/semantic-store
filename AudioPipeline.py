
from BasePipeline import Pipeline
import TextPipeline
import whisper
import re
import torch
import numpy as np
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


class AudioPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :
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
        self.whisper_model = whisper.load_model('tiny.en')
        self.model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    
    def commit(self) :
        self.db_connection.commit()
        faiss.write_index(self.index, self.faiss_uri)


    def encode_text(self, sentences: list[str]) -> list[torch.Tensor] | np.ndarray | torch.Tensor :
        embeddings = self.model.encode(sentences)
        return np.array(embeddings).reshape(-1, 384)

  

    def insert_file(self, path: str) -> tuple :
        extracted_text = self.whisper_model.transribe(path)
        extracted_text = extracted_text['text']

        sentences = TextPipeline.split_text(extracted_text)
        file_id = str(uuid.uuid4())
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
        print(D, I)

        Q = f"SELECT * FROM text_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"

        return self.db.execute(Q).fetchall() , D