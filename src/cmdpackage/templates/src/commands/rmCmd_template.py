#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

rmCmd_template = Template(dedent("""import os, json, hashlib
from ..defs.logIt import printIt, lable, cStr, color
from ..classes.optSwitches import removeCmdSwitchOptions
from ..classes.CommandManager import command_manager
from .commands import Commands

commandJsonDict = {
    "rmCmd": {
        "description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
        "option_switches": {"d": "Silently rm the command"},
        "option_strings": {},
        "arguments": {
            "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
            "argName": "Optional names of argument to remove.",
        },
    }
}
cmdObj = Commands()
commands = cmdObj.commands


def rmCmd(argParse):
    # Check for +d flag (silent mode) using unconventional persistence storage model
    # -d = silence OFF (prompts), +d = silence ON (no prompts)
    use_silent_mode = hasattr(argParse, "cmd_options") and argParse.cmd_options.get("d", False)

    # Reload commands to get current state
    cmdObj = Commands()
    commands = cmdObj.commands

    args = argParse.args
    theArgs = args.arguments

    if len(theArgs) == 0:
        printIt("Command name required", lable.ERROR)
        return

    cmdName = theArgs[0]

    # CRITICAL BUG FIX: Check if we have cmd_options that represent flags to remove
    # When user runs "${packName} rmCmd tmplMgt --desc", the --desc gets parsed as cmd_options
    # rather than being passed as an argument, so we need to handle both cases
    flags_to_remove = []
    if hasattr(argParse, "cmd_options") and argParse.cmd_options:
        for flag_name, flag_value in argParse.cmd_options.items():
            # Skip the 'd' flag which is for rmCmd itself (silent mode)
            if flag_name != "d":
                flags_to_remove.append(flag_name)

    # If we have flags to remove, treat this as "remove specific flags" not "remove entire command"
    if flags_to_remove:
        if cmdName not in commands:
            printIt(f'"{cmdName}" is not currently a Command.', lable.WARN)
            return

        # Process each flag that was specified for removal
        for flagName in flags_to_remove:
            cmd_data = commands[cmdName]
            is_option_switch = "option_switches" in cmd_data and flagName in cmd_data["option_switches"]
            is_option_string = "option_strings" in cmd_data and flagName in cmd_data["option_strings"]
            is_old_switch = "switchFlags" in cmd_data and flagName in cmd_data["switchFlags"]

            if is_option_switch or is_option_string or is_old_switch:
                if use_silent_mode:
                    chkRm = "y"  # Auto-confirm in silent mode
                else:
                    chkRm: str = input(f"Permanently delete swtc flag '--{flagName}' from {cmdName} (y/N): \\n")
                    if chkRm == "":
                        chkRm = "N"

                if chkRm[0].lower() == "y":
                    removeCmdSwtcFlag(cmdName, flagName)
                    printIt(
                        f'Swtc flag "--{flagName}" removed from command "{cmdName}"',
                        lable.RmArg,
                    )
                else:
                    printIt(
                        f'Swtc flag "--{flagName}" not removed from command "{cmdName}"',
                        lable.INFO,
                    )
            else:
                printIt(
                    f'Swtc flag "--{flagName}" is not defined for command "{cmdName}"',
                    lable.WARN,
                )
        return

    # If only one argument provided and no flags to remove, remove the entire command
    if len(theArgs) == 1:
        if cmdName in commands:
            if cmdName in ["newCmd", "modCmd", "rmCmd"]:
                printIt(f'Permission denied for "{cmdName}".', lable.WARN)
                return

            if use_silent_mode:
                chkRm = "y"  # Auto-confirm in silent mode
            else:
                chkRm: str = input(f"Permanently delete {cmdName} (y/N): \\n")
                if chkRm == "":
                    chkRm = "N"

            if chkRm[0].lower() == "y":
                removeCmd(cmdName)
                printIt(cmdName, lable.RmCmd)
            else:
                printIt(f'Command "{cmdName}" not removed.', lable.INFO)
        else:
            printIt(f'"{cmdName}" is not currently a Command.', lable.WARN)
    else:
        # Multiple arguments - remove specific items from the command
        if cmdName not in commands:
            printIt(f'"{cmdName}" is not currently a Command.', lable.WARN)
            return

        for argIndex in range(1, len(theArgs)):
            anArg = theArgs[argIndex]

            # CRITICAL BUG FIX: Check for flag prefixes FIRST to prevent accidental command deletion
            # Priority 1: Check if anArg is a flag with prefix (-, --, +, ++)
            if anArg.startswith(("-", "+")):
                # Handle swtc flag removal with prefix
                flagName = anArg.lstrip("-+")  # Remove -, --, +, ++ prefix
                cmd_data = commands[cmdName]
                is_option_switch = "option_switches" in cmd_data and flagName in cmd_data["option_switches"]
                is_option_string = "option_strings" in cmd_data and flagName in cmd_data["option_strings"]
                is_old_switch = "switchFlags" in cmd_data and flagName in cmd_data["switchFlags"]

                if is_option_switch or is_option_string or is_old_switch:
                    if use_silent_mode:
                        chkRm = "y"  # Auto-confirm in silent mode
                    else:
                        chkRm: str = input(f"Permanently delete swtc flag {anArg} from {cmdName} (y/N): \\n")
                        if chkRm == "":
                            chkRm = "N"

                    if chkRm[0].lower() == "y":
                        removeCmdSwtcFlag(cmdName, flagName)
                        printIt(
                            f'Swtc flag "{anArg}" removed from command "{cmdName}"',
                            lable.RmArg,
                        )
                    else:
                        printIt(
                            f'Swtc flag "{anArg}" not removed from command "{cmdName}"',
                            lable.INFO,
                        )
                else:
                    printIt(
                        f'Swtc flag "{anArg}" is not defined for command "{cmdName}"',
                        lable.WARN,
                    )
            else:
                # Priority 2: Check if anArg is a flag name without prefix (legacy support)
                cmd_data = commands[cmdName]
                is_option_switch = "option_switches" in cmd_data and anArg in cmd_data["option_switches"]
                is_option_string = "option_strings" in cmd_data and anArg in cmd_data["option_strings"]
                is_old_switch = "switchFlags" in cmd_data and anArg in cmd_data["switchFlags"]

                if is_option_switch or is_option_string or is_old_switch:
                    # Handle swtc flag removal by flag name (without prefix)
                    if use_silent_mode:
                        chkRm = "y"  # Auto-confirm in silent mode
                    else:
                        chkRm: str = input(f"Permanently delete swtc flag '-{anArg}' from {cmdName} (y/N):\\n")
                        if chkRm == "":
                            chkRm = "N"

                    if chkRm[0].lower() == "y":
                        removeCmdSwtcFlag(cmdName, anArg)
                        printIt(
                            f'Swtc flag "-{anArg}" removed from command "{cmdName}"',
                            lable.RmArg,
                        )
                    else:
                        printIt(
                            f'Swtc flag "-{anArg}" not removed from command "{cmdName}"',
                            lable.INFO,
                        )
                # Priority 3: Check if anArg is a regular argument
                elif "arguments" in commands[cmdName] and anArg in commands[cmdName]["arguments"]:
                    if use_silent_mode:
                        chkRm = "y"  # Auto-confirm in silent mode
                    else:
                        chkRm: str = input(f"Permanently delete argument {anArg} (y/N): \\n")
                        if chkRm == "":
                            chkRm = "N"

                    if chkRm[0].lower() == "y":
                        removeCmdArg(cmdName, anArg)
                        printIt(anArg, lable.RmArg)
                    else:
                        printIt(
                            f'Argument "{anArg}" not removed from command "{cmdName}".',
                            lable.INFO,
                        )
                else:
                    printIt(
                        f'"{anArg}" is not an argument or swtc flag for command "{cmdName}".',
                        lable.WARN,
                    )


def removeCmdArg(cmdName, argName):
    \"\"\"Remove an argument from a command using CommandManager\"\"\"
    # Use CommandManager to remove the argument
    if not command_manager.remove_argument(cmdName, argName):
        printIt(f"Argument '{argName}' not found in command '{cmdName}'", lable.WARN)
        return

    # Remove the function from the source file
    removeFunctionFromSourceFile(cmdName, argName)

    # Update source file's commandJsonDict
    cmd_data = command_manager.get_command_data(cmdName)
    updateSourceFileAfterRemoval(cmdName, cmd_data)


def removeCmdSwtcFlag(cmdName: str, flagName: str) -> None:
    \"\"\"Remove a switch flag from a command.\"\"\"
    command_manager.remove_flag_from_all_locations(cmdName, flagName)

    # Update source file's commandJsonDict
    cmd_data = command_manager.get_command_data(cmdName)
    updateSourceFileAfterRemoval(cmdName, cmd_data)


def updateSourceFileAfterRemoval(cmdName: str, cmdDict: dict) -> None:
    \"\"\"Update the commandJsonDict in the source file after removing an argument or swtc flag\"\"\"
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


def removeFunctionFromSourceFile(cmdName: str, argName: str) -> None:
    \"\"\"Remove a function definition from the source file\"\"\"
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f"{cmdName}.py")

    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return

    # Read the current file content
    with open(fileName, "r") as fr:
        fileContent = fr.read()

    lines = fileContent.split("\\n")

    # Find the function definition and its end
    function_start = -1
    function_end = -1
    indent_level = 0

    for i, line in enumerate(lines):
        # Look for the function definition
        if line.strip().startswith(f"def {argName}("):
            function_start = i
            # Find the indentation level of this function
            indent_level = len(line) - len(line.lstrip())
            continue

        # If we're inside a function, look for the end
        if function_start != -1 and i > function_start:
            # If we hit a non-empty line that's at the same or lesser indent level as the function,
            # or another function definition, we've found the end
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and not line.strip().startswith("#"):
                    function_end = i - 1  # Previous line was the end
                    break
            # If we reach the end of file
            elif i == len(lines) - 1:
                function_end = i
                break

    # If function was found, remove it
    if function_start != -1:
        if function_end == -1:
            function_end = len(lines) - 1  # Function goes to end of file

        # Remove the function lines (including any trailing empty lines that belong to it)
        # Also remove leading empty lines before the function if they exist
        start_remove = function_start
        end_remove = function_end

        # Look backwards for empty lines to remove before function
        while start_remove > 0 and not lines[start_remove - 1].strip():
            start_remove -= 1

        # Look forwards for empty lines to remove after function
        while end_remove < len(lines) - 1 and not lines[end_remove + 1].strip():
            end_remove += 1

        # Create new content without the function
        new_lines = lines[:start_remove] + lines[end_remove + 1 :]

        # Write the updated content back to the file
        with open(fileName, "w") as fw:
            fw.write("\\n".join(new_lines))

        printIt(f"Removed function '{argName}' from {fileName}", lable.INFO)
    else:
        printIt(f"Function '{argName}' not found in {fileName}", lable.WARN)


def removeCmd(cmdName):
    \"\"\"Remove a command completely.\"\"\"
    command_manager.remove_command(cmdName)

    # Remove the Python file
    pyFileName = f"{cmdName}.py"
    pyFileName = os.path.join(os.path.dirname(__file__), pyFileName)
    if os.path.isfile(pyFileName):
        os.remove(pyFileName)

    # Remove command flags from .${packName}rc and .cmdrc
    removeCmdSwitchOptions(cmdName)
"""))

