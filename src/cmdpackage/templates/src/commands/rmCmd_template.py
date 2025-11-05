#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

rmCmd_template = Template(dedent("""import os, json, hashlib
from ..defs.logIt import printIt, lable, cStr, color
from ..classes.optSwitches import removeCmdswitchFlags
from .commands import Commands

commandJsonDict = {"commands_rmCmd": {"description": "Command commands_rmCmd", "switchFlags": {}}}

cmdObj = Commands()
commands = cmdObj.commands
theDir = os.path.dirname(os.path.realpath(__file__))
jsonFileName = os.path.join(theDir, "commands.json")


def update_sync_data_md5(file_path):
    \"\"\"Update the MD5 hash for a file in genTempSyncData.json\"\"\"
    try:
        # Get the project root (go up from commands dir to ${packName} dir, then to project root)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(theDir)))
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


def rmCmd(argParse):
    # Reload commands to get current state
    cmdObj = Commands()
    commands = cmdObj.commands

    args = argParse.args
    theArgs = args.arguments

    if len(theArgs) == 0:
        printIt("Command name required", lable.ERROR)
        return

    cmdName = theArgs[0]

    # If only one argument provided, remove the entire command
    if len(theArgs) == 1:
        if cmdName in commands:
            if cmdName in ["newCmd", "modCmd", "rmCmd"]:
                printIt(f'Permission denied for "{cmdName}".', lable.WARN)
                return
            chkRm: str = input(f"Permanently delete {cmdName} (y/N):\\n")
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

            # Check if anArg is a swtc flag name (check if it exists in switchFlags)
            if "switchFlags" in commands[cmdName] and anArg in commands[cmdName]["switchFlags"]:
                # Handle swtc flag removal by flag name (without -)
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
            # Check if anArg is a swtc flag (starts with -) - legacy support
            elif anArg.startswith("-"):
                # Handle swtc flag removal with dash prefix
                flagName = anArg.lstrip("-")  # Remove - or -- prefix
                if "switchFlags" in commands[cmdName] and flagName in commands[cmdName]["switchFlags"]:
                    chkRm: str = input(f"Permanently delete swtc flag {anArg} from {cmdName} (y/N):\\n")
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
            elif anArg in commands[cmdName]:
                chkRm: str = input(f"Permanently delete argument {anArg} (y/N):\\n")
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
    global jsonFileName
    with open(jsonFileName, "r") as rf:
        theJson = json.load(rf)
        del theJson[cmdName][argName]
    with open(jsonFileName, "w") as wf:
        json.dump(theJson, wf, indent=2)

    # Update MD5 hash in genTempSyncData.json if it exists
    update_sync_data_md5(jsonFileName)

    # Remove the function from the source file
    removeFunctionFromSourceFile(cmdName, argName)

    # Update source file's commandJsonDict
    updateSourceFileAfterRemoval(cmdName, theJson[cmdName])


def removeCmdSwtcFlag(cmdName, flagName):
    \"\"\"Remove a swtc flag from commands.json, .${packName}rc, and source file\"\"\"
    global jsonFileName
    with open(jsonFileName, "r") as rf:
        theJson = json.load(rf)
        if "switchFlags" in theJson[cmdName] and flagName in theJson[cmdName]["switchFlags"]:
            del theJson[cmdName]["switchFlags"][flagName]
            # If switchFlags becomes empty, we can leave it empty
            if not theJson[cmdName]["switchFlags"]:
                theJson[cmdName]["switchFlags"] = {}
    with open(jsonFileName, "w") as wf:
        json.dump(theJson, wf, indent=2)

    # Update MD5 hash in genTempSyncData.json if it exists
    update_sync_data_md5(jsonFileName)

    # Remove flag from .${packName}rc file
    ${packName}rc_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(jsonFileName))), ".${packName}rc")

    if os.path.exists(${packName}rc_file):
        try:
            with open(${packName}rc_file, "r") as pf:
                ${packName}rc_data = json.load(pf)

            # Remove the flag from commandFlags if it exists
            if (
                "commandFlags" in ${packName}rc_data
                and cmdName in ${packName}rc_data["commandFlags"]
                and flagName in ${packName}rc_data["commandFlags"][cmdName]
            ):

                del ${packName}rc_data["commandFlags"][cmdName][flagName]

                # If command has no more flags, remove the command entry
                if not ${packName}rc_data["commandFlags"][cmdName]:
                    del ${packName}rc_data["commandFlags"][cmdName]

                with open(${packName}rc_file, "w") as pf:
                    json.dump(${packName}rc_data, pf, indent=2)

                printIt(f"Removed flag '{flagName}' from .${packName}rc", lable.INFO)

        except (json.JSONDecodeError, KeyError) as e:
            printIt(f"Warning: Could not update .${packName}rc file: {e}", lable.WARN)

    # Update source file's commandJsonDict
    updateSourceFileAfterRemoval(cmdName, theJson[cmdName])


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
    global jsonFileName
    with open(jsonFileName, "r") as rf:
        theJson = json.load(rf)
        del theJson[cmdName]
    with open(jsonFileName, "w") as wf:
        json.dump(theJson, wf, indent=2)

    # Update MD5 hash in genTempSyncData.json if it exists
    update_sync_data_md5(jsonFileName)

    pyFileName = f"{cmdName}.py"
    pyFileName = os.path.join(theDir, pyFileName)
    if os.path.isfile(pyFileName):
        os.remove(pyFileName)

    # Remove command flags from .${packName}rc
    removeCmdswitchFlags(cmdName)
"""))

