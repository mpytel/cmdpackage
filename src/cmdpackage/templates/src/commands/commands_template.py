#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

commands_template = Template(dedent("""import json
import os
from copy import copy
import inspect


class Commands(object):
    def __init__(self) -> None:
        self.cmdFileDir = os.path.dirname(inspect.getfile(self.__class__))
        self.cmdFileName = os.path.join(self.cmdFileDir, "commands.json")
        try:
            with open(self.cmdFileName, "r") as fr:
                rawJson = json.load(fr)
                self._switchFlags = {}

                # Handle global switches - check both old and new structure
                try:
                    self._switchFlags["switchFlags"] = copy(rawJson["switchFlags"])
                except:
                    self._switchFlags["switchFlags"] = {}

                # Handle commands - check if new structure with "commands" key exists
                if "commands" in rawJson:
                    # New structure - commands are under "commands" key
                    self._commands = rawJson["commands"]
                else:
                    # Old structure - remove switchFlags and everything else is commands
                    if "switchFlags" in rawJson:
                        del rawJson["switchFlags"]
                    # Remove other metadata keys that aren't commands
                    metadata_keys = ["option_switches", "option_strings", "description"]
                    for key in metadata_keys:
                        if key in rawJson:
                            del rawJson[key]
                    self._commands = rawJson

            self.checkForUpdates()

            # Verify commands.json integrity with tracked Python files
            self._verify_integrity()

        except json.decoder.JSONDecodeError:
            self.rebuildCommandsJson()

    def _verify_integrity(self):
        \"\"\"Verify commands.json integrity and auto-repair if needed\"\"\"
        try:
            from ..classes.CommandManager import command_manager

            # Quick integrity check
            if not command_manager.verify_commands_json_integrity():
                # Attempt auto-repair
                print("⚠️  Commands.json integrity issues detected. Auto-repairing...")
                if command_manager.repair_commands_json_from_python_files():
                    print("✅ Commands.json successfully repaired from Python files")
                    # Reload the commands after repair
                    with open(self.cmdFileName, "r") as fr:
                        rawJson = json.load(fr)
                        if "switchFlags" in rawJson:
                            del rawJson["switchFlags"]
                        self._commands = rawJson
                else:
                    print("❌ Failed to repair commands.json - manual intervention required")
        except Exception as e:
            # Don't let integrity check break the normal operation
            print(f"Warning: Could not verify commands.json integrity: {e}")

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, aDict: dict):
        self._commands = aDict
        self._writeCmdJsonFile()

    @property
    def switchFlags(self):
        return self._switchFlags

    @switchFlags.setter
    def switchFlags(self, aDict: dict):
        self._switchFlags = aDict
        self._writeCmdJsonFile()

    def _writeCmdJsonFile(self):
        # outJson = copy(self._switchFlags)
        # outJson.update(self._commands)
        outJson = self._switchFlags | self._commands
        with open(self.cmdFileName, "w") as fw:
            json.dump(outJson, fw, indent=2)

    def checkForUpdates(self):
        dirList = os.listdir(self.cmdFileDir)
        for aFile in dirList:
            if not aFile in [
                "commands.py",
                "__init__.py",
                "cmdOptSwtcboard.py",
                "cmdSwtcboard.py",
            ]:
                if aFile[:-2] == "py":
                    chkName = aFile[:-3]
                    if chkName not in self.commands and chkName != "commands":
                        commandJsonDict = self.extractCommandJsonDict(aFile)
                        self._commands[chkName] = commandJsonDict
        self._writeCmdJsonFile()

    def rebuildCommandsJson(self):
        dirList = os.listdir(self.cmdFileDir)
        self._commands = {}
        for aFile in dirList:
            if not aFile in [
                "commands.py",
                "__init__.py",
                "cmdOptSwtcboard.py",
                "cmdSwtcboard.py",
            ]:
                if aFile[:-2] == "py":
                    chkName = aFile[:-3]
                    commandJsonDict = self.extractCommandJsonDict(aFile)
                    self._commands[chkName] = commandJsonDict
        self._writeCmdJsonFile()

    def extractCommandJsonDict(self, fileName: str) -> dict:
        cmdJsonDict = {}
        filePath = os.path.join(self.cmdFileDir, fileName)
        with open(filePath, "r") as fr:
            fileLines = fr.readlines()
        inCmdJsonDict = False
        cmdJsonLines = []
        for line in fileLines:
            if line.strip().startswith("commandJsonDict = {"):
                inCmdJsonDict = True
            if inCmdJsonDict:
                cmdJsonLines.append(line)
            if inCmdJsonDict and line.strip().endswith("}"):
                inCmdJsonDict = False
                break
        cmdJsonStr = "".join(cmdJsonLines).replace("commandJsonDict =", "").strip()
        try:
            cmdJsonDict = json.loads(cmdJsonStr)
            cmdName = list(cmdJsonDict.keys())[0]
            self._commands[cmdName] = cmdJsonDict[cmdName]
        except json.JSONDecodeError:
            pass
        return cmdJsonDict
"""))

