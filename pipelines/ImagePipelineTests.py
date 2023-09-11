from PIL import Image

from ImagePipeline import ImagePipeline
i = ImagePipeline('some2.db_image.faiss','some2.db')
# Assuming you have an instance of your class defined as 'semantic_store'
# and your similarity_search function is defined within that class.
# i.insert_file('cat.jpg')
# i.insert_file('dog.jpeg')
# i.insert_file('sky.jpeg')
# i.commit()
# Example query image file path / query text 
query_image_path = 'serious' #output image is of cat

# Specify the number of similar images you want to retrieve (k)
k = 3 # Adjust this based on your desired number of results

# Perform the image-to-image similarity search
similar_images, distances = i.similarity_search(query_image_path, k)

# 'similar_images' will contain a list of similar images, and 'distances' will contain their distances.

# You can iterate through the results and process them as needed.
for i, (image_data, distance) in enumerate(zip(similar_images, distances)):
    # 'image_data' contains information about each similar image.
    # 'distance' contains the similarity distance.
    
    # Process and display the results as needed.
    print(f"Result {i + 1}:")
    print(f"Distance: {distance}")
    # Process and display image_data, which contains information about the similar image.
    # Example: image_id, image_path, etc.
    similar_image = Image.open(image_data[2])
    similar_image.show()
    # Optionally, load and display the similar image using image_data['image_path']
    # Example: similar_image = Image.open(image_data['image_path'])
    # Example: similar_image.show()