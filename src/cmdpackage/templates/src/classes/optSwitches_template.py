#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

optSwitches_template = Template(dedent("""import json
from pathlib import Path
from ..defs.logIt import printIt, lable

# Store command options in src/${packName}/commands/.cmdrc
rcFileDir = Path(__file__).resolve().parents[1] / "commands"  # Go to src/${packName}/commands
rcFileName = rcFileDir.joinpath(".cmdrc")


class optSwitches:
    def __init__(self, switchFlags: dict) -> None:
        self.switchFlags = switchFlags
        self.optSwitches = readoptSwitches()

    def toggleSwtcFlag(self, swtcFlag: str):
        optSwitches = {}
        optSwitches["switchFlags"] = {}
        currSwtcFlag = swtcFlag[1:]
        if swtcFlag[0] in "+":
            currSwtcValue = True  # not (self.optSwitches["switchFlags"][currSwtcFlag] == True)
        else:
            currSwtcValue = False
        try:
            self.optSwitches["switchFlags"][currSwtcFlag] = currSwtcValue
        except:
            print("here")
            self.optSwitches["switchFlags"][currSwtcFlag] = True
        writeOptJson(self.optSwitches, self.switchFlags)


def saveCmdSwitchOptions(cmdName: str, cmdOptions: dict, cmd_switch_options: dict):
    \"\"\"Save command-specific switch options to .cmdrc\"\"\"
    save_command_options(cmdName, cmdOptions, cmd_switch_options)


def toggleCmdSwitchOption(cmdName: str, optionName: str, setValue: bool):
    \"\"\"Toggle a command-specific boolean option in .cmdrc\"\"\"
    toggle_command_option(cmdName, optionName, setValue)


def getCmdSwitchOptions(cmdName: str) -> dict:
    \"\"\"Get stored command-specific switch options from .cmdrc\"\"\"
    return get_command_options(cmdName)


def removeCmdSwitchOptions(cmdName: str):
    \"\"\"Remove command-specific switch options from .cmdrc when command is deleted\"\"\"
    remove_command_options(cmdName)


def readoptSwitches() -> dict:
    global rcFileName
    optSwitches = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRcJson = json.load(rf)
        # Handle new .cmdrc structure (option_switches, option_strings, commands)
        # Map to old structure for backward compatibility
        optSwitches["switchFlags"] = rawRcJson.get("option_switches", {})
        optSwitches["commandFlags"] = rawRcJson.get("commands", {})
    else:
        # Initialize new structure
        optSwitches["switchFlags"] = {}
        optSwitches["commandFlags"] = {}
    return optSwitches


def writeOptJson(optSwitches: dict, switchFlags: dict) -> dict:
    global rcFileName
    rawRC = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwitches
    for swtcFlag in switchFlags.keys():  # fill in missing items'
        try:
            _ = rawRC["switchFlags"][swtcFlag]
        except:
            rawRC["switchFlags"][swtcFlag] = False
    # printIt(formatOptStr(rawRC["switchFlags"]), lable.INFO)
    with open(rcFileName, "w") as wf:
        json.dump(rawRC, wf, indent=2)
    return rawRC


def formatOptStr(optSwitches: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwitches:
        rtnStr += f"-{cmdOpt}={optSwitches[cmdOpt]}, "
    rtnStr = rtnStr[:-2]
    return rtnStr


# =============================================================================
# Command Storage Management
# =============================================================================


def get_cmdrc_path() -> Path:
    \"\"\"Get the path to the .cmdrc file for command storage\"\"\"
    # Get the path relative to this file: src/${packName}/defs/utilities.py
    # Go up to src/${packName}/commands/.cmdrc
    current_file = Path(__file__).resolve()
    commands_dir = current_file.parent.parent / "commands"
    return commands_dir / ".cmdrc"


def read_cmdrc() -> dict:
    \"\"\"Read the command storage file (.cmdrc) and return the data\"\"\"
    cmdrc_path = get_cmdrc_path()

    if not cmdrc_path.exists():
        # Create default structure if file doesn't exist
        return {"option_switches": {}, "option_strings": {}, "commands": {}}

    try:
        with open(cmdrc_path, "r") as f:
            data = json.load(f)
            # Ensure all required sections exist
            if "option_switches" not in data:
                data["option_switches"] = {}
            if "option_strings" not in data:
                data["option_strings"] = {}
            if "commands" not in data:
                data["commands"] = {}
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        printIt(f"Error reading .cmdrc: {e}", lable.WARN)
        return {"option_switches": {}, "option_strings": {}, "commands": {}}


def write_cmdrc(data: dict) -> bool:
    \"\"\"Write data to the command storage file (.cmdrc)\"\"\"
    cmdrc_path = get_cmdrc_path()

    try:
        # Ensure directory exists
        cmdrc_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with pretty formatting
        with open(cmdrc_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        printIt(f"Error writing .cmdrc: {e}", lable.ERROR)
        return False


def save_command_options(cmd_name: str, cmd_options: dict, cmd_option_definitions: dict) -> None:
    \"\"\"
    Save command-specific options to .cmdrc

    Args:
        cmd_name: The name of the command
        cmd_options: Dict of option names to values
        cmd_option_definitions: Dict of option definitions with type info
    \"\"\"
    data = read_cmdrc()

    # Initialize command section if it doesn't exist
    if cmd_name not in data["commands"]:
        data["commands"][cmd_name] = {"option_switches": {}, "option_strings": {}}

    # Process each option based on its type
    for option_name, option_value in cmd_options.items():
        if option_name in cmd_option_definitions:
            option_def = cmd_option_definitions[option_name]
            option_type = option_def.get("type", "str")

            if option_type == "bool":
                # Boolean option - save to option_switches
                data["commands"][cmd_name]["option_switches"][option_name] = bool(option_value)
            elif option_type == "str":
                # String option - save to option_strings
                if option_value == "__STRING_OPTION__":
                    data["commands"][cmd_name]["option_strings"][option_name] = ""
                else:
                    data["commands"][cmd_name]["option_strings"][option_name] = str(option_value)

    # Write back to file
    if write_cmdrc(data):
        printIt(f"Command options saved for '{cmd_name}'", lable.INFO)
    else:
        printIt(f"Failed to save command options for '{cmd_name}'", lable.ERROR)


def toggle_command_option(cmd_name: str, option_name: str, set_value: bool) -> None:
    \"\"\"Toggle a command-specific boolean option in .cmdrc\"\"\"
    data = read_cmdrc()

    # Initialize command section if it doesn't exist
    if cmd_name not in data["commands"]:
        data["commands"][cmd_name] = {"option_switches": {}, "option_strings": {}}

    # Set the option value
    data["commands"][cmd_name]["option_switches"][option_name] = set_value

    # Write back to file
    if write_cmdrc(data):
        status = "enabled" if set_value else "disabled"
        printIt(f"Command option '{option_name}' {status} for '{cmd_name}'", lable.INFO)
    else:
        printIt(f"Failed to toggle command option '{option_name}' for '{cmd_name}'", lable.ERROR)


def get_command_options(cmd_name: str) -> dict:
    \"\"\"Get stored command-specific options from .cmdrc\"\"\"
    data = read_cmdrc()
    return data.get("commands", {}).get(cmd_name, {})


def remove_command_options(cmd_name: str) -> None:
    \"\"\"Remove all stored options for a specific command from .cmdrc\"\"\"
    data = read_cmdrc()

    if "commands" in data and cmd_name in data["commands"]:
        del data["commands"][cmd_name]

        if write_cmdrc(data):
            printIt(f"Command options removed for '{cmd_name}'", lable.INFO)
        else:
            printIt(f"Failed to remove command options for '{cmd_name}'", lable.ERROR)
"""))

