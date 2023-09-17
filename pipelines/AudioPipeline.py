
from pipelines.BasePipeline import Pipeline
import pipelines.TextPipeline as TextPipeline
import whisper
import torch
import numpy as np
import sqlite3
from sentence_transformers import SentenceTransformer
import faiss
import torch
from utils import *
import uuid
from models import Base, MasterFileRecord, DeletedIds, ImageRecord, TextRecord
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text



class AudioPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sql_uri: str) -> None :
        self.chunk_size = 256 # word chunk size
        self.qa_faiss_uri = "qa_" + faiss_uri
        self.__db_connection = create_engine('sqlite:///' + sql_uri)
        Session = sessionmaker(bind=self.__db_connection)
        self.__db = Session()
        
        try :
            self.index = faiss.read_index(faiss_uri)
        
        except RuntimeError:
            self.index = faiss.IndexFlatL2(384)
            faiss.write_index(self.index, faiss_uri)

        self.faiss_uri = faiss_uri
        self.whisper_model = whisper.load_model('tiny.en')
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    
    def commit(self) :
        self.__db.commit()
        faiss.write_index(self.index, self.faiss_uri)


    def encode_text(self, sentences: list[str]) -> list[torch.Tensor] | np.ndarray | torch.Tensor :
        embeddings = self.model.encode(sentences)
        return np.array(embeddings).reshape(-1, 384)

    def insert_into_qa(self, path: str, file_id: str) -> [int, int]:
        extracted_text = self.whisper_model.transribe(path)
        extracted_text = extracted_text['text']

        sentences = split_text(extracted_text)
        embeddings = self.encode_text(sentences)
        first_index = self.index.ntotal
        self.index.add(embeddings)
        last_index = self.index.ntotal

        for i, sentence in enumerate(sentences) :
            new_record = TextRecord(
                faiss_id=first_index + i,
                file_id=file_id,
                text_data=sentence
            )
            self.__db.add(new_record)

        
        return first_index, last_index
    

    def insert_file(self, path: str, file_id=None) -> tuple :
        if file_id == None :
            file_id = str(uuid.uuid4())
        self.insert_into_qa(path, file_id)
        self.commit()
        return file_id 
    


    def similarity_search(self, query: str, k: int) -> list[int]:
        '''
        Returns list of (faiss_id, file_id, path, text_data) and Distances ranked according to distances.
        
        '''
        
        query_embedding = self.model.encode([query])
        D, I = self.index.search(np.array(query_embedding).reshape(-1, 384), k)
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