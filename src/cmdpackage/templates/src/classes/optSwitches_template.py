#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

optSwitches_template = Template(dedent("""import json
from pathlib import Path
from ..defs.logIt import printIt, lable

rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath(f".${packName}rc")


class OptSwtces:
    def __init__(self, swtcFlags: dict) -> None:
        self.swtcFlags = swtcFlags
        self.optSwtces = readOptSwtces()

    def toggleSwtcFlag(self, swtcFlag: str):
        optSwtces = {}
        optSwtces["swtcFlags"] = {}
        currSwtcFlag = swtcFlag[1:]
        if swtcFlag[0] in "+":
            currSwtcValue = (
                True  # not (self.optSwtces["swtcFlags"][currSwtcFlag] == True)
            )
        else:
            currSwtcValue = False
        try:
            self.optSwtces["swtcFlags"][currSwtcFlag] = currSwtcValue
        except:
            print("here")
            self.optSwtces["swtcFlags"][currSwtcFlag] = True
        writeOptJson(self.optSwtces, self.swtcFlags)


def saveCmdSwtcFlags(cmdName: str, cmdOptions: dict, cmdSwtcFlags: dict):
    \"\"\"Save command-specific swtc flags to .${packName}rc\"\"\"
    rcData = readOptSwtces()

    # Initialize command flags section if it doesn't exist
    if "commandFlags" not in rcData:
        rcData["commandFlags"] = {}
    if cmdName not in rcData["commandFlags"]:
        rcData["commandFlags"][cmdName] = {}

    # Process each command option
    for optionName, optionValue in cmdOptions.items():
        if optionName in cmdSwtcFlags:
            flagDef = cmdSwtcFlags[optionName]
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
    rcData = readOptSwtces()

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


def getCmdSwtcFlags(cmdName: str) -> dict:
    \"\"\"Get stored command-specific swtc flags from .${packName}rc\"\"\"
    rcData = readOptSwtces()
    return rcData.get("commandFlags", {}).get(cmdName, {})


def removeCmdSwtcFlags(cmdName: str):
    \"\"\"Remove command-specific swtc flags from .${packName}rc when command is deleted\"\"\"
    rcData = readOptSwtces()

    # Check if command exists in commandFlags
    if "commandFlags" in rcData and cmdName in rcData["commandFlags"]:
        del rcData["commandFlags"][cmdName]

        # If commandFlags is now empty, we can remove the whole section
        if not rcData["commandFlags"]:
            del rcData["commandFlags"]

        # If the entire file would be empty or only has empty sections, delete the file
        if not rcData.get("swtcFlags") and not rcData.get("commandFlags"):
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


def readOptSwtces() -> dict:
    global rcFileName
    optSwtces = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRcJson = json.load(rf)
        optSwtces["swtcFlags"] = rawRcJson.get("swtcFlags", {})
        optSwtces["commandFlags"] = rawRcJson.get("commandFlags", {})
    else:
        optSwtces["swtcFlags"] = {}
        optSwtces["commandFlags"] = {}
    return optSwtces


def writeOptJson(optSwtces: dict, swtcFlags: dict) -> dict:
    global rcFileName
    rawRC = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwtces
    for swtcFlag in swtcFlags.keys():  # fill in missing items'
        try:
            _ = rawRC["swtcFlags"][swtcFlag]
        except:
            rawRC["swtcFlags"][swtcFlag] = False
    # printIt(formatOptStr(rawRC["swtcFlags"]), lable.INFO)
    with open(rcFileName, "w") as wf:
        json.dump(rawRC, wf, indent=2)
    return rawRC


def formatOptStr(optSwtces: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwtces:
        rtnStr += f"-{cmdOpt}={optSwtces[cmdOpt]}, "
    rtnStr = rtnStr[:-2]
    return rtnStr
"""))

