#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

modCmd_template = Template(dedent("""import os, copy, json, re
from ..defs.logIt import printIt, lable
from ..defs.validation import (
    validate_argument_name,
    check_command_uses_argcmddef_template,
)
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdSwitchOptions
from ..classes.CommandManager import command_manager
from .commands import Commands
from .templates.argCmdDef import cmdDefTemplate
from .templates.argDefTemplate import argDefTemplate
import readline

commandJsonDict = {
    "modCmd": {
        "description": "Modify a command or argument descriptions, or add another argument for command. The cmdName.py file will not be modified.",
        "option_switches": {},
        "option_strings": {},
        "arguments": {
            "cmdName": "Name of command being modified",
            "argName": "(argName...) Optional names of argument(s) to modify.",
        },
    }
}

readline.parse_and_bind("tab: compleat")
readline.parse_and_bind("set editing-mode vi")


cmdObj = Commands()
commands = cmdObj.commands


def modCmd(argParse: ArgParse):
    args = argParse.args
    cmdObj = Commands()
    argsDict = args.arguments

    if len(argsDict) == 0:
        printIt("Command name required", lable.ERROR)
        return

    modCmdName = args.arguments[0]
    if modCmdName in cmdObj.commands.keys():
        # Combine regular arguments with option values from cmd_options
        combined_args = list(args.arguments)

        # Add option values to arguments for processing
        if hasattr(argParse, "cmd_options") and argParse.cmd_options:
            for option_name, option_value in argParse.cmd_options.items():
                if isinstance(option_value, bool):
                    # Boolean option (single hyphen) - add regardless of value for option definition
                    combined_args.append(f"-{option_name}")
                elif option_value == "__STRING_OPTION__" or not isinstance(option_value, bool):
                    # String option (double hyphen) - either has a value or is marked as string option
                    combined_args.append(f"--{option_name}")

        # Check if command uses argCmdDef template for validation
        uses_argcmddef = check_command_uses_argcmddef_template(modCmdName)
        theArgs, tracking = verifyArgsWithDiscriptions(cmdObj, combined_args, uses_argcmddef)
        # Check if there are actual modifications (excluding _option_details)
        actual_modifications = {k: v for k, v in theArgs.items() if k != "_option_details"}
        if len(actual_modifications) > 0 or (theArgs.get("_option_details") and len(theArgs["_option_details"]) > 0):
            # updateCMDJson(cmdObj, modCmdName, theArgs)
            command_manager.update_command_json(cmdObj, theArgs, cmd_name=modCmdName, mode="modify")

            # If command uses argCmdDef template, add new argument functions to the .py file
            if uses_argcmddef:
                add_new_argument_functions(modCmdName, theArgs, tracking)

            # Save new option details to .${packName}rc if any were added
            option_details = theArgs.get("_option_details", {})
            if option_details:
                # Extract options for the command being modified
                new_cmd_options = {}

                for option_name, option_def in option_details.items():
                    option_type = option_def.get("type", "str")
                    if option_type == "bool":
                        # Boolean option - save with default value False
                        new_cmd_options[option_name] = False
                    elif option_type == "str":
                        # String option - save with empty string default
                        new_cmd_options[option_name] = ""

                # Save the options to .${packName}rc using the saveCmdSwitchOptions function
                if new_cmd_options:
                    saveCmdSwitchOptions(modCmdName, new_cmd_options, option_details)

            # Print detailed modification results
            print_modification_results(modCmdName, tracking)
        else:
            # Check if anything was requested but all rejected
            if len(tracking["requested"]) > 0:
                if len(tracking["rejected"]) == len(tracking["requested"]):
                    printIt(
                        f'All requested modifications for "{modCmdName}" were rejected.',
                        lable.WARN,
                    )
                else:
                    printIt(f'"{modCmdName}" unchanged.', lable.INFO)
            else:
                printIt(f'"{modCmdName}" unchanged.', lable.INFO)
    else:
        printIt(f'"{modCmdName}" does not exists. use newCmd or add it.', lable.INFO)


def print_modification_results(cmd_name: str, tracking: dict) -> None:
    \"\"\"Print detailed results of modification operations\"\"\"
    modified = tracking.get("modified", [])
    rejected = tracking.get("rejected", [])
    requested = tracking.get("requested", [])

    if len(modified) > 0:
        if len(modified) == 1:
            printIt(f'"{cmd_name}" - modified {modified[0]}.', lable.ModCmd)
        else:
            mod_list = ", ".join(modified)
            printIt(f'"{cmd_name}" - modified {mod_list}.', lable.ModCmd)

    # Only show rejection summary if some items were modified (mixed results)
    if len(rejected) > 0 and len(modified) > 0:
        if len(rejected) == 1:
            printIt(f"Note: {rejected[0]} was rejected.", lable.INFO)
        else:
            rej_list = ", ".join(rejected)
            printIt(f"Note: {rej_list} were rejected.", lable.INFO)


def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs, uses_argcmddef: bool = False) -> tuple[dict, dict]:
    rtnDict = {}
    option_details = {}
    cmdName = theArgs[0]

    # Track what was processed vs rejected
    tracking = {"modified": [], "rejected": [], "requested": []}

    # First pass: validate all arguments and separate them by type
    valid_args = []
    for argIndex in range(len(theArgs)):
        argName = theArgs[argIndex]

        # Track all requested items (skip command name)
        if argIndex > 0:
            tracking["requested"].append(argName)

            # Pre-validate regular arguments for argCmdDef template
            if not argName.startswith("-") and uses_argcmddef:
                if not validate_argument_name(argName, cmdName):
                    printIt(
                        f"Skipping invalid argument '{argName}' - cannot be used as function name",
                        lable.WARN,
                    )
                    tracking["rejected"].append(f"argument {argName}")
                    continue

            valid_args.append((argIndex, argName))

    # Special case: if only command name provided, handle command description modification
    if len(theArgs) == 1:
        cmdName = theArgs[0]
        chgDisc = input(f"Replace description for {cmdName} (y/N): \\n")
        if chgDisc.lower() == "y":
            theDict = input(f"Enter help description for argument {cmdName}:\\n")
            if theDict == "":
                theDict = f"no help for {cmdName}"
            rtnDict[cmdName] = theDict
            tracking["modified"].append(f"command {cmdName}")

    # Second pass: process only valid arguments with prompts
    for argIndex, argName in valid_args:
        saveDict = False

        if argName.startswith("--"):
            # Double hyphen option (stores value)
            if len(argName) <= 2:
                printIt("Missing option name after double hyphen.", lable.WARN)
                exit(0)
            optionName = argName[2:]  # Remove --
            theDict = input(f"Enter help description for option {argName} (stores value):\\n")
            if theDict == "":
                theDict = f"Value option {argName}"
            option_details[optionName] = {"description": theDict, "type": "str"}
            tracking["modified"].append(f"option {argName}")
        elif argName.startswith("-"):
            # Single hyphen option (boolean option)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            theDict = input(f"Enter help description for option {argName} (true/false):\\n")
            if theDict == "":
                theDict = f"Boolean option {argName}"
            option_details[optionName] = {"description": theDict, "type": "bool"}
            tracking["modified"].append(f"option {argName}")
        else:
            # Regular argument (not command description - that's handled above)
            theDict = ""
            saveDict = False

            if argName in cmdObj.commands[cmdName].keys():
                chgDisc = input(f"Replace description for {argName} (y/N): \\n")
                if chgDisc.lower() == "y":
                    saveDict = True
            else:  # add new arg
                saveDict = True
                newArg = True

            if saveDict:
                theDict = input(f"Enter help description for argument {argName}:\\n")
                if theDict == "":
                    theDict = f"no help for {argName}"
                # only populate rtnDict with modified descriptions
                rtnDict[argName] = theDict
                tracking["modified"].append(f"argument {argName}")

        argIndex += 1

    # Store option details separately for later processing
    rtnDict["_option_details"] = option_details
    return rtnDict, tracking


def writeCodeFile(theArgs: dict) -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f"{list(theArgs.keys())[0]}.py")
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs)
        with open(fileName, "w") as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr


def cmdCodeBlock(theArgs: dict) -> str:
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defTemp = cmdDefTemplate
    argTemp = argDefTemplate
    rtnStr = defTemp.substitute(defName=defName)
    argIndex = 1
    while argIndex < len(argNames):  # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argTemp.substitute(argName=theArgs[argName])
        argIndex += 1
    return rtnStr


def add_new_argument_functions(cmdName: str, theArgs: dict, tracking: dict) -> None:
    \"\"\"Add new argument functions to the command's .py file if using argCmdDef template\"\"\"

    # Get list of newly added arguments (exclude command name, _option_details, and existing modifications)
    new_arguments = []
    modified_items = tracking.get("modified", [])

    for item in modified_items:
        if item.startswith("argument ") and not item.startswith("argument " + cmdName):
            # Extract argument name from "argument argname" format
            arg_name = item.replace("argument ", "")
            # Only add if this is a new argument (not command description modification)
            if arg_name != cmdName and arg_name in theArgs and arg_name != "_option_details":
                new_arguments.append(arg_name)

    if not new_arguments:
        return

    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f"{cmdName}.py")

    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return

    # Read the current file content
    with open(fileName, "r") as fr:
        fileContent = fr.read()

    # Generate new function definitions using argDefTemplate
    new_functions = ""
    for argName in new_arguments:
        # Create function definition using the template
        argDescription = theArgs.get(argName, f"no help for {argName}")
        function_code = argDefTemplate.substitute(
            argName=argName, defName=cmdName, packName="${packName}"  # Use the package name
        )
        new_functions += function_code

    # Append new functions to the end of the file
    if new_functions:
        updated_content = fileContent + "\\n" + new_functions

        # Write the updated content back to the file
        with open(fileName, "w") as fw:
            fw.write(updated_content)

        arg_list = ", ".join(new_arguments)
        printIt(f"Added function definitions for arguments: {arg_list}", lable.INFO)
"""))

