import os
import uuid
import requests
import sqlite3
from utils import * 
from StoreObjects import *
from collections import defaultdict
from pipelines.TextPipeline import TextPipeline
from pipelines.ImagePipeline import ImagePipeline
from pipelines.AudioPipeline import AudioPipeline
from models import Base, MasterFileRecord, DeletedIds, ImageRecord, TextRecord
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text as textQuery


class Store:
    def __init__(self) :
        self.__is_connected = False
        self.__db_connection = None
        self.__db = None

    
    def connect(self, store_uri: str) :
        base_uri = store_uri.split('.')[0]
        sql_uri = base_uri + '.db' 


        text_index = base_uri + '_text.faiss'
        image_index = base_uri + '_image.faiss'
        audio_index = base_uri + '_audio.faiss'

        self.__image_pipeline = ImagePipeline(faiss_uri=image_index, sql_uri=sql_uri)
        self.__text_pipeline = TextPipeline(faiss_uri=text_index, sql_uri=sql_uri)
        self.__audio_pipeline = AudioPipeline(faiss_uri=audio_index, sql_uri=sql_uri)

        self.__pipelines = {
            "image" : self.__image_pipeline,
            "text" : self.__text_pipeline,
            "audio" : self.__audio_pipeline
        }

        self.__db_connection = create_engine('sqlite:///' + sql_uri)
        Session = sessionmaker(bind=self.__db_connection)
        self.__db = Session()

        self.__is_connected = True

        Base.metadata.create_all(self.__db_connection)

        self.commit()


    def multimodal_search(self, path: str, k: int, left: str, right: str) :
        pass

    # def _text_to_text_search(self, q:str, k: int) :
    #     self.pipelines['text'].similarity_search(q, k)
    

    def _text_to_image_search(self, q:str, k: int) :

        if(len(split_text(q))<50) :
            images, distances = self.__image_pipeline.similarity_search(q, k)

            image_objects = []
            for image, dist in zip(images, distances):
                uuid = image[1]

                raw_sql = textQuery(f'''
                SELECT file_path FROM master_file_record WHERE uuid='{uuid}'
                ''')

                with self.__db_connection.connect() as connection :
                    file_path = connection.execute(raw_sql).fetchone()


                image_object = ImageObject(image[1], file_path[0], dist)
                image_objects.append(image_object)

        return image_objects
    
    def _text_to_text_search(self, q: str, k:int) :
        temp_texts, distances = self.__text_pipeline.similarity_search(q, k)
                
        texts = []
        for text, d in zip(temp_texts, list(distances)) :
            texts.append(list(text) + [d])
        
        texts_dict = defaultdict(list)
        for text in texts :
            texts_dict[text[1]].append(text)

        text_objects = []

        for uuid in texts_dict :
            raw_sql = textQuery(f'''
                SELECT file_path FROM master_file_record WHERE uuid='{uuid}'
            ''')

            with self.__db_connection.connect() as connection :
                file_path = connection.execute(raw_sql).fetchone()
            # print(file_path)
            text_object = TextObject(uuid, file_path[0], [], [])
            for text in texts_dict[uuid] :
                text_object.chunks.append(text[2])
                text_object.distances.append(text[3])
            
            text_objects.append(text_object)
        

        return TextObjects(text_objects)
            

    def _text_to_audio_search(self, q: str, k: int) :
        temp_audios, distances = self.__audio_pipeline.similarity_search(q, k)
                
        audios = []
        for audio, d in zip(temp_audios, list(distances)) :
            audios.append(list(audio) + [d])
        
        audio_dict = defaultdict(list)

        for audio in audios :
            audio_dict[audio[1]].append(audio)


        audio_objects = []

        for uuid in audio_dict :
            audio_object = AudioObject(uuid, audio_dict[uuid][0][2], [], [])
            for audio in audio_dict[uuid] :
                audio_object.chunks.append(audio[2])
                audio_object.distances.append(audio[3])
            
            audio_objects.append(audio_object)
        
        return AudioObjects(audio_objects)

    def _image_to_image_search(self, path: str, k:int) :
        images, distances = self.__image_pipeline.image_to_image_search(path, k)

        image_objects = []
        for image, dist in zip(images, distances):
            image_object = ImageObject(image[1], image[2], dist)
            image_objects.append(image_object)
        
        return image_objects

    def _audio_to_text_search(self, path: str, k:int) :
        pass



    def _audio_to_image_search(self, path: str, k: int):
        pass

    def _audio_to_audio_search(self, path: str, k: int) :
        pass

    
    def search(self, q: str, k: int, modals=['text']) :

        s = StoreObject()

        if 'image' in modals :
            image_objects = self._text_to_image_search(q, k)
            # print(image_objects)
            s.images = image_objects
        
        if 'text' in modals :
            text_objects = self._text_to_text_search(q, k)

            s.texts = text_objects

        if 'audio' in modals :
            audio_objects = self._text_to_audio_search(q, k)
            s.audios = audio_objects
            
        
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

    def __insert_into_master_file_record(self, file_id, file_path, modality):
        if self.__is_connected:
            record = MasterFileRecord(
                uuid=file_id,
                file_path=file_path,
                file_type=modality,
            )
            self.__db.add(record)
            self.commit()



    def __insert_local(self, path: str) :
        if not self.__is_connected:
            print("Not connected to the database. Call connect() first.")
            return

       
        modality = self.__determine_modality(path)


        if modality not in self.__pipelines:
            print("Unsupported modality.")
            return

        file_id = str(uuid.uuid4())
        pipeline = self.__pipelines[modality]
        file_id = pipeline.insert_file(path, file_id)
        

        self.__insert_into_master_file_record(file_id, path, modality)
        return file_id;

   
    def __insert_remote(self, uri: str):
        try:
            response = requests.get(uri)
            if response.status_code == 200:
                file_id = str(uuid.uuid4())
                content_type = response.headers.get('content-type')
                
                if content_type:
                    file_extension = content_type.split('/')[-1]
                else:
                    file_extension = os.path.splitext(uri)[1].strip('.')
                
                temp_filename = file_id + '.' + file_extension
                
                with open(temp_filename, 'wb') as temp_file:
                    temp_file.write(response.content)
                
                modality = self.__determine_modality(temp_filename)
                
                if modality not in self.__pipelines:
                    print("Unsupported modality.")
                    return

                pipeline = self.__pipelines[modality]
                file_id = pipeline.insert_file(temp_filename, file_id)

                self.__insert_into_master_file_record(file_id, uri, modality)
                os.remove(temp_filename)
                return file_id
                
            else:
                print("Failed to fetch remote file. Status code:", response.status_code)
                return None
        except Exception as e:
            print("Error inserting remote file:", str(e))
            return None


    def insert(self, path: str):
        if path.startswith(('http://', 'https://', 'ftp://')):  
            return self.__insert_remote(path)
        else:
            return self.__insert_local(path)



    
    def get(self, uuid: str):
        if self.__is_connected:
            result = self.__db.query(MasterFileRecord).filter_by(uuid=uuid).first()
            if result:
                f = FileObject(result.uuid, result.file_path, result.file_type)
                return f
            else:
                return None  # 

    def delete(self, uuid: str) :
        pass    



    def commit(self) :
        self.__image_pipeline.commit()
        self.__audio_pipeline.commit()
        self.__text_pipeline.commit()
        self.__db.commit()

    def _db(self) :
        return self.__db




