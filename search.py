import os

# Tasks
# 1. Install Anaconda, Pytorch,
# 2. Make a function to list all the images in directory


def list_images(path):
    # this lists all files in a directory
    # make it such that it only lists images.
    return os.listdir(path)
