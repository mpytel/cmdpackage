#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

optSwitches_template = Template(dedent("""import json
from pathlib import Path
from ..defs.logIt import printIt, lable

rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath(f".${packName}rc")


class OptSwi${packName}hes:
    def __init__(self, swi${packName}hFlags: dict) -> None:
        self.swi${packName}hFlags = swi${packName}hFlags
        self.optSwi${packName}hes = readOptSwi${packName}hes()

    def toggleSwi${packName}hFlag(self, swi${packName}hFlag: str):
        optSwi${packName}hes = {}
        optSwi${packName}hes["swi${packName}hFlags"] = {}
        currSwi${packName}hFlag = swi${packName}hFlag[1:]
        if swi${packName}hFlag[0] in "+":
            currSwi${packName}hValue = (
                True  # not (self.optSwi${packName}hes["swi${packName}hFlags"][currSwi${packName}hFlag] == True)
            )
        else:
            currSwi${packName}hValue = False
        try:
            self.optSwi${packName}hes["swi${packName}hFlags"][currSwi${packName}hFlag] = currSwi${packName}hValue
        except:
            print("here")
            self.optSwi${packName}hes["swi${packName}hFlags"][currSwi${packName}hFlag] = True
        writeOptJson(self.optSwi${packName}hes, self.swi${packName}hFlags)


def saveCmdSwi${packName}hFlags(cmdName: str, cmdOptions: dict, cmdSwi${packName}hFlags: dict):
    \"\"\"Save command-specific swi${packName}h flags to .${packName}rc\"\"\"
    rcData = readOptSwi${packName}hes()

    # Initialize command flags section if it doesn't exist
    if "commandFlags" not in rcData:
        rcData["commandFlags"] = {}
    if cmdName not in rcData["commandFlags"]:
        rcData["commandFlags"][cmdName] = {}

    # Process each command option
    for optionName, optionValue in cmdOptions.items():
        if optionName in cmdSwi${packName}hFlags:
            flagDef = cmdSwi${packName}hFlags[optionName]
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


def toggleCmdSwi${packName}hFlag(cmdName: str, flagName: str, setValue: bool):
    \"\"\"Toggle a command-specific boolean flag in .${packName}rc\"\"\"
    rcData = readOptSwi${packName}hes()

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


def getCmdSwi${packName}hFlags(cmdName: str) -> dict:
    \"\"\"Get stored command-specific swi${packName}h flags from .${packName}rc\"\"\"
    rcData = readOptSwi${packName}hes()
    return rcData.get("commandFlags", {}).get(cmdName, {})


def removeCmdSwi${packName}hFlags(cmdName: str):
    \"\"\"Remove command-specific swi${packName}h flags from .${packName}rc when command is deleted\"\"\"
    rcData = readOptSwi${packName}hes()

    # Check if command exists in commandFlags
    if "commandFlags" in rcData and cmdName in rcData["commandFlags"]:
        del rcData["commandFlags"][cmdName]

        # If commandFlags is now empty, we can remove the whole section
        if not rcData["commandFlags"]:
            del rcData["commandFlags"]

        # If the entire file would be empty or only has empty sections, delete the file
        if not rcData.get("swi${packName}hFlags") and not rcData.get("commandFlags"):
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


def readOptSwi${packName}hes() -> dict:
    global rcFileName
    optSwi${packName}hes = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRcJson = json.load(rf)
        optSwi${packName}hes["swi${packName}hFlags"] = rawRcJson.get("swi${packName}hFlags", {})
        optSwi${packName}hes["commandFlags"] = rawRcJson.get("commandFlags", {})
    else:
        optSwi${packName}hes["swi${packName}hFlags"] = {}
        optSwi${packName}hes["commandFlags"] = {}
    return optSwi${packName}hes


def writeOptJson(optSwi${packName}hes: dict, swi${packName}hFlags: dict) -> dict:
    global rcFileName
    rawRC = {}
    if rcFileName.is_file():
        with open(rcFileName, "r") as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwi${packName}hes
    for swi${packName}hFlag in swi${packName}hFlags.keys():  # fill in missing items'
        try:
            _ = rawRC["swi${packName}hFlags"][swi${packName}hFlag]
        except:
            rawRC["swi${packName}hFlags"][swi${packName}hFlag] = False
    # printIt(formatOptStr(rawRC["swi${packName}hFlags"]), lable.INFO)
    with open(rcFileName, "w") as wf:
        json.dump(rawRC, wf, indent=2)
    return rawRC


def formatOptStr(optSwi${packName}hes: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwi${packName}hes:
        rtnStr += f"-{cmdOpt}={optSwi${packName}hes[cmdOpt]}, "
    rtnStr = rtnStr[:-2]
    return rtnStr
"""))

