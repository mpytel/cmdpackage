#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

validation_template = Template(dedent("""\"\"\"
Validation utilities for command and argument names
\"\"\"

import keyword
import builtins
import os
from .logIt import printIt, lable


def is_python_keyword_or_builtin(name: str) -> bool:
    \"\"\"Check if a name is a Python keyword or built-in function/type\"\"\"
    return keyword.iskeyword(name) or hasattr(builtins, name)


def get_reserved_names() -> set:
    \"\"\"Get all reserved Python names that should not be used as function names\"\"\"
    reserved = set()

    # Add Python keywords
    reserved.update(keyword.kwlist)

    # Add built-in functions and types
    reserved.update(dir(builtins))

    # Add some common problematic names that might not be in builtins
    additional_reserved = {
        "exec",
        "eval",
        "compile",
        "globals",
        "locals",
        "vars",
        "dir",
        "help",
        "input",
        "print",
        "open",
        "file",
        "exit",
        "quit",
        "license",
        "copyright",
        "credits",
    }
    reserved.update(additional_reserved)

    return reserved


def validate_argument_name(arg_name: str, cmd_name: str | None = None) -> bool:
    \"\"\"
    Validate that an argument name is safe to use as a function name
    Returns True if valid, False if invalid
    \"\"\"
    if not arg_name:
        printIt("Argument name cannot be empty", lable.ERROR)
        return False

    # Check if it's a valid Python identifier
    if not arg_name.isidentifier():
        printIt(f"'{arg_name}' is not a valid Python identifier", lable.ERROR)
        return False

    # Check if it's a reserved name
    if is_python_keyword_or_builtin(arg_name):
        printIt(
            f"'{arg_name}' is a Python keyword or built-in name and cannot be used as a function name",
            lable.ERROR,
        )
        return False

    return True


def check_command_uses_argcmddef_template(cmd_name: str) -> bool:
    \"\"\"Check if a command file was generated using argCmdDef template\"\"\"
    file_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to src/${packName}
    file_path = os.path.join(file_dir, "commands", f"{cmd_name}.py")

    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r") as f:
            first_line = f.readline().strip()
            return "argCmdDef template" in first_line
    except Exception:
        return False


def validate_arguments_for_argcmddef(arg_names: list, cmd_name: str) -> list:
    \"\"\"
    Validate argument names for argCmdDef template usage
    Returns list of valid argument names, prints errors for invalid ones
    \"\"\"
    valid_args = []

    for arg_name in arg_names:
        if validate_argument_name(arg_name, cmd_name):
            valid_args.append(arg_name)
        else:
            printIt(f"Skipping invalid argument name: '{arg_name}'", lable.WARN)

    return valid_args
"""))

