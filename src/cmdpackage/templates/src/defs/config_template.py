#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

config_template = Template(dedent("""import os
from io import StringIO
from dotenv import dotenv_values  # Using a standard library for parsing .env syntax

# NOTE: This implementation relies on the 'dotenv-values' package
# for safe, reliable .env file parsing. If you need 100% pure
# standard library function, you would have to write the parser yourself.


def config(setting_name, default=None, config_file=".env"):
    \"\"\"
    Reads a configuration setting from:
    1. Environment variables.
    2. A specified .env file.
    3. Returns the provided default value if not found.

    Args:
        setting_name (str): The name of the environment variable/setting.
        default (any): The fallback value if the setting is not found.
        config_file (str): The path to the .env file.

    Returns:
        str: The retrieved configuration value.
    \"\"\"

    # 1. Check Environment Variables (Highest Priority)
    if setting_name in os.environ:
        return os.environ[setting_name]

    # 2. Check the .env file
    try:
        # dotenv_values handles complex .env syntax (quotes, comments, etc.)
        env_vars = dotenv_values(config_file)
        if setting_name in env_vars:
            return env_vars[setting_name]
    except FileNotFoundError:
        # If the .env file doesn't exist, ignore and proceed
        pass

    # 3. Return Default Value (Lowest Priority)
    if default is not None:
        return default

    # If no value is found and no default is provided, raise an error
    raise KeyError(f"Setting '{setting_name}' not found in environment, .env file, and no default provided.")
"""))

