import glob
import numpy as np
from abc import ABC, abstractmethod
import sqlite3
from sentence_transformers import SentenceTransformer, util
import faiss
import os

class Pipeline(ABC):

    @abstractmethod
    def scan(self) -> None:
        pass

    @abstractmethod
    def insert_one(self) -> int:
        pass

    @abstractmethod
    def search(self, query: str, k: int) -> list[int]:
        pass


class TextPipeline(Pipeline):
    def __init__(self, faiss_uri: str, sqlite_uri: str) -> None :
        
        # initialize sqlite db
        # db schema : [faiss_id, file_name, file_location, text_data]
        self.db_connection = sqlite3.connect(sqlite_uri)
        self.db = self.db_connection.cursor()
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS text_table (
                faiss_id INTEGER PRIMARY KEY,
                file_name TEXT,
                path TEXT,
                text_data TEXT
            )
        ''')


        self.db_connection.commit()
        
        # initialize faiss index
        try :
            self.index = faiss.read_index(faiss_uri)
            print("text index load success")
        
        except faiss.Exception as e:
            print("index does not exist")
            print("creating new index")
            self.index = faiss.IndexFlatL2(384)
            faiss.write_index(self.index, faiss_uri)

        # initialize 
        self.model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')




    def __extract_text(self, path: str) -> list[str] :
        # Logic for extracting text from documents such as pdfs and docx
        pass

    def __encode_text(self, text: list[str]):
        encodings = self.model.encode(text)
        return encodings


    def insert_one(self, file_name:str ,path: str) -> [int, int]:

        file_ext = path.split('.')[-1]

        sentances = self.__extract_text(path)
        encodings = self.__encode_text(sentances)

        last_index = self.index.ntotal

        for i, encoding in enumerate(encodings) :
            self.index.add(np.array([encoding]))
            self.db.execute(
                "INSERT INTO text_table (faiss_id, file_name, path, text_data) VALUES (?, ?, ?, ?)",
                (last_index + i, file_name, path, sentances[i])
            )
        
        self.db_connection.commit()

        return last_index, last_index + len(sentances)

class ImagePipeline(Pipeline):
    pass


class MediaPipeline(Pipeline):
    pass


class Driver:
    pass


def list_images():
    '''
    This function lists only image files in a directory
    Filters out only image files (JPEG, PNG, GIF, etc.)
    '''

=======

# Tasks
# 1. Install Anaconda, Pytorch,
# 2. Make a function to list all the images in directory recursively

def list_images():
    '''
    This function lists only image files in a directory
    Filters out only image files (JPEG, PNG, GIF, etc.)
    '''
    extensions = ["png","jpeg","jpg","svg","gif","pjp","avif","apng","webp","jfif","pjpeg"]
    images_files = []
    for e in extensions:
        f = glob.glob(f"**/*.{e}",recursive=True)
        if f:images_files.append(f)
    return images_files

# Test the function
#call the list_image function to search for images in cwd and subdirectories
images_list = list_images()

#display the found images
#additional conversion to str for better viewing experience
for image in images_list:
    img = str(image)[1:-1]
    print(img)