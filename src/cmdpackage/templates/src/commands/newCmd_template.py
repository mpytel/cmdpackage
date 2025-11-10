#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

newCmd_template = Template(dedent("""import os, sys, copy, json
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
from ..classes.optSwitches import saveCmdSwitchOptions
from ..classes.CommandManager import command_manager
from .commands import Commands

# from .templates.argCmdDef import cmdDefTemplate
# from .templates.argDefTemplate import argDefTemplate

commandJsonDict = {
    "newCmd": {
        "description": "Add new command <cmdName> with [argNames...]. Also creates a file cmdName.py.",
        "option_switches": {"d": "Silently use default description"},
        "option_strings": {},
        "arguments": {
            "cmdName": "Name of new command",
            "argName": "(argName...) Optional names of argument to associate with the new command.",
        },
    }
}
readline.parse_and_bind("tab: compleat")
readline.parse_and_bind("set editing-mode vi")


cmdObj = Commands()


def newCmd(argParse: ArgParse):
    args = argParse.args

    # Handle --templates option to list available templates
    if hasattr(argParse, "cmd_options") and "templates" in argParse.cmd_options:
        # If templates option has a value, use it as template name
        if argParse.cmd_options["templates"] != "__STRING_OPTION__" and argParse.cmd_options["templates"] is not True:
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
            elif "templates" in argParse.cmd_options and argParse.cmd_options["templates"] not in [
                "__STRING_OPTION__",
                True,
            ]:
                template_name = argParse.cmd_options["templates"]

            # Validate template exists - EXIT with error if invalid
            if template_name != "argCmdDef" and not template_exists(template_name):
                printIt(f"ERROR: Template '{template_name}' not found.", lable.ERROR)
                list_templates()
                return

        # Check if +d option is being used for default descriptions
        # In ${packName} system: -d means silence OFF (d=False), +d means silence ON (d=True)
        # This is an unconventional persistence storage model where minus=off, plus=on
        use_defaults = hasattr(argParse, "cmd_options") and argParse.cmd_options.get("d", False)

        # Combine regular arguments with option values from cmd_options
        combined_args = list(args.arguments)

        for option_name, option_value in argParse.cmd_options.items():
            # Skip newCmd-specific options that aren't part of the command being created
            if option_name in ["template", "templates", "d"]:
                continue

            if isinstance(option_value, bool):
                # Boolean option (single hyphen) - add regardless of value for option definition
                combined_args.append(f"-{option_name}")
            elif option_value == "__STRING_OPTION__" or not isinstance(option_value, bool):
                # String option (double hyphen) - either has a value or is marked as string option
                combined_args.append(f"--{option_name}")

        theArgs = verifyArgsWithDiscriptions(cmdObj, combined_args, template_name, use_defaults)
        newCommandCMDJson = command_manager.update_command_json(cmdObj, theArgs, mode="create")

        writeCodeFile(theArgs, newCommandCMDJson, template_name)

        # Save newCmd-specific options to .${packName}rc for the newCmd command itself
        if hasattr(argParse, "cmd_options") and argParse.cmd_options:
            # Save newCmd-specific options like --template
            newcmd_options = {}
            newcmd_swtc_options = {}
            for option_name, option_value in argParse.cmd_options.items():
                if option_name in ["template", "templates"]:
                    # Save template option for newCmd command
                    if option_name == "template":
                        newcmd_options["template"] = option_value
                        newcmd_swtc_options["template"] = {"type": "str"}
                    elif option_name == "templates" and option_value not in [
                        "__STRING_OPTION__",
                        True,
                    ]:
                        # --templates=value format, treat as template
                        newcmd_options["template"] = option_value
                        newcmd_swtc_options["template"] = {"type": "str"}

            # Save newCmd-specific options if any were found
            if newcmd_options:
                saveCmdSwitchOptions("newCmd", newcmd_options, newcmd_swtc_options)

            # Extract boolean options for the new command being created
            new_cmd_options = {}
            for option_name, option_value in argParse.cmd_options.items():
                # Skip newCmd-specific options
                if option_name in ["template", "templates"]:
                    continue
                # Only save boolean options (single hyphen options) with default value False
                if isinstance(option_value, bool):
                    new_cmd_options[option_name] = False  # Default to False for new command options

            # Save the options if any were found
            if new_cmd_options:
                # Create switchFlags dict for the new command
                new_cmd_swtc_options = {}
                for option_name in new_cmd_options.keys():
                    new_cmd_swtc_options[option_name] = {"type": "bool"}
                saveCmdSwitchOptions(newCmdName, new_cmd_options, new_cmd_swtc_options)

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
    cmdObj: Commands, theArgs, template_name: str = "simple", use_defaults: bool = False
) -> dict:
    rtnDict = {}
    optionFlags = {}
    argIndex = 0
    cmdName = theArgs[argIndex]

    def get_default_description(name, arg_type="argument"):
        \"\"\"Generate clever, relevant default descriptions for ${packName} system arguments\"\"\"
        pi_descriptions = {
            "${packName}": "Creates a new ${packName} (pertinent information) structure for topic management",
            "piType": "Specifies the type of pertinent information (e.g., topic, domain, concept)",
            "piTitle": "The title/name of the ${packName} object for identification and indexing",
            "piSD": "Short description providing context for the ${packName}'s purpose and content",
            "piBase": "Base ${packName} structure containing core pertinent information elements",
            "piBody": "Extended content body that can assume any piTypeBody structure",
            "piIndexer": "Indexing metadata for ${packName} discovery and organization",
            "piInfluence": "Precedent and descendent relationships for ${packName} networks",
        }

        # Return specific ${packName} description if available, otherwise generate generic one
        if name in pi_descriptions:
            return pi_descriptions[name]
        elif name.startswith("${packName}"):
            return f"Pi-related {arg_type} for {name[2:].lower()} management in the pertinent information system"
        else:
            return f"Argument for {name} functionality"

    while argIndex < len(theArgs):
        argName = theArgs[argIndex]

        if argName.startswith("--"):
            # Double hyphen option (stores value)
            if len(argName) <= 2:
                printIt("Missing option name after double hyphen.", lable.WARN)
                exit(0)
            optionName = argName[2:]  # Remove --
            if use_defaults:
                theDict = get_default_description(optionName, "option")
            else:
                theDict = input(f"Enter help description for option {argName} (stores value): \\n")
                if theDict == "":
                    theDict = f"Value option {argName}"
            optionFlags[optionName] = {"description": theDict, "type": "str"}
        elif argName.startswith("-"):
            # Single hyphen option (boolean flag)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            if use_defaults:
                theDict = get_default_description(optionName, "flag")
            else:
                theDict = input(f"Enter help description for flag {argName} (true/false): \\n")
                if theDict == "":
                    theDict = f"Boolean flag {argName}"
            optionFlags[optionName] = {"description": theDict, "type": "bool"}
        else:
            # Regular argument
            # Validate argument name if using argCmdDef template (creates functions)
            if template_name == "argCmdDef" and argIndex > 0:  # Skip command name validation
                if not validate_argument_name(argName, cmdName):
                    printIt(
                        f"Skipping invalid argument '{argName}' - cannot be used as function name",
                        lable.WARN,
                    )
                    argIndex += 1
                    continue
            if use_defaults:
                theDict = get_default_description(argName)
            else:
                theDict = input(f"Enter help description for argument {argName}: \\n")
                if theDict == "":
                    theDict = f"Run ${packName} modCmd {argName}"
            rtnDict[argName] = theDict

        argIndex += 1

    # Store option details separately for later processing
    rtnDict["_option_details"] = optionFlags
    return rtnDict


def writeCodeFile(theArgs: dict, newCommandCMDJson: dict, template_name: str = "simple") -> str:
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


def cmdCodeBlock(theArgs: dict, newCommandCMDJson: dict, template_name: str = "simple") -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]

    # Import the specified template
    try:
        print("importing template:", template_name)
        template_module = importlib.import_module(f"${packName}.commands.templates.{template_name}")

        # Map template names to their template variable names
        template_var_names = {
            "argCmdDef": "cmdDefTemplate",
            "simple": "simpleTemplate",
            "asyncDef": "asyncDefTemplate",
            "classCall": "classCallTemplate",
        }

        # get template from template module
        template_var_name = template_var_names.get(template_name, f"{template_name}Template")
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

    # Add regular arguments to the code block (skip _option_details)
    for argName in theArgs.keys():
        if argName != "_option_details":
            cmdCodeBlockJsonDict[argName] = theArgs[argName]

    rtnStr = argCmdDefTemplate.substitute(packName=packName, defName=cmdName, commandJsonDict=commandJsonDictStr)

    argIndex = 1
    while argIndex < len(argNames):  # add subarg functions
        argName = argNames[argIndex]
        # Skip the special _option_details entry when generating argument functions
        if argName != "_option_details":
            # Only add argument functions if template has argDefTemplate
            if argDefTemplate is not None:
                rtnStr += argDefTemplate.substitute(argName=argName, defName=cmdName, packName=packName)
        argIndex += 1
    return rtnStr
"""))

