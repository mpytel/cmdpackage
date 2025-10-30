#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

argDefTemplateStr = dedent(
    """# Generated using argCmdDef template
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

cmdObj = Commands()
commands = cmdObj.commands

def ${defName}(argParse):
    global commands
    args = argParse.args
    theCmd = args.commands[0]
    theArgNames = list(commands[theCmd].keys())
    # filter out 'description'a 'switchFlags' from argument names
    theArgNames = [arg for arg in theArgNames if arg not in ['description', 'switchFlags']]
    theArgs = args.arguments
    argIndex = 0
    nonCmdArg = True
    # printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.DEBUG)
    # delete place holder code bellow that loops though arguments provided
    # when this command is called when not needed.
    # Note: that function having a name that is entered as an argument part
    # of this code and is called using the built in exec function. while argIndex < len(theArgs):
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands[theCmd]:
            nonCmdArg = False
            exec(f"{anArg}(argParse)")
        # process know and unknown aregument for this {packName} {defName} command
        elif nonCmdArg:
            if argIndex+1 > len(theArgNames):
                printIt(f"unknown argument: {anArg}", lable.INFO)
            else:
                printIt(f"{theArgNames[argIndex]}: {anArg}", lable.INFO)
        argIndex += 1
    if len(theArgs) == 0:
        printIt("no argument(s) entered", lable.INFO)

"""
)