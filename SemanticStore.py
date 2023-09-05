import sqlite3
from TextPipeline import TextPipeline
from ImagePipeline import ImagePipeline
from AudioPipeline import AudioPipeline
from StoreObjects import *
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

    
    def search(self, q: str, k: int) :
        s = StoreObject()

        # only allow text to image search if tokens are less than 50
        # image_objects = self.text_to_image_search(q, k)
        # s.images = image_objects


        text_objects = self.text_to_text_search(q, k)
        s.texts = text_objects
        
        return s;
        


    


    def __determine_modality(self, path: str):
        # Implement a function to determine the modality based on the path
        # For example, you can check the file extension to determine the modality
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

        # Perform the insertion based on the determined modality
        if modality == "text":
            # Insert image data into the image pipeline
            file_id, first_index, last_index = pipeline.insert_file(path)
            self.db.execute(
                "INSERT INTO master_file_record (uuid, file_path, file_type, faiss_start_index, faiss_end_index) VALUES (?, ?, ?, ?, ?)",
                 (file_id, path, "text", first_index, last_index)               
            )
        elif modality == "image":
            file_id, first_index = pipeline.insert_file(path)
            self.db.execute(
                "INSERT INTO master_file_record (uuid, file_path, file_type, faiss_start_index, faiss_end_index) VALUES (?, ?, ?, ?, ?)",
                (file_id, path, "image", first_index, first_index)
            )
        elif modality == "audio":
            # Insert audio data into the audio pipeline
            # You need to define how to process and insert audio data into your pipeline
            pass
        else:
            print("Unsupported modality.")

        # Commit changes to the database
        self.commit()



    def commit(self) :
        self.image_pipeline.commit()
        self.audio_pipeline.commit()
        self.text_pipeline.commit()
        self.db_connection.commit()

    def sql(self) :
        return self.db





s = Store()
s.connect('some1.db')
s.insert('RAS_03_375.pdf')
s.commit()
res = s.search("hexapod gait robobot", 5)
for text in res.texts :
    print(text)


# image_pipeline = ImagePipeline(faiss_uri='image.faiss', sqlite_uri='semantic.db')

# # image_pipeline.insert_file('cat.jpg')
# # image_pipeline.insert_file('dog.jpeg')
# # image_pipeline.insert_file('sky.jpeg')
# print(image_pipeline.similarity_search("a black dog", 3))
# print(text_pipeline.ntotal)
# tick = time.time()
# embeds = text_pipeline.encode_text(["There are 7 wonders in the world", "I have a ball, and will play with dog", "a great pizza"])
# tock = time.time()
# print(shape, tock - tick)

# def list_images():
#     '''
#     This function lists only image files in a directory
#     Filters out only image files (JPEG, PNG, GIF, etc.)
#     '''
#     extensions = ["png","jpeg","jpg","svg","gif","pjp","avif","apng","webp","jfif","pjpeg"]
#     images_files = []
#     for e in extensions:
#         f = glob.glob(f"**/*.{e}",recursive=True)
#         if f:images_files.append(f)
#     return images_files

# # Test the function
# #call the list_image function to search for images in cwd and subdirectories
# images_list = list_images()

# #display the found images
# #additional conversion to str for better viewing experience
# for image in images_list:
#     img = str(image)[1:-1]
#     print(img)

