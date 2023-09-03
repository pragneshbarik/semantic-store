import glob
import whisper
import re
import torch
import numpy as np
import time
from abc import ABC, abstractmethod
import sqlite3
from BasePipeline import Pipeline

from sentence_transformers import SentenceTransformer
import faiss
import os
import torch
import clip
from PIL import Image
import uuid
from PyPDF2 import PdfReader


class ImagePipeline :

    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :
        self.db_connection = sqlite3.connect(sqlite_uri)
        self.db = self.db_connection.cursor()
        
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS image_table (
                faiss_id INTEGER PRIMARY KEY,
                file_id TEXT,
                path TEXT
            )
        ''')

        self.db_connection.commit()
        
        try :
            self.index = faiss.read_index(faiss_uri)
        
        except RuntimeError:
            self.index = faiss.IndexFlatL2(512)
            faiss.write_index(self.index, faiss_uri)

        self.faiss_uri = faiss_uri
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

  

    def commit(self) :
        self.db_connection.commit()
        faiss.write_index(self.index, self.faiss_uri)


    def insert_file(self, path: str) -> tuple :
        file_id = str(uuid.uuid4())
        first_index = self.index.ntotal
        embeddings = {}
        with torch.no_grad() :
            image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
            embeddings[path] = self.model.encode_image(image)
            
        embed_vector = embeddings[path].detach().cpu().numpy()

        embed_vector = np.float32(embed_vector)
        
        faiss.normalize_L2(embed_vector)
        self.index.add(embed_vector)
        
        

        self.db.execute(
           "INSERT INTO image_table (faiss_id, file_id, path) VALUES (?, ?, ?)", 
           (first_index, file_id, path)
        )

        self.commit()

        return file_id, first_index


    def similarity_search(self, q: str, k: int, file: bool = False) -> list[int]:
        if not file:
            tokens = clip.tokenize([q]).to(self.device)
            text_features = self.model.encode_text(tokens)

            text_np = text_features.detach().cpu().numpy()
            text_np = np.float32(text_np)

            faiss.normalize_L2(text_np)

            D, I = self.index.search(text_np, k)

            faiss_indices = list(I[0])
            print(D, I)

            Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"



            return Pipeline.order_by(self.db.execute(Q).fetchmany(k), I[0]), D

        else:
            file_ext = q.split('.')[-1]
            if file_ext.lower() in ['png', 'jpg', 'jpeg']:
                image = self.preprocess(Image.open(q)).unsqueeze(0).to(self.device)
            
                embeddings = self.model.encode_image(image)
                
                D, I = self.index.search(embeddings, k)
                faiss_indices = list(I[0])

                Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"
                

                return Pipeline.order_by(self.db.execute(Q).fetchall(),I[0]), D