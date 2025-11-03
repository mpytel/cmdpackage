#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

newCmd_template = Template(dedent("""import os, sys, copy, hashlib, json
import importlib
import readline
from string import Template
from json import dumps
from ..defs.logIt import printIt, lable
from ..defs.validation import (
    validate_argument_name,
    check_command_uses_argcmddef_template,
)
from ..classes.argParse import ArgParse
from ..classes.optSwi${packName}hes import saveCmdSwi${packName}hFlags
from .commands import Commands

# from .templates.argCmdDef import cmdDefTemplate
# from .templates.argDefTemplate import argDefTemplate

commandJsonDict = {
    "commands_newCmd": {"description": "Command commands_newCmd", "swi${packName}hFlags": {}}
}

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


def newCmd(argParse: ArgParse):
    args = argParse.args

    # Handle --templates option to list available templates
    if hasattr(argParse, "cmd_options") and "templates" in argParse.cmd_options:
        # If templates option has a value, use it as template name
        if (
            argParse.cmd_options["templates"] != "__STRING_OPTION__"
            and argParse.cmd_options["templates"] is not True
        ):
            # --templates=templatename format, treat as --template
            pass  # Continue with command creation using the specified template
        else:
            # --templates without value, list templates and return
            list_templates()
            return

    cmdObj = Commands()
    argsDict = args.arguments

    if len(argsDict) == 0:
        printIt("Command name required", lable.ERROR)
        return

    newCmdName = args.arguments[0]
    if newCmdName not in cmdObj.commands.keys():
        # Determine and validate template FIRST before any other processing
        template_name = "argCmdDef"  # default
        if hasattr(argParse, "cmd_options"):
            # Check for --template option
            if "template" in argParse.cmd_options:
                template_name = argParse.cmd_options["template"]
            # Check for --templates=value option
            elif "templates" in argParse.cmd_options and argParse.cmd_options[
                "templates"
            ] not in ["__STRING_OPTION__", True]:
                template_name = argParse.cmd_options["templates"]

            # Validate template exists - EXIT with error if invalid
            if template_name != "argCmdDef" and not template_exists(template_name):
                printIt(f"ERROR: Template '{template_name}' not found.", lable.ERROR)
                list_templates()
                return

        # Combine regular arguments with option flags from cmd_options
        combined_args = list(args.arguments)

        for option_name, option_value in argParse.cmd_options.items():
            # Skip newCmd-specific options that aren't part of the command being created
            if option_name in ["template", "templates"]:
                continue

            if isinstance(option_value, bool):
                # Boolean flag (single hyphen) - add regardless of value for flag definition
                combined_args.append(f"-{option_name}")
            elif option_value == "__STRING_OPTION__" or not isinstance(
                option_value, bool
            ):
                # String option (double hyphen) - either has a value or is marked as string option
                combined_args.append(f"--{option_name}")

        theArgs = verifyArgsWithDiscriptions(cmdObj, combined_args, template_name)
        newCommandCMDJson = updateCMDJson(cmdObj, theArgs)

        writeCodeFile(theArgs, newCommandCMDJson, template_name)

        # Save newCmd-specific options to .${packName}rc for the newCmd command itself
        if hasattr(argParse, "cmd_options") and argParse.cmd_options:
            # Save newCmd-specific options like --template
            newcmd_flags = {}
            newcmd_swi${packName}h_flags = {}
            for option_name, option_value in argParse.cmd_options.items():
                if option_name in ["template", "templates"]:
                    # Save template option for newCmd command
                    if option_name == "template":
                        newcmd_flags["template"] = option_value
                        newcmd_swi${packName}h_flags["template"] = {"type": "str"}
                    elif option_name == "templates" and option_value not in [
                        "__STRING_OPTION__",
                        True,
                    ]:
                        # --templates=value format, treat as template
                        newcmd_flags["template"] = option_value
                        newcmd_swi${packName}h_flags["template"] = {"type": "str"}

            # Save newCmd-specific flags if any were found
            if newcmd_flags:
                saveCmdSwi${packName}hFlags("newCmd", newcmd_flags, newcmd_swi${packName}h_flags)

            # Extract boolean flags for the new command being created
            new_cmd_flags = {}
            for option_name, option_value in argParse.cmd_options.items():
                # Skip newCmd-specific options
                if option_name in ["template", "templates"]:
                    continue
                # Only save boolean flags (single hyphen options) with default value False
                if isinstance(option_value, bool):
                    new_cmd_flags[option_name] = (
                        False  # Default to False for new command flags
                    )

            # Save the flags if any were found
            if new_cmd_flags:
                # Create swi${packName}hFlags dict for the new command
                new_cmd_swi${packName}h_flags = {}
                for flag_name in new_cmd_flags.keys():
                    new_cmd_swi${packName}h_flags[flag_name] = {"type": "bool"}
                saveCmdSwi${packName}hFlags(newCmdName, new_cmd_flags, new_cmd_swi${packName}h_flags)

        printIt(f'"{newCmdName}" added using {template_name} template.', lable.NewCmd)
    else:
        printIt(
            f'"{newCmdName}" exists. use modCmd or rmCmd to modify or remove this command.',
            lable.INFO,
        )


def list_templates():
    \"\"\"List all available templates\"\"\"
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = []

    for file in os.listdir(template_dir):
        if file.endswith(".py") and file != "__init__.py":
            template_name = file[:-3]  # Remove .py extension
            # Exclude argDefTemplate as it's an internal helper template
            if template_name != "argDefTemplate":
                templates.append(template_name)

    printIt("Available templates:", lable.INFO)
    for template in sorted(templates):
        printIt(f"  - {template}", lable.INFO)


def template_exists(template_name):
    \"\"\"Check if a template exists and is available for user selection\"\"\"
    # argDefTemplate is internal only, not available for user selection
    if template_name == "argDefTemplate":
        return False

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_file = os.path.join(template_dir, f"{template_name}.py")
    return os.path.isfile(template_file)


def verifyArgsWithDiscriptions(
    cmdObj: Commands, theArgs, template_name: str = "simple"
) -> dict:
    rtnDict = {}
    optionFlags = {}
    argIndex = 0
    cmdName = theArgs[argIndex]

    while argIndex < len(theArgs):
        argName = theArgs[argIndex]

        if argName.startswith("--"):
            # Double hyphen option (stores value)
            if len(argName) <= 2:
                printIt("Missing option name after double hyphen.", lable.WARN)
                exit(0)
            optionName = argName[2:]  # Remove --
            theDict = input(
                f"Enter help description for option {argName} (stores value):\\n"
            )
            if theDict == "":
                theDict = f"Value option {argName}"
            optionFlags[optionName] = {"description": theDict, "type": "str"}
        elif argName.startswith("-"):
            # Single hyphen option (boolean flag)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            theDict = input(
                f"Enter help description for flag {argName} (true/false):\\n"
            )
            if theDict == "":
                theDict = f"Boolean flag {argName}"
            optionFlags[optionName] = {"description": theDict, "type": "bool"}
        else:
            # Regular argument
            # Validate argument name if using argCmdDef template (creates functions)
            if (
                template_name == "argCmdDef" and argIndex > 0
            ):  # Skip command name validation
                if not validate_argument_name(argName, cmdName):
                    printIt(
                        f"Skipping invalid argument '{argName}' - cannot be used as function name",
                        lable.WARN,
                    )
                    argIndex += 1
                    continue
            theDict = input(f"Enter help description for argument {argName}:\\n")
            if theDict == "":
                theDict = f"no help for {argName}"
            rtnDict[argName] = theDict

        argIndex += 1

    # Store option flags separately for later processing
    rtnDict["_optionFlags"] = optionFlags
    return rtnDict


def writeCodeFile(
    theArgs: dict, newCommandCMDJson: dict, template_name: str = "simple"
) -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f"{list(theArgs.keys())[0]}.py")
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs, newCommandCMDJson, template_name)
        with open(fileName, "w") as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr


def cmdCodeBlock(
    theArgs: dict, newCommandCMDJson: dict, template_name: str = "simple"
) -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]

    # Import the specified template
    try:
        print("importing template:", template_name)
        template_module = importlib.import_module(
            f"${packName}.commands.templates.{template_name}"
        )

        # Map template names to their template variable names
        template_var_names = {
            "argCmdDef": "cmdDefTemplate",
            "simple": "simpleTemplate",
            "asyncDef": "asyncDefTemplate",
            "classCall": "classCallTemplate",
        }

        # get template from template module
        template_var_name = template_var_names.get(
            template_name, f"{template_name}Template"
        )
        argCmdDefTemplate: Template = getattr(template_module, template_var_name)

        # get argument def template for argCmdDef to use when nessesary
        argDef = importlib.import_module("${packName}.commands.templates.argDefTemplate")
        argDefTemplate: Template = argDef.argDefTemplate

    except (ImportError, AttributeError) as e:
        printIt(
            f"Could not import template '{template_name}': {e}, using default",
            lable.WARN,
        )
        from .templates.argCmdDef import cmdDefTemplate as argCmdDefTemplate
        from .templates.argDefTemplate import argDefTemplate

    cmdCodeBlockJsonDict = {}
    cmdCodeBlockJsonDict[cmdName] = newCommandCMDJson
    commandJsonDictStr = "commandJsonDict = " + dumps(cmdCodeBlockJsonDict, indent=2)

    # Add regular arguments to the code block (skip _optionFlags)
    for argName in argNames:
        if argName != "_optionFlags":
            cmdCodeBlockJsonDict[argName] = theArgs[argName]

    rtnStr = argCmdDefTemplate.substitute(
        packName=packName, defName=cmdName, commandJsonDict=commandJsonDictStr
    )

    argIndex = 1
    while argIndex < len(argNames):  # add subarg functions
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry when generating argument functions
        if argName != "_optionFlags":
            # Only add argument functions if template has argDefTemplate
            if argDefTemplate is not None:
                rtnStr += argDefTemplate.substitute(
                    argName=argName, defName=cmdName, packName=packName
                )
        argIndex += 1
    return rtnStr


def updateCMDJson(cmdObj: Commands, theArgs: dict) -> dict:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defDiscription = theArgs[argNames[0]]
    newCommandCMDJson = {}
    newCommandCMDJson["description"] = defDiscription

    # Handle option flags if they exist
    optionFlags = theArgs.get("_optionFlags", {})
    newCommandCMDJson["swi${packName}hFlags"] = optionFlags

    argIndex = 1
    while argIndex < len(theArgs):  # add subarg functions
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry
        if argName != "_optionFlags":
            newCommandCMDJson[argName] = theArgs[argName]
        argIndex += 1
    commands[argNames[0]] = newCommandCMDJson
    cmdObj.commands = commands

    # Update MD5 hash in genTempSyncData.json if it exists
    commands_json_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "commands.json"
    )
    update_sync_data_md5(commands_json_file)

    return newCommandCMDJson
"""))

