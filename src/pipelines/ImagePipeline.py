
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
from models import Base, MasterFileRecord, DeletedIds, ImageRecord
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text

class ImagePipeline :

    def __init__(self, faiss_uri: str, sql_uri: str) -> None :
        self.__db_connection = create_engine('sqlite:///' + sql_uri)
        Session = sessionmaker(bind=self.__db_connection)
        self.__db = Session()
            
        try :
            self.index = faiss.read_index(faiss_uri)
        
        except RuntimeError:
            self.index = faiss.IndexFlatL2(512)
            faiss.write_index(self.index, faiss_uri)

        self.faiss_uri = faiss_uri
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

  

    def commit(self) :
        self.__db.commit()
        faiss.write_index(self.index, self.faiss_uri)
    
    def encode_image(self, path: str) -> torch.Tensor :
        with torch.no_grad() :
            image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
            return self.model.encode_image(image)
            
    def encode_text(self, sentance: str) -> list[torch.Tensor] | np.ndarray | torch.Tensor:
        tokens = clip.tokenize([sentance]).to(self.device)
        with torch.no_grad() :
            text_features = self.model.encode_text(tokens)
            text_np = text_features.detach().cpu().numpy()
            text_np = np.float32(text_np)
            return text_np  



    def fetch_indexes(self, file_id) :
        query = self.__db.query(ImageRecord.faiss_id).filter_by(file_id=file_id) 
        res = query.all()
        result_values = [row[0] for row in res]
        return result_values

    def insert_file(self, path: str, file_id = None) -> tuple :
        if file_id == None :
            file_id = str(uuid.uuid4())
        
        first_index = self.index.ntotal
        embeddings = self.encode_image(path)
        embed_vector = embeddings.detach().cpu().numpy()
        embed_vector = np.float32(embed_vector)
        faiss.normalize_L2(embed_vector)
        self.index.add(embed_vector)
        
        

        new_record = ImageRecord(
            faiss_id=first_index,
            file_id=file_id,
        )
        self.__db.add(new_record)


        self.commit()

        return file_id

    def image_to_image_search(self, path: str, k: int) :
        file_ext = path.split('.')[-1]
        if file_ext.lower() in ['png', 'jpg', 'jpeg']:
            image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
    
            query_embedding = self.model.encode_image(image)

            D, I = self.qa_index.search(np.array(query_embedding).reshape(-1, 512), k)
            D, I = remove_neg_indexes(D, I)

            if len(I) > 0:
                raw_sql = text(f'''
                SELECT *
                FROM image_table
                WHERE faiss_id IN ({', '.join(map(str, I))})
                ''')

                with self.__db_connection.connect() as connection:
                    result = connection.execute(raw_sql).fetchall()
            
                print(result)
                sorted_records = order_by(result, I)

                return sorted_records, D
            else:
                return [], []



    def similarity_search(self, q: str, k: int, file: bool = False) -> list[int]:
        query_embedding = self.encode_text(q)
        D, I = self.index.search(np.array(query_embedding).reshape(-1, 512), k)
        D, I = remove_neg_indexes(D, I)
        print(D, I)

        if len(I) > 0:
            raw_sql = text(f'''
                SELECT *
                FROM image_table
                WHERE faiss_id IN ({', '.join(map(str, I))})
            ''')

            with self.__db_connection.connect() as connection:
                result = connection.execute(raw_sql).fetchall()
            
            print(result)
            sorted_records = order_by(result, I)

            return sorted_records, D
        else:
            return [], []
