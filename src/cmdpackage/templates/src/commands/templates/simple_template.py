#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

simple_template = Template(dedent("""from string import Template
from textwrap import dedent

simpleTemplate = Template(
    dedent(
        \"\"\"# Generated using simple template
from ..defs.logIt import printIt, lable

$${commandJsonDict}

def $${defName}(argParse):
    '''Simple $${defName} command implementation'''
    args = argParse.args
    arguments = args.arguments

    printIt(f"Running $${defName} command", lable.INFO)

    if len(arguments) == 0:
        printIt("No arguments provided", lable.WARN)
        return

    for i, arg in enumerate(arguments):
        printIt(f"Argument {i+1}: {arg}", lable.INFO)

\"\"\"
    )
)
"""))

