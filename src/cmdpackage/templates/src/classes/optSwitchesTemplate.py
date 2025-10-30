#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

optSwitchesTemplate = Template(
    dedent(
        """import json
from pathlib import Path
from ..defs.logIt import printIt, lable

rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath(f'.${packName}rc')

class OptSwitches():
    def __init__(self, switchFlags: dict) -> None:
        self.switchFlags = switchFlags
        self.optSwitches = readOptSwitches()

    def toggleSwitchFlag(self, switchFlag: str):
        optSwitches = {}
        optSwitches["switchFlags"] = {}
        currSwitchFlag = switchFlag[1:]
        if switchFlag[0] in '+':
            currSwitchValue = True # not (self.optSwitches["switchFlags"][currSwitchFlag] == True)
        else:
            currSwitchValue  = False
        try:
            self.optSwitches["switchFlags"][currSwitchFlag] = currSwitchValue
        except:
            print('here')
            self.optSwitches["switchFlags"][currSwitchFlag] = True
        writeOptJson(self.optSwitches, self.switchFlags)
                                      
def saveCmdSwitchFlags(cmdName: str, cmdOptions: dict, cmdSwitchFlags: dict):
    \"\"\"Save command-specific switch flags to .${packName}rc\"\"\"
    rcData = readOptSwitches()
    
    # Initialize command flags section if it doesn't exist
    if 'commandFlags' not in rcData:
        rcData['commandFlags'] = {}
    if cmdName not in rcData['commandFlags']:
        rcData['commandFlags'][cmdName] = {}
    
    # Process each command option
    for optionName, optionValue in cmdOptions.items():
        if optionName in cmdSwitchFlags:
            flagDef = cmdSwitchFlags[optionName]
            if flagDef['type'] == 'bool':
                # Boolean flag - store true/false
                rcData['commandFlags'][cmdName][optionName] = bool(optionValue)
            elif flagDef['type'] == 'str':
                # String option - store the value (or empty string if not provided)
                if optionValue == '__STRING_OPTION__':
                    rcData['commandFlags'][cmdName][optionName] = ""
                else:
                    rcData['commandFlags'][cmdName][optionName] = str(optionValue)
    
    # Write back to file
    with open(rcFileName, 'w') as wf:
        json.dump(rcData, wf, indent=2)
    
    printIt(f"Command flags saved for '{cmdName}'", lable.INFO)

def toggleCmdSwitchFlag(cmdName: str, flagName: str, setValue: bool):
    \"\"\"Toggle a command-specific boolean flag in .${packName}rc\"\"\"
    rcData = readOptSwitches()
    
    # Initialize command flags section if it doesn't exist
    if 'commandFlags' not in rcData:
        rcData['commandFlags'] = {}
    if cmdName not in rcData['commandFlags']:
        rcData['commandFlags'][cmdName] = {}
    
    # Set the flag value
    rcData['commandFlags'][cmdName][flagName] = setValue
    
    # Write back to file
    with open(rcFileName, 'w') as wf:
        json.dump(rcData, wf, indent=2)
    
    status = "enabled" if setValue else "disabled"
    printIt(f"Command flag '{flagName}' {status} for '{cmdName}'", lable.INFO)

def getCmdSwitchFlags(cmdName: str) -> dict:
    \"\"\"Get stored command-specific switch flags from .${packName}rc\"\"\"
    rcData = readOptSwitches()
    return rcData.get('commandFlags', {}).get(cmdName, {})
                                      
def removeCmdSwitchFlags(cmdName: str):
    \"\"\"Remove command-specific switch flags from .${packName}rc when command is deleted\"\"\"
    rcData = readOptSwitches()
    
    # Check if command exists in commandFlags
    if 'commandFlags' in rcData and cmdName in rcData['commandFlags']:
        del rcData['commandFlags'][cmdName]
        
        # If commandFlags is now empty, we can remove the whole section
        if not rcData['commandFlags']:
            del rcData['commandFlags']
        
        # If the entire file would be empty or only has empty sections, delete the file
        if not rcData.get('switchFlags') and not rcData.get('commandFlags'):
            if rcFileName.is_file():
                rcFileName.unlink()
                # printIt(f"Removed '{cmdName}' flags and deleted empty .${packName}rc file", lable.INFO)
        else:
            # Write back the updated file
            with open(rcFileName, 'w') as wf:
                json.dump(rcData, wf, indent=2)
            # printIt(f"Removed '{cmdName}' flags from .${packName}rc", lable.INFO)
    else:
        # printIt(f"No flags found for '{cmdName}' in .${packName}rc", lable.INFO)
        pass

def readOptSwitches() -> dict:
    global rcFileName
    optSwitches = {}
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
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
        with open(rcFileName, 'r') as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwitches
    for switchFlag in switchFlags.keys(): # fill in missing items'
        try: _ = rawRC["switchFlags"][switchFlag]
        except: rawRC["switchFlags"][switchFlag] = False
    # printIt(formatOptStr(rawRC["switchFlags"]), lable.INFO)
    with open(rcFileName, 'w') as wf:
        json.dump(rawRC, wf, indent=2)
    return rawRC
                                      
def formatOptStr(optSwitches: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwitches:
        rtnStr += f'-{cmdOpt}={optSwitches[cmdOpt]}, '
    rtnStr = rtnStr[:-2]
    return rtnStr
"""
    )
)