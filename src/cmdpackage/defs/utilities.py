import os

def chkDir(dirName: str):
    if not os.path.isdir(dirName):
        os.makedirs(dirName, exist_ok=True)