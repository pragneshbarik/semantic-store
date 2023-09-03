import sqlite3
import TextPipeline
import ImagePipeline
import AudioPipeline
from StoreObjects import *
from collections import defaultdict



# Multimodal searchs
# Allowed searchs
# str -> str    ~ done
# str -> image  ~ done
# str -> audio  ~ done
# str -> video  ~ done
# image -> image


# Left to implement
# image -> str
# image -> audio
# image -> video

# 



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
                file_path TEXT
                file_type TEXT
                faiss_start_indices TEXT
                faiss_end_indices TEXT
            )
            '''
        )

        self.commit()


    def multimodal_search(self, path: str, k: int, left: str, right: str) :
        pass
    
    def search(self, q: str, k: int) :
        s = StoreObject

        images, distances = self.image_pipeline.similarity_search(q, k)
        
        for image, dist in zip(images, distances) :
            image_object = ImageObject(image[1], image[2], dist)
            s.images.append(image_object)

        temp_texts, distances = self.text_pipeline.similarity_search(q, k)
        
        texts = []
        for text, d in zip(temp_texts, list(distances[0])) :
            texts.append(list(text) + [d])
        
        
        texts_dict = defaultdict(list)
        for text in texts :
            texts_dict[text[1]].append(text)

        for uuid in texts_dict :
            text_object = TextObject(uuid, texts_dict[uuid][0][2], [], [])
            for text in texts_dict[uuid] :
                text_object.chunks.append(text[3])
                text_object.distances.append(text[4])
            
            s.texts.append(text_object)

    


    def determine_modality(self, path: str):
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

       
        modality = self.determine_modality(path)

        if modality not in self.pipelines:
            print("Unsupported modality.")
            return

        pipeline = self.pipelines[modality]

        # Perform the insertion based on the determined modality
        if modality == "image":
            # Insert image data into the image pipeline
            file_id, first_index = pipeline.insert_file(path)
            self.db.execute(
                '''

'''                
            )
        elif modality == "text":
            # Insert text data into the text pipeline
            # You need to define how to process and insert text data into your pipeline
            pass
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




# text_pipeline = TextPipeline(faiss_uri='text.faiss', sqlite_uri='semantic.db')
image_pipeline = ImagePipeline(faiss_uri='image.faiss', sqlite_uri='semantic.db')

# image_pipeline.insert_file('cat.jpg')
# image_pipeline.insert_file('dog.jpeg')
# image_pipeline.insert_file('sky.jpeg')
print(image_pipeline.similarity_search("a black dog", 3))
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

