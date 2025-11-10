#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

utilities_template = Template(dedent("""import os
import hashlib
import json
from pathlib import Path
from .logIt import printIt, lable, cStr, color


def get_visual_length(text: str) -> int:
    \"\"\"
    Get the visual length of text, excluding ANSI color codes.

    Args:
        text: Text that may contain ANSI color codes

    Returns:
        Visual length of the text as it appears in terminal
    \"\"\"
    import re

    # Remove ANSI escape sequences (color codes)
    ansi_escape = re.compile(r"\\x1B(?:[@-Z\\\\-_]|\\[[0-?]*[ -/]*[@-~])")
    clean_text = ansi_escape.sub("", text)
    return len(clean_text)


def format_wrapped_text(title: str, text: str, max_width: int = 80) -> str:
    \"\"\"
    Format text with proper wrapping and indentation after a title prefix.

    Args:
        title: The title prefix (e.g., "Description:", "  • +black/-black:")
        text: The text content to wrap
        max_width: Maximum line width including the lable prefix (default 80)

    Returns:
        Formatted string with proper wrapping and indentation

    The function accounts for the "INFO: " prefix that gets added by lable.INFO,
    so the actual content width is max_width - 6 characters.
    Indentation aligns with where the actual text content starts.
    \"\"\"
    # Account for "INFO: " prefix from lable.INFO
    lable_prefix_length = 6  # "INFO: " is 6 characters
    content_width = max_width - lable_prefix_length

    # Create the full title with space
    full_title_with_space = f"{title} "

    # Calculate visual position where content starts (after the title and space)
    # This needs to include the lable prefix since that's where content will actually appear
    title_visual_length = get_visual_length(title)
    content_start_pos = lable_prefix_length + title_visual_length + 1  # +1 for space after title

    # If title itself is too long, put text on next line with basic indentation
    if (title_visual_length + 1) >= content_width - 10:  # Leave some margin
        indent = " " * 4  # Basic 4-space indent
        wrapped_lines = []
        words = text.split()
        current_line = ""

        for word in words:
            if len(current_line + word) + 1 <= content_width - 4:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        result = full_title_with_space + "\\n"
        for line in wrapped_lines:
            result += indent + line + "\\n"
        return result.rstrip()

    # Normal wrapping logic
    words = text.split()
    lines = []

    # Start with title + space + first part of text
    current_line = full_title_with_space
    current_visual_length = title_visual_length + 1  # Position without INFO: prefix

    for word in words:
        # Calculate if adding this word would exceed the width
        word_length = len(word)
        space_needed = 1 if current_visual_length > (title_visual_length + 1) else 0
        test_length = current_visual_length + space_needed + word_length

        if test_length <= content_width:
            # Word fits on current line
            if current_visual_length == (title_visual_length + 1):
                # First word after title
                current_line += word
                current_visual_length += word_length
            else:
                # Add space + word
                current_line += " " + word
                current_visual_length += 1 + word_length
        else:
            # Word doesn't fit, start new line
            lines.append(current_line)

            # Create indent to align with content start position
            # The content should align with where text starts after "INFO: Title: "
            # So we need indent equal to the full visual position where content starts
            indent = " " * content_start_pos
            current_line = indent + word
            current_visual_length = content_start_pos + word_length

    # Add the last line
    if current_line:
        lines.append(current_line)

    return "\\n".join(lines)


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

