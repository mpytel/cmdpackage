#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

commands_template = Template(dedent("""import json, os
from copy import copy
import inspect


class Commands(object):
    def __init__(self) -> None:
        self.cmdFileDir = os.path.dirname(inspect.getfile(self.__class__))
        self.cmdFileName = os.path.join(self.cmdFileDir, "commands.json")
        try:
            with open(self.cmdFileName, "r") as fr:
                rawJson = json.load(fr)
                self._swi${packName}hFlags = {}
                try:
                    self._swi${packName}hFlags["swi${packName}hFlags"] = copy(rawJson["swi${packName}hFlags"])
                    del rawJson["swi${packName}hFlags"]
                except:
                    self._swi${packName}hFlags["swi${packName}hFlags"] = {}
                self._commands = rawJson
            self.checkForUpdates()
        except json.decoder.JSONDecodeError:
            self.rebuildCommandsJson()

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, aDict: dict):
        self._commands = aDict
        self._writeCmdJsonFile()

    @property
    def swi${packName}hFlags(self):
        return self._swi${packName}hFlags

    @swi${packName}hFlags.setter
    def swi${packName}hFlags(self, aDict: dict):
        self._swi${packName}hFlags = aDict
        self._writeCmdJsonFile()

    def _writeCmdJsonFile(self):
        # outJson = copy(self._swi${packName}hFlags)
        # outJson.update(self._commands)
        outJson = self._swi${packName}hFlags | self._commands
        with open(self.cmdFileName, "w") as fw:
            json.dump(outJson, fw, indent=2)

    def checkForUpdates(self):
        dirList = os.listdir(self.cmdFileDir)
        for aFile in dirList:
            if not aFile in [
                "commands.py",
                "__init__.py",
                "cmdOptSwi${packName}hboard.py",
                "cmdSwi${packName}hboard.py",
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
                "cmdOptSwi${packName}hboard.py",
                "cmdSwi${packName}hboard.py",
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

