
import re
from BasePipeline import Pipeline
import torch
import numpy as np
import sqlite3
from sentence_transformers import SentenceTransformer
import faiss
import torch
import clip
import uuid
from PyPDF2 import PdfReader
from PIL import Image


class TextPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :

        self.chunk_size = 256 # word chunk size
        self.qa_faiss_uri = "qa_" + faiss_uri
        self.clip_faiss_uri = "clip_" + faiss_uri
        self.db_connection = sqlite3.connect(sqlite_uri)
        self.db = self.db_connection.cursor()
        
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS qa_text_table (
                faiss_id INTEGER PRIMARY KEY,
                document_id TEXT,
                text_data TEXT
            )
        ''')
    
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS clip_text_table (
                faiss_id INTEGER PRIMARY KEY,
                file_id TEXT,
                file_path TEXT,
                text_data TEXT
                        
        )
        ''')

        self.db_connection.commit()
        
        try :
            self.qa_index = faiss.read_index(self.qa_faiss_uri)
            self.clip_index = faiss.read_index(self.clip_faiss_uri)
        
        except RuntimeError:
            self.qa_index = faiss.IndexFlatL2(384)
            self.clip_index = faiss.IndexFlatL2(512)
            faiss.write_index(self.qa_index, self.qa_faiss_uri)
            faiss.write_index(self.clip_index, self.clip_faiss_uri)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.qa_model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
        self.clip_model, self.preprocess = clip.load("ViT-B/32", device=self.device)
    
    def commit(self) :
        self.db_connection.commit()
        faiss.write_index(self.qa_index, self.qa_faiss_uri)
        faiss.write_index(self.clip_index, self.clip_faiss_uri)


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
        embeddings = self.qa_model.encode(sentences)
        return np.array(embeddings).reshape(-1, 384)


    def insert_into_clip(self, path: str, document_id: str) -> [int, int]:
        file_ext = path.split('.')[-1]

        text = self.extract_text(path)
        sentences = self.split_text(text, 77)
        tokens = clip.tokenize(sentences).to(self.device)

        text_features = self.model.encode_text(tokens)

        embeddings = text_features.detach().cpu().numpy()
        embeddings = np.float32(embeddings)

        faiss.normalize_L2(embeddings)

        first_index = self.clip_index.ntotal
        self.clip_index.add(embeddings)
        last_index = self.clip_index.ntotal

        for i, sentence in enumerate(sentences) :
            self.db.execute(
                "INSERT INTO clip_text_table (faiss_id, file_id, file_path, text_data) VALUES (?, ?, ?, ?)",
                (first_index + i, document_id, path, sentence)
            )
        
        return first_index, last_index
    
    def insert_into_qa(self, path: str, document_id: str) -> [int, int]:
        text = self.extract_text(path)
        sentences = self.split_text(text, self.chunk_size)
        embeddings = self.encode_text(sentences)
        first_index = self.qa_index.ntotal
        self.qa_index.add(embeddings)
        last_index = self.qa_index.ntotal

        for i, sentence in enumerate(sentences) :
            self.db.execute(
                "INSERT INTO qa_text_table (faiss_id, file_id, path, text_data) VALUES (?, ?, ?, ?)",
                (first_index + i, document_id, sentence)
            )
        
        return first_index, last_index

    def insert_text(self, path: str) :
        # text = self.extract_text(path)
        document_id = str(uuid.uuid4())
        indices = {}
        indices['clip'] = self.insert_into_clip(path, document_id)
        indices['qa'] = self.insert_into_qa(path, document_id)

        self.commit()

        return document_id, indices
        
        
    def similarity_search(self, query: str, k: int) -> list[int]:
        '''
        Returns list of (faiss_id, file_id, path, text_data) and Distances ranked according to distances.
        
        '''
        
        query_embedding = self.qa_model.encode([query])
        D, I = self.qa_index.search(np.array(query_embedding).reshape(-1, 384), k)


        faiss_indices = list(I[0])

        Q = f"SELECT * FROM text_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"

        return Pipeline.order_by(self.db.execute(Q).fetchall(), I[0]) , D
    
    def search_via_image(self, path: str, k:int) :
        query_embedding = {}

        with torch.no_grad() :
            image = self.preprocess(Image.open(path)).unsqueeze(0).to(self.device)
            query_embedding[path] = self.clip_model.encode_image(image)
        
        embed_vector = query_embedding[path].detach().cpu().numpy()
        embed_vector = np.float32(embed_vector).reshape(-1, 512)

        faiss.normalize_L2(embed_vector)

        D, I = self.clip_index.search(embed_vector, k)
        faiss_indices = list(I[0])

        Q = f"SELECT * FROM clip_text_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"

        return Pipeline.order_by(self.db.execute(Q).fetchall(), I[0]) , D
    

    def search_via_text(self, query: str, k: int):
        query_embedding = self.qa_model.encode([query])
        D, I = self.qa_index.search(np.array(query_embedding).reshape(-1, 384), k)

        faiss_indices = list(I[0])

        Q = f"SELECT * FROM text_table WHERE faiss_id in ({','.join(map(str, faiss_indices))})"

        return Pipeline.order_by(self.db.execute(Q).fetchall(), I[0]) , D
    
    
