#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

modCmd_template = Template(dedent("""import os, copy, json, re, hashlib
from ..defs.logIt import printIt, lable
from ..defs.validation import (
    validate_argument_name,
    check_command_uses_argcmddef_template,
)
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdswitchFlags
from .commands import Commands
from .templates.argCmdDef import cmdDefTemplate
from .templates.argDefTemplate import argDefTemplate
import readline

commandJsonDict = {"commands_modCmd": {"description": "Command commands_modCmd", "switchFlags": {}}}

readline.parse_and_bind("tab: compleat")
readline.parse_and_bind("set editing-mode vi")


def update_sync_data_md5(file_path):
    \"\"\"Update the MD5 hash for a file in genTempSyncData.json\"\"\"
    try:
        # Get the project root (go up from commands dir to ${packName} dir, then to project root)
        commands_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(commands_dir)))
        sync_data_file = os.path.join(project_root, "genTempSyncData.json")

        if not os.path.exists(sync_data_file):
            # If genTempSyncData.json doesn't exist, no need to update
            return

        # Calculate new MD5 hash
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        # Load sync data
        with open(sync_data_file, "r") as f:
            sync_data = json.load(f)

        # Update MD5 for the file if it's tracked
        abs_file_path = os.path.abspath(file_path)
        if abs_file_path in sync_data:
            sync_data[abs_file_path]["fileMD5"] = file_hash

            # Save updated sync data
            with open(sync_data_file, "w") as f:
                json.dump(sync_data, f, indent=4)

            printIt(
                f"Updated MD5 hash for {os.path.basename(file_path)} in sync data",
                lable.INFO,
            )

    except Exception as e:
        printIt(f"Warning: Could not update sync data MD5: {e}", lable.WARN)


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
        # Combine regular arguments with option flags from cmd_options
        combined_args = list(args.arguments)

        # Add option flags to arguments for processing
        if hasattr(argParse, "cmd_options") and argParse.cmd_options:
            for option_name, option_value in argParse.cmd_options.items():
                if isinstance(option_value, bool):
                    # Boolean flag (single hyphen) - add regardless of value for flag definition
                    combined_args.append(f"-{option_name}")
                elif option_value == "__STRING_OPTION__" or not isinstance(option_value, bool):
                    # String option (double hyphen) - either has a value or is marked as string option
                    combined_args.append(f"--{option_name}")

        # Check if command uses argCmdDef template for validation
        uses_argcmddef = check_command_uses_argcmddef_template(modCmdName)
        theArgs, tracking = verifyArgsWithDiscriptions(cmdObj, combined_args, uses_argcmddef)
        # Check if there are actual modifications (excluding _optionFlags)
        actual_modifications = {k: v for k, v in theArgs.items() if k != "_optionFlags"}
        if len(actual_modifications) > 0 or (theArgs.get("_optionFlags") and len(theArgs["_optionFlags"]) > 0):
            updateCMDJson(cmdObj, modCmdName, theArgs)

            # If command uses argCmdDef template, add new argument functions to the .py file
            if uses_argcmddef:
                add_new_argument_functions(modCmdName, theArgs, tracking)

            # Save new option flags to .${packName}rc if any were added
            option_flags = theArgs.get("_optionFlags", {})
            if option_flags:
                # Extract flags for the command being modified
                new_cmd_flags = {}

                for option_name, flag_def in option_flags.items():
                    flag_type = flag_def.get("type", "str")
                    if flag_type == "bool":
                        # Boolean flag - save with default value False
                        new_cmd_flags[option_name] = False
                    elif flag_type == "str":
                        # String option - save with empty string default
                        new_cmd_flags[option_name] = ""

                # Save the flags to .${packName}rc using the saveCmdswitchFlags function
                if new_cmd_flags:
                    saveCmdswitchFlags(modCmdName, new_cmd_flags, option_flags)

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
    optionFlags = {}
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
        chgDisc = input(f"Replace description for {cmdName} (y/N): ")
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
            optionFlags[optionName] = {"description": theDict, "type": "str"}
            tracking["modified"].append(f"option {argName}")
        elif argName.startswith("-"):
            # Single hyphen option (boolean flag)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            theDict = input(f"Enter help description for flag {argName} (true/false):\\n")
            if theDict == "":
                theDict = f"Boolean flag {argName}"
            optionFlags[optionName] = {"description": theDict, "type": "bool"}
            tracking["modified"].append(f"flag {argName}")
        else:
            # Regular argument (not command description - that's handled above)
            theDict = ""
            saveDict = False

            if argName in cmdObj.commands[cmdName].keys():
                chgDisc = input(f"Replace description for {argName} (y/N): ")
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

    # Store option flags separately for later processing
    rtnDict["_optionFlags"] = optionFlags
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

    # Get list of newly added arguments (exclude command name, _optionFlags, and existing modifications)
    new_arguments = []
    modified_items = tracking.get("modified", [])

    for item in modified_items:
        if item.startswith("argument ") and not item.startswith("argument " + cmdName):
            # Extract argument name from "argument argname" format
            arg_name = item.replace("argument ", "")
            # Only add if this is a new argument (not command description modification)
            if arg_name != cmdName and arg_name in theArgs and arg_name != "_optionFlags":
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


def updateCMDJson(cmdObj: Commands, modCmdName: str, theArgs: dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())

    # Handle command description update if present
    if modCmdName in argNames:
        commands[modCmdName]["description"] = theArgs[modCmdName]
        argIndex = 1
    else:
        argIndex = 0

    # Handle option flags if they exist
    optionFlags = theArgs.get("_optionFlags", {})
    if optionFlags:
        # Initialize switchFlags if it doesn't exist
        if "switchFlags" not in commands[modCmdName]:
            commands[modCmdName]["switchFlags"] = {}
        # Add new option flags to the command's switchFlags
        commands[modCmdName]["switchFlags"].update(optionFlags)

    # Add regular arguments (skip _optionFlags)
    while argIndex < len(theArgs):
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry
        if argName != "_optionFlags":
            commands[modCmdName][argName] = theArgs[argName]
        argIndex += 1

    cmdObj.commands = commands

    # Update MD5 hash in genTempSyncData.json if it exists
    commands_json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "commands.json")
    update_sync_data_md5(commands_json_file)

    # Also update the source file's commandJsonDict
    updateSourceFileCommandJsonDict(modCmdName, commands[modCmdName])


def updateSourceFileCommandJsonDict(cmdName: str, cmdDict: dict) -> None:
    \"\"\"Update the commandJsonDict in the source file\"\"\"
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f"{cmdName}.py")

    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return

    # Read the current file content
    with open(fileName, "r") as fr:
        fileContent = fr.read()

    # Create the new commandJsonDict string
    newCommandJsonDict = {cmdName: cmdDict}
    jsonStr = json.dumps(newCommandJsonDict, indent=2)

    # Pattern to mtc the existing commandJsonDict
    pattern = r"commandJsonDict\\s*=\\s*\\{[^}]*\\}"

    # Check if it's a simple dict or nested dict
    if "{" in fileContent and "}" in fileContent:
        # Look for the commandJsonDict pattern with proper nesting
        lines = fileContent.split("\\n")
        start_line = -1
        end_line = -1
        brace_count = 0
        in_dict = False

        for i, line in enumerate(lines):
            if "commandJsonDict" in line and "=" in line and "{" in line:
                start_line = i
                in_dict = True
                brace_count = line.count("{") - line.count("}")
            elif in_dict:
                brace_count += line.count("{") - line.count("}")
                if brace_count == 0:
                    end_line = i
                    break

        if start_line != -1 and end_line != -1:
            # Replace the commandJsonDict section
            before_lines = lines[:start_line]
            after_lines = lines[end_line + 1 :]

            new_lines = before_lines + [f"commandJsonDict = {jsonStr}"] + after_lines

            # Write the updated content back to the file
            with open(fileName, "w") as fw:
                fw.write("\\n".join(new_lines))

            printIt(f"Updated commandJsonDict in {fileName}", lable.INFO)
        else:
            printIt(f"Could not find commandJsonDict pattern in {fileName}", lable.WARN)
"""))

