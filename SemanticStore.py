import sqlite3
from pipelines.TextPipeline import TextPipeline
from pipelines.ImagePipeline import ImagePipeline
from pipelines.AudioPipeline import AudioPipeline
from StoreObjects import *
from utils import * 
from collections import defaultdict


class Store:
    def __init__(self) :
        self.__is_connected = False
        

    
    def connect(self, store_uri: str) :
        sql_uri = store_uri.split('.')[0]  + ".db"
        self.db_connection = sqlite3.connect(sql_uri)
        self.db = self.db_connection.cursor()


        text_index = sql_uri + '_text.faiss'
        image_index = sql_uri + '_image.faiss'

        self.image_pipeline = ImagePipeline(faiss_uri=image_index, sqlite_uri=sql_uri)
        self.text_pipeline = TextPipeline(faiss_uri=text_index, sqlite_uri=sql_uri)
        self.audio_pipeline = AudioPipeline(faiss_uri=text_index, sqlite_uri=sql_uri)

        self.pipelines = {
            "image" : self.image_pipeline,
            "text" : self.text_pipeline,
            "audio" : self.audio_pipeline
        }

        self.__is_connected = True

        self.db.execute(
        '''
        CREATE TABLE IF NOT EXISTS master_file_record (
            uuid TEXT PRIMARY KEY,
            file_path TEXT,
            file_type TEXT,
            faiss_start_index TEXT,
            faiss_end_index TEXT
        )
        '''
)


        self.commit()


    def multimodal_search(self, path: str, k: int, left: str, right: str) :
        pass
    

    def text_to_image_search(self, q:str, k: int) :

        if(len(TextPipeline.split_text(q))<50) :
            images, distances = self.image_pipeline.similarity_search(q, k)

            image_objects = []
            for image, dist in zip(images, distances):
                image_object = ImageObject(image[1], image[2], dist)
                image_objects.append(image_object)

        return image_objects
    
    def text_to_text_search(self, q: str, k:int) :
        temp_texts, distances = self.text_pipeline.similarity_search(q, k)
                
        texts = []
        for text, d in zip(temp_texts, list(distances[0])) :
            texts.append(list(text) + [d])
        
        texts_dict = defaultdict(list)
        for text in texts :
            texts_dict[text[1]].append(text)

        text_objects = []

        for uuid in texts_dict :
            text_object = TextObject(uuid, texts_dict[uuid][0][2], [], [])
            for text in texts_dict[uuid] :
                text_object.chunks.append(text[3])
                text_object.distances.append(text[4])
            
            text_objects.append(text_object)
        
        return text_objects
            

    def text_to_audio_search(self, q: str, k: int) :
        pass

    def image_to_image_search(self, path: str, k:int) :
        pass

    def audio_to_text_search(self, path: str, k:int) :
        pass

    def audio_to_image_search(self, path: str, k: int):
        pass

    def audio_to_audio_search(self, path: str, k: int) :
        pass

    
    def search(self, q: str, k: int, modals=['text']) :
        s = StoreObject()

        if 'image' in modals :
            image_objects = self.text_to_image_search(q, k)
            s.images = image_objects
        
        if 'text' in modals :
            text_objects = self.text_to_text_search(q, k)
            s.texts = text_objects

        if 'audio' in modals :
            pass
            
        
        return s;
        

    def __determine_modality(self, path: str):
        file_extension = path.split(".")[-1].lower()
        if file_extension in ["jpg", "jpeg", "png"]:
            return "image"
        elif file_extension in ["txt", "pdf"]:
            return "text"
        elif file_extension in ["mp3", "wav", "flac"]:
            return "audio"
        else:
            return "unsupported"  # Modify as needed for your specific use case

    def insert(self, path: str):
        if not self.__is_connected:
            print("Not connected to the database. Call connect() first.")
            return

       
        modality = self.__determine_modality(path)

        if modality not in self.pipelines:
            print("Unsupported modality.")
            return

        pipeline = self.pipelines[modality]
        res = ""


        if modality == "text":
            # Insert image data into the image pipeline
            file_id, first_index, last_index = pipeline.insert_file(path)
            self.db.execute(
                "INSERT INTO master_file_record (uuid, file_path, file_type, faiss_start_index, faiss_end_index) VALUES (?, ?, ?, ?, ?)",
                 (file_id, path, "text", first_index, last_index)               
            )
            res = file_id
            
        elif modality == "image":
            file_id, first_index = pipeline.insert_file(path)
            self.db.execute(
                "INSERT INTO master_file_record (uuid, file_path, file_type, faiss_start_index, faiss_end_index) VALUES (?, ?, ?, ?, ?)",
                (file_id, path, "image", first_index, first_index)
            )
            res = file_id

            
        elif modality == "audio":
            file_id, first_index, last_index = pipeline.insert_file(path)

            self.db.execute(
                "INSERT INTO master_file_record (uuid, file_path, file_type, faiss_start_index, faiss_end_index) VALUES (?, ?, ?, ?, ?)",
                (file_id, path, "audio", first_index, last_index)
            )
            res = file_id

            
        else:
            raise FileNotFoundError(path)
        self.commit()
        return res;



    def commit(self) :
        self.image_pipeline.commit()
        self.audio_pipeline.commit()
        self.text_pipeline.commit()
        self.db_connection.commit()

    def sql(self) :
        return self.db




# import Store from SemanticStore

s = Store()
s.connect('some2.db')
# s.insert('RAS_03_375.pdf')
s.commit()
res = s.search("hexapod gait robobot", 5)

print(res)
