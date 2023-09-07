
import torch
import numpy as np
import sqlite3
from pipelines.BasePipeline import Pipeline
from sentence_transformers import SentenceTransformer
import faiss
import os
import torch
import clip
from PIL import Image
import uuid
from utils import *

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
    
    def encode_image(self, path: str) -> torch.Tensor :
        with torch.no_grad() :
            image = self.preprocess(image).unsqueeze(0).to(self.device)
            return self.model.encode_image(image)
            
    def encode_text(self, sentance: str) -> list[torch.Tensor] | np.ndarray | torch.Tensor:
        tokens = clip.tokenize([sentance]).to(self.device)
        with torch.no_grad() :
            text_features = self.model.encode_text(tokens)
            text_np = text_features.detach().cpu().numpy()
            text_np = np.float32(text_np)
            return text_np  



    def insert_file(self, path: str) -> tuple :
        file_id = str(uuid.uuid4())
        first_index = self.index.ntotal
        embeddings = self.encode_image(path)
        embed_vector = embeddings.detach().cpu().numpy()
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
            query_embeddings = self.encode_text(q) 
            faiss.normalize_L2(query_embeddings)
            D, I = self.index.search(query_embeddings, k)

            D, I = remove_neg_indexes(D, I)


            Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, I))})"

            return order_by(self.db.execute(Q).fetchall(), I), D

        else:
            file_ext = q.split('.')[-1]
            if file_ext.lower() in ['png', 'jpg', 'jpeg']:
                image = self.preprocess(Image.open(q)).unsqueeze(0).to(self.device)
            
                embeddings = self.model.encode_image(image)
                
                D, I = self.index.search(embeddings, k)

                arg_minus_one = np.where(I[0] == -1)[0]
                I = I[0][:arg_minus_one]
                D = D[0][:arg_minus_one]

                faiss_indices = list(I)


                Q = f"SELECT * FROM image_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"
                

                return order_by(self.db.execute(Q).fetchall(),I), D