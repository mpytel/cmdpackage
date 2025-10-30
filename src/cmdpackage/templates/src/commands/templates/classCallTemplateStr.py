#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

classCallTemplateStr = dedent(
    """# Generated using classCall template
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

class ${defName}Command:
    def __init__(self, argParse):
        self.argParse = argParse
        self.cmdObj = Commands()
        self.commands = self.cmdObj.commands
        self.args = argParse.args
        self.theCmd = self.args.commands[0]
        self.theArgNames = list(self.commands[self.theCmd].keys())
        self.theArgs = self.args.arguments

    def execute(self):
        '''Main execution method for ${defName} command'''
        printIt(f"Executing {self.theCmd} command with class-based approach", lable.INFO)

        if len(self.theArgs) == 0:
            printIt("No arguments provided", lable.WARN)
            return

        argIndex = 0
        while argIndex < len(self.theArgs):
            anArg = self.theArgs[argIndex]
            method_name = f"handle_{anArg}"
            if hasattr(self, method_name):
                getattr(self, method_name)()
            else:
                printIt(f"Processing argument: {anArg}", lable.INFO)
            argIndex += 1

def ${defName}(argParse):
    '''Entry point for ${defName} command'''
    command_instance = ${defName}Command(argParse)
    command_instance.execute()

"""
)