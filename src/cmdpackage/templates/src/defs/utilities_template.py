#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

utilities_template = Template(dedent("""import os
import hashlib
from .logIt import printIt, lable, cStr, color


def calculate_md5(file_path: str) -> str:
    \"\"\"Calculate MD5 hash of a file\"\"\"
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        printIt(f"Error calculating MD5 for {file_path}: {e}", lable.ERROR)
        return ""


def walk_directory(directory: str) -> list[str]:
    \"\"\"Get a list of all files in the specified directory and its subdirectories\"\"\"
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list


def split_args(inlist, moreStartsWithList: list[str]) -> tuple[list[str], list[str]]:
    \"\"\"
    Split out option flags (starting with - or +) from the argument list.

    Returns a tuple containing two lists:
    - The first list contains arguments.
    - The second list contains option arguments.
    \"\"\"
    startsWithList = ("-", "+") + tuple(moreStartsWithList)
    theArgs = [arg for arg in inlist if not str(arg).startswith(startsWithList)]
    optList = [arg for arg in inlist if not str(arg).startswith(startsWithList)]
    return (theArgs, optList)
"""))

