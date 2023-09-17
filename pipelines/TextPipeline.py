
import re
from pipelines.BasePipeline import Pipeline
import torch
import numpy as np
import sqlite3
from sentence_transformers import SentenceTransformer
import faiss
import torch
import clip
import uuid
from utils import *
from PIL import Image
from models import Base, MasterFileRecord, DeletedIds, ImageRecord, TextRecord
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text




class TextPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sql_uri: str) -> None :

        self.chunk_size = 256 # word chunk size
        self.__db_connection = create_engine('sqlite:///' + sql_uri)
        Session = sessionmaker(bind=self.__db_connection)
        self.__db = Session()
        
    
        
        try :
            self.qa_index = faiss.read_index(self.faiss_uri)
        
        except RuntimeError:
            self.qa_index = faiss.IndexFlatL2(384)
            faiss.write_index(self.qa_index, self.faiss_uri)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.qa_model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    
    def commit(self) :
        self.__db.commit()
        faiss.write_index(self.qa_index, self.faiss_uri)

    def fetch_indexes(self, file_id) :
        query = self.__db.query(TextRecord.faiss_id).filter_by(file_id=file_id) 
        res = query.all()
        result_values = [row[0] for row in res]
        return result_values

    
    def encode_text(self, sentences: list[str]) -> list[torch.Tensor] | np.ndarray | torch.Tensor:
        embeddings = self.qa_model.encode(sentences)
        return np.array(embeddings).reshape(-1, 384)


    
    
    def insert_into_qa(self, path: str, file_id: str) -> [int, int]:
        text = extract_text(path)
        sentences = split_text(text, self.chunk_size)
        embeddings = self.encode_text(sentences)
        first_index = self.qa_index.ntotal
        self.qa_index.add(embeddings)
        last_index = self.qa_index.ntotal

        for i, sentence in enumerate(sentences) :
            new_record = TextRecord(
                faiss_id=first_index + i,
                file_id=file_id,
                text_data=sentence
            )
            self.__db.add(new_record)

        
        return first_index, last_index

    def insert_file(self, path: str, file_id=None) :
        if file_id==None :
            file_id = str(uuid.uuid4())

        self.insert_into_qa(path, file_id)
        self.commit()

        return file_id
    
    def insert_text(self, text: str) :
        document_id = str(uuid.uuid4())
        sentences = split_text(text, self.chunk_size)
        embeddings = self.encode_text(sentences)
        first_index = self.qa_index.ntotal
        self.qa_index.add(embeddings)
        last_index = self.qa_index.ntotal

        for i, sentence in enumerate(sentences) :
            self.db.execute(
                "INSERT INTO qa_text_table (faiss_id, file_id, file_path, text_data) VALUES (?, ?, ?, ?)",
                (first_index + i, document_id, sentence)
            )
        
    def similarity_search(self, query: str, k: int) -> list[int]:
        query_embedding = self.qa_model.encode([query])
        D, I = self.qa_index.search(np.array(query_embedding).reshape(-1, 384), k)
        D, I = remove_neg_indexes(D, I)
        print(D, I)

        if len(I) > 0:

            raw_sql = text(f'''
                SELECT *
                FROM text_table
                WHERE faiss_id IN ({', '.join(map(str, I))})
            ''')

            # Execute the raw SQL query
            with self.__db_connection.connect() as connection:
                result = connection.execute(raw_sql).fetchall()

            print(result)
            sorted_records = order_by(result, I)

            return sorted_records, D

        else:
            return [], []

    
    def image_to_text_search(self, path: str, k:int) :
        query_embedding = { }

        with torch.no_grad() :
            image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
            query_embedding[path] = self.clip_model.encode_image(image)
        
        embed_vector = query_embedding[path].detach().cpu().numpy()
        embed_vector = np.float32(embed_vector).reshape(-1, 512)

        faiss.normalize_L2(embed_vector)

        D, I = self.clip_index.search(embed_vector, k)
        D, I = remove_neg_indexes(D, I)

        if(len(I) > 0) :
            Q = f"SELECT * FROM qa_text_table WHERE faiss_id in ({','.join(map(str, I))})"
            return order_by(self.db.execute(Q).fetchall(), I) , D
        else:
            return [], []
    




