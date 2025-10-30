#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

asyncDefTemplateStr = dedent(
    """# Generated using asyncDef template
import asyncio
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

async def ${defName}_async(argParse):
    '''Async implementation of ${defName} command'''
    args = argParse.args
    theCmd = args.commands[0]
    theArgs = args.arguments

    printIt(f"Starting async {theCmd} command", lable.INFO)

    if len(theArgs) == 0:
        printIt("No arguments provided", lable.WARN)
        return

    # Process arguments asynchronously
    tasks = []
    for arg in theArgs:
        tasks.append(process_argument_async(arg))

    results = await asyncio.gather(*tasks)
    printIt(f"Completed processing {len(results)} arguments", lable.PASS)

async def process_argument_async(arg):
    '''Process individual argument asynchronously'''
    # Simulate async work
    await asyncio.sleep(0.1)
    printIt(f"Processed: {arg}", lable.INFO)
    return arg

def ${defName}(argParse):
    '''Entry point for async ${defName} command'''
    asyncio.run(${defName}_async(argParse))

"""
)