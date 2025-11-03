#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

classCall_template = Template(dedent("""from string import Template
from textwrap import dedent

classCallTemplate = Template(
    dedent(
        \"\"\"# Generated using classCall template
import sys    
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

$${commandJsonDict}

class $${defName}Command:
    def __init__(self, argParse):
        self.argParse = argParse
        self.cmdObj = Commands()
        self.commands = self.cmdObj.commands
        self.args = argParse.args
        self.theCmd = self.args.commands[0]
        self.theArgNames = list(self.commands[self.theCmd].keys())
        self.theArgs = self.args.arguments
        self.module = sys.modules[__name__]

    def execute(self):
        \\"\\"\\"Main execution method for $${defName} command\\"\\"\\"
        
        theArgs = _filter_out_options(self.theArgs)

        argIndex = 0
        while argIndex < len(theArgs):
            anArg = theArgs[argIndex]
            method_name = str(anArg)
            if hasattr(self.module, method_name):
                # Dynamically calls use handle_ prefix to map to methods.
                getattr(self.module, method_name)(self.argParse)
            else:
                printIt(f"Processing argument: {anArg}", lable.INFO)
            argIndex += 1

        if len(self.theArgs) == 0:
            printIt("No arguments provided", lable.WARN)
            return

            
def _filter_out_options(args):
    \\"\\"\\"Filters out option flags(starting with - or +) from the argument list.\\"\\"\\"
    filtered_args = [arg for arg in args if not str(arg).startswith(("-", "+"))]
    return filtered_args

    
def $${defName}(argParse):
    \\"\\"\\"Entry point for $${defName} command\\"\\"\\"
    command_instance = $${defName}Command(argParse)
    command_instance.execute()
\"\"\"
    )
)
"""))

