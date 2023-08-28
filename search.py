import glob

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