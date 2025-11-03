#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

fileDiff_template = Template(dedent("""import sys
import os
import difflib
from difflib import unified_diff
from pathlib import Path
from ${packName}.defs.logIt import printIt, lable, cStr, color

import black
from black import FileMode
from black.report import NothingChanged

commandJsonDict = {
    "fileDiff": {
        "description": "Show the differnces between two files.",
        "origFile": "Original file name",
        "newFile": "New file name",
    }
}


def fileDiff(argParse):
    global commands
    args = argParse.args
    theArgs = args.arguments
    if len(theArgs) == 2:
        origFileName: str = theArgs[0]
        newFileName: str = theArgs[1]
        compare_python_files(origFileName, newFileName)


def compare_python_files(origFileName: str, newFileName: str, chkBlack=False) -> bool:
    \"\"\"
    Compares two Python files and prints their differences.
    Return True if no differenc found or error occred.

    Args:
        origFileName (str): The path to the first Python file (e.g., the original).
        newFileName (str): The path to the second Python file (e.g., the modified).
    \"\"\"
    rtnBool = False
    # 1. Validate file paths
    if not os.path.exists(origFileName):
        print(f"Error: File not found at '{origFileName}'", file=sys.stderr)
        return rtnBool
    if not os.path.exists(newFileName):
        print(f"Error: File not found at '{newFileName}'", file=sys.stderr)
        return rtnBool
    if not os.path.isfile(origFileName):
        print(f"Error: '{origFileName}' is not a file.", file=sys.stderr)
        return rtnBool
    if not os.path.isfile(newFileName):
        print(f"Error: '{newFileName}' is not a file.", file=sys.stderr)
        return rtnBool

    # 2. Read file contents as lists of lines
    try:
        with open(origFileName, "r", encoding="utf-8") as f1:
            lines1 = f1.readlines()
        with open(newFileName, "r", encoding="utf-8") as f2:
            lines2 = f2.readlines()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return rtnBool
    except UnicodeDecodeError:
        print(
            f"Error: Could not decode file with UTF-8. Try a different encoding if known.",
            file=sys.stderr,
        )
        return rtnBool

    # 3. Generate differences using difflib.unified_diff
    # unified_diff produces a diff in the unified format, like 'diff -u'
    # 'lineterm=' is important if readlines() keeps newlines, to avoid double spacing in output.
    diff = difflib.unified_diff(
        lines1, lines2, fromfile=origFileName, tofile=newFileName
    )
    # lineterm=''  # Ensures difflib doesn't add an extra newline if lines already have them

    # Convert diff generator to list to check if it has content
    diff_lines = list(diff)

    # 4. check if black foprmatting removes diff
    if chkBlack:
        # print('------------ chkBlack')
        diff_result = compare_black_diff(origFileName, newFileName)
        if diff_result:
            diff_lines = diff_result.splitlines(keepends=True)
        else:
            diff_lines = []

    if diff_lines:
        # 5. Print the differences with optional color coding
        print("\\n--- Differences ---")
        for line in diff_lines:
            # ANSI escape codes for coloring output in terminals
            if line.startswith("+"):
                print(f"\\033[92m{line}\\033[0m", end="")  # Green for added lines
            elif line.startswith("-"):
                print(f"\\033[91m{line}\\033[0m", end="")  # Red for removed lines
            elif line.startswith("@"):
                print(f"\\033[94m{line}\\033[0m", end="")  # Blue for hunk headers
            else:
                print(line, end="")  # Default color for context lines
        print("\\n" + "=" * 60 + "\\n")
        rtnBool = False  # Differences found
    else:
        print(f"No differences found between {origFileName} and {newFileName}.")
        rtnBool = True  # No differences found
    return rtnBool


def compare_black_diff(origFileName, newFileName):
    \"\"\"
    Returns the diff of a Python file after black formatting, as a string.
    Returns None if no changes are needed.
    \"\"\"
    orig_file_path = Path(origFileName)
    new_file_path = Path(newFileName)
    try:
        # Read the original content
        orig_code = orig_file_path.read_text(encoding="utf-8")

        # Format the code using Black
        orig_formatted_code = black.format_file_contents(
            orig_code, fast=True, mode=FileMode(line_length=88)
        )

        # Read the new content
        new_code = new_file_path.read_text(encoding="utf-8")

        # Format the code using Black
        new_formatted_code = black.format_file_contents(
            new_code, fast=True, mode=FileMode(line_length=88)
        )

        # Split the original and formatted code into lines
        original_lines = orig_formatted_code.splitlines(keepends=True)
        new_lines = new_formatted_code.splitlines(keepends=True)

        # Generate the unified diff
        diff = unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{origFileName}",
            tofile=f"b/{newFileName}",
        )
        if not diff:
            new_file_path.write_text(new_formatted_code, encoding="utf-8")
        return "".join(diff)

    except NothingChanged:
        return None
    except Exception as e:
        print(f"Error processing {new_file_path}: {e}")
        return None
"""))

