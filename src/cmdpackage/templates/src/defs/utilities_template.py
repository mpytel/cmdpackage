#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

utilities_template = Template(dedent("""import hashlib
from .logIt import printIt, lable, cStr, color


def calculate_md5(file_path: str) -> str:
    \"\"\"Calculate MD5 hash of a file\"\"\"
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        printIt(f"Error calculating MD5 for {file_path}: {e}", lable.ERROR)
        return ""


def filter_out_options(inlist, moreStartsWithList: list[str]) -> list:
    \"\"\"Filters out option flags (starting with - or +) from the argument list.\"\"\"
    startsWithList = ("-", "+") + tuple(moreStartsWithList)
    filtered_args = [arg for arg in inlist if not str(arg).startswith(startsWithList)]
    return filtered_args
"""))

