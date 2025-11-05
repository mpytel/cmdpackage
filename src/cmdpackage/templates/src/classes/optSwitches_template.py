#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

optSwitches_template = Template(dedent("""import json
from pathlib import Path
from ..defs.logIt import printIt, lable

rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath(f".${packName}rc")


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


def saveCmdswitchFlags(cmdName: str, cmdOptions: dict, cmdswitchFlags: dict):
    \"\"\"Save command-specific swtc flags to .${packName}rc\"\"\"
    rcData = readoptSwitches()

    # Initialize command flags section if it doesn't exist
    if "commandFlags" not in rcData:
        rcData["commandFlags"] = {}
    if cmdName not in rcData["commandFlags"]:
        rcData["commandFlags"][cmdName] = {}

    # Process each command option
    for optionName, optionValue in cmdOptions.items():
        if optionName in cmdswitchFlags:
            flagDef = cmdswitchFlags[optionName]
            if flagDef["type"] == "bool":
                # Boolean flag - store true/false
                rcData["commandFlags"][cmdName][optionName] = bool(optionValue)
            elif flagDef["type"] == "str":
                # String option - store the value (or empty string if not provided)
                if optionValue == "__STRING_OPTION__":
                    rcData["commandFlags"][cmdName][optionName] = ""
                else:
                    rcData["commandFlags"][cmdName][optionName] = str(optionValue)

    # Write back to file
    with open(rcFileName, "w") as wf:
        json.dump(rcData, wf, indent=2)

    printIt(f"Command flags saved for '{cmdName}'", lable.INFO)


def toggleCmdSwtcFlag(cmdName: str, flagName: str, setValue: bool):
    \"\"\"Toggle a command-specific boolean flag in .${packName}rc\"\"\"
    rcData = readoptSwitches()

    # Initialize command flags section if it doesn't exist
    if "commandFlags" not in rcData:
        rcData["commandFlags"] = {}
    if cmdName not in rcData["commandFlags"]:
        rcData["commandFlags"][cmdName] = {}

    # Set the flag value
    rcData["commandFlags"][cmdName][flagName] = setValue

    # Write back to file
    with open(rcFileName, "w") as wf:
        json.dump(rcData, wf, indent=2)

    status = "enabled" if setValue else "disabled"
    printIt(f"Command flag '{flagName}' {status} for '{cmdName}'", lable.INFO)


def getCmdswitchFlags(cmdName: str) -> dict:
    \"\"\"Get stored command-specific swtc flags from .${packName}rc\"\"\"
    rcData = readoptSwitches()
    return rcData.get("commandFlags", {}).get(cmdName, {})


def removeCmdswitchFlags(cmdName: str):
    \"\"\"Remove command-specific swtc flags from .${packName}rc when command is deleted\"\"\"
    rcData = readoptSwitches()

    # Check if command exists in commandFlags
    if "commandFlags" in rcData and cmdName in rcData["commandFlags"]:
        del rcData["commandFlags"][cmdName]

        # If commandFlags is now empty, we can remove the whole section
        if not rcData["commandFlags"]:
            del rcData["commandFlags"]

        # If the entire file would be empty or only has empty sections, delete the file
        if not rcData.get("switchFlags") and not rcData.get("commandFlags"):
            if rcFileName.is_file():
                rcFileName.unlink()
                # printIt(f"Removed '{cmdName}' flags and deleted empty .${packName}rc file", lable.INFO)
        else:
            # Write back the updated file
            with open(rcFileName, "w") as wf:
                json.dump(rcData, wf, indent=2)
            # printIt(f"Removed '{cmdName}' flags from .${packName}rc", lable.INFO)
    else:
        # printIt(f"No flags found for '{cmdName}' in .${packName}rc", lable.INFO)
        pass


def readoptSwitches() -> dict:
    global rcFileName
    optSwitches = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRcJson = json.load(rf)
        optSwitches["switchFlags"] = rawRcJson.get("switchFlags", {})
        optSwitches["commandFlags"] = rawRcJson.get("commandFlags", {})
    else:
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
"""))

