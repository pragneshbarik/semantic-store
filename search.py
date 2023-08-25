import os
import fnmatch

# Tasks
# 1. Install Anaconda, Pytorch,
# 2. Make a function to list all the images in directory

def list_images(path):
    # This function lists only image files in a directory
    # List all files in the directory
    all_files = os.listdir(path)
    
    # Filter out only image files (JPEG, PNG, GIF, etc.)
    image_files = [f for f in all_files if fnmatch.fnmatch(f, '*.jpg') or fnmatch.fnmatch(f, '*.jpeg') or fnmatch.fnmatch(f, '*.png') or fnmatch.fnmatch(f, '*.gif') or fnmatch.fnmatch(f, '*.svg') or fnmatch.fnmatch(f, '*.webp') or fnmatch.fnmatch(f, '*.apng') or fnmatch.fnmatch(f, '*.avif') or fnmatch.fnmatch(f, '*.jfif') or fnmatch.fnmatch(f, '*.pjpeg')or fnmatch.fnmatch(f, '*.pjp')]
    
    return image_files

# Test the function
#get the current working directory
directory_path = str(os.getcwd())

#call the list_image function to search for images in cwd
images_list = list_images(directory_path)

#display the found images in a list
print(images_list)
