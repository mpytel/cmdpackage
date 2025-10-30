#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

# This template is used for generating argument functions within other templates
argCmdDefTemplate = Template(dedent("""def ${argName}(argParse):
    args = argParse.args
    printIt("def ${defName} executed.", lable.INFO)
    printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.INFO)
    printIt(str(args), lable.INFO)

"""))
