#!/usr/bin/python
from string import Template
from textwrap import dedent

mainFile = dedent("""import sys, os
from .classes.argParse import ArgParse
from .commands.cmdSwitchbord import cmdSwitchbord

def main():
        #packName = os.path.basename(sys.argv[0])
        argParse = ArgParse()
        cmdSwitchbord(argParse)

if __name__ == '__main__':
    main()
""")
cmdSwitchbordFileStr = dedent("""import sys, traceback
from argparse import Namespace
from ..defs.logIt import printIt, lable
from .commands import Commands
from .cmdOptSwitchbord import cmdOptSwitchbord
from ..classes.argParse import ArgParse

cmdObj = Commands()
commands = cmdObj.commands
switchFlags = cmdObj.switchFlags["switcheFlags"]

def cmdSwitchbord(argParse: ArgParse):
    global commands
    theCmd = 'notSet'
    try:
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                switchFlagChk = sys.argv[2]
                # Only handle single hyphen options here, let double hyphen pass through
                if len(sys.argv) == 3 and switchFlagChk[0] in '-+?' and not switchFlagChk.startswith('--'):
                    if switchFlagChk[1:] in switchFlags.keys():
                        print(f'00001: {switchFlagChk}')
                        cmdOptSwitchbord(switchFlagChk, switchFlags)
                    else:
                        if switchFlagChk not in ["-h", "--help"]:
                            printIt(f'{switchFlagChk} not defined',lable.WARN)
                        else:
                            argParse.parser.print_help()
                    exit()
            args: Namespace = argParse.args
            theCmd = args.commands[0]
            if theCmd in commands.keys():
                exec(f'from ..commands.{theCmd} import {theCmd}')
                exec(f'{theCmd}(argParse)')
            else:
                theArgs = args.arguments
                argIndex = 0
                while argIndex < len(theArgs):
                    anArg = theArgs[argIndex]
                    printIt(f"argument {str(argIndex).zfill(2)}: {anArg}", lable.INFO)
                    argIndex += 1
                if len(theArgs) == 0:
                    printIt("no argument(s) entered", lable.INFO)
        else:
            argParse.parser.print_help()
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'{theCmd}\\n{tb_str}', lable.ERROR)
        exit()
""")
cmdOptSwitchbordFileStr = dedent("""from ..classes.optSwitches import OptSwitches

def cmdOptSwitchbord(switchFlag: str, switchFlags: str):
    optSwitches = OptSwitches(switchFlags)
    optSwitches.toggleSwitchFlag(switchFlag)
""")
newCmdTemplateStr = """from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

cmdObj = Commands()
commands = cmdObj.commands

def ${defName}(argParse):
    global commands
    args = argParse.args
    theCmd = args.commands[0]
    theArgNames = list(commands[theCmd].keys())
    theArgs = args.arguments
    argIndex = 0
    nonCmdArg = True
    printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.DEBUG)
    # delete place holder code bellow that loops though arguments provided
    # when this command is called when not needed.
    # Note: that function having a name that is entered as an argument part
    # of this code and is called using the built in exec function. while argIndex < len(theArgs):
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands[theCmd]:
            nonCmdArg = False
            exec(f"{anArg}(argParse)")
        elif nonCmdArg:  # not a know aregument for this {packName} {defName} command
            if len(theArgNames) > 1:
                printIt(f"{theArgNames[argIndex+1]}: {anArg}",lable.INFO)
            else:
                printIt(f"unknown argument: {anArg}", lable.INFO)
        argIndex += 1
    if len(theArgs) == 0:
        printIt("no argument(s) entered", lable.INFO)

"""
argDefTemplateStr = dedent("""def ${argName}(argParse):
    args = argParse.args
    printIt(args, lable.INFO)

""")
asyncTemplateStr = """import asyncio
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

async def ${defName}_async(argParse):
    '''Async implementation of ${defName} command'''
    args = argParse.args
    theCmd = args.commands[0]
    theArgs = args.arguments

    printIt(f"Starting async {theCmd} command", lable.INFO)

    if len(theArgs) == 0:
        printIt("No arguments provided", lable.WARN)
        return

    # Process arguments asynchronously
    tasks = []
    for arg in theArgs:
        tasks.append(process_argument_async(arg))

    results = await asyncio.gather(*tasks)
    printIt(f"Completed processing {len(results)} arguments", lable.PASS)

async def process_argument_async(arg):
    '''Process individual argument asynchronously'''
    # Simulate async work
    await asyncio.sleep(0.1)
    printIt(f"Processed: {arg}", lable.INFO)
    return arg

def ${defName}(argParse):
    '''Entry point for async ${defName} command'''
    asyncio.run(${defName}_async(argParse))

"""
classCallTemplateStr = """from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

class ${defName}Command:
    def __init__(self, argParse):
        self.argParse = argParse
        self.cmdObj = Commands()
        self.commands = self.cmdObj.commands
        self.args = argParse.args
        self.theCmd = self.args.commands[0]
        self.theArgNames = list(self.commands[self.theCmd].keys())
        self.theArgs = self.args.arguments

    def execute(self):
        '''Main execution method for ${defName} command'''
        printIt(f"Executing {self.theCmd} command with class-based approach", lable.INFO)

        if len(self.theArgs) == 0:
            printIt("No arguments provided", lable.WARN)
            return

        argIndex = 0
        while argIndex < len(self.theArgs):
            anArg = self.theArgs[argIndex]
            method_name = f"handle_{anArg}"
            if hasattr(self, method_name):
                getattr(self, method_name)()
            else:
                printIt(f"Processing argument: {anArg}", lable.INFO)
            argIndex += 1

def ${defName}(argParse):
    '''Entry point for ${defName} command'''
    command_instance = ${defName}Command(argParse)
    command_instance.execute()


"""
simpleTemplateStr = """from ..defs.logIt import printIt, lable

def ${defName}(argParse):
    '''Simple ${defName} command implementation'''
    args = argParse.args
    arguments = args.arguments

    printIt(f"Running ${defName} command", lable.INFO)

    if len(arguments) == 0:
        printIt("No arguments provided", lable.WARN)
        return

    for i, arg in enumerate(arguments):
        printIt(f"Argument {i+1}: {arg}", lable.INFO)


"""
newCmdStr = dedent("""import os, sys, copy
from ..defs.logIt import printIt, lable
from ..classes.argParse import ArgParse
from .commands import Commands, cmdDescriptionTagStr
from .templates.newCmd import cmdDefTemplate, argDefTemplate
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

def newCmd(argParse: ArgParse):
    args = argParse.args

    # Handle --templates option to list available templates
    if hasattr(argParse, 'cmd_options') and 'templates' in argParse.cmd_options:
        list_templates()
        return

    cmdObj = Commands()
    argsDict = args.arguments

    if len(argsDict) == 0:
        printIt("Command name required", lable.ERROR)
        return

    newCmdName = args.arguments[0]
    if newCmdName not in cmdObj.commands.keys():
        theArgs = verifyArgsWithDiscriptions(cmdObj, argsDict)
        updateCMDJson(cmdObj, theArgs)

        # Determine template to use
        template_name = 'newCmd'  # default
        if hasattr(argParse, 'cmd_options') and 'template' in argParse.cmd_options:
            template_name = argParse.cmd_options['template']
            if not template_exists(template_name):
                printIt(f"Template '{template_name}' not found. Using default template.", lable.WARN)
                template_name = 'newCmd'

        writeCodeFile(theArgs, template_name)
        printIt(f'"{newCmdName}" added using {template_name} template.', lable.NewCmd)
    else:
        printIt(f'"{newCmdName}" exists. use modCmd or rmCmd to modify or remove this command.', lable.INFO)

def list_templates():
    '''List all available templates'''
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    templates = []

    for file in os.listdir(template_dir):
        if file.endswith('.py') and file != '__init__.py':
            template_name = file[:-3]  # Remove .py extension
            templates.append(template_name)

    printIt("Available templates:", lable.INFO)
    for template in sorted(templates):
        printIt(f"  - {template}", lable.INFO)

def template_exists(template_name):
    '''Check if a template exists'''
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    template_file = os.path.join(template_dir, f'{template_name}.py')
    return os.path.isfile(template_file)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        if argName[0] == '-':
            if len(argName) >= 2:
                if argName[2] == '-':
                    printIt("Only single hyphen options allowed.",lable.WARN)
                    exit(0)
                else:
                    theDisc = input(f'Enter help description for {argName}:\\n')
                    if theDisc == '': theDisc = f'no help for {argName}'
            else:
                printIt("Missing ascii letters after hyphen.",lable.WARN)
                exit(0)
        else:
            theDisc = input(f'Enter help description for {argName}:\\n')
            if theDisc == '': theDisc = f'no help for {argName}'
        rtnDict[argName] = theDisc
        argIndex += 1
    return rtnDict

def writeCodeFile(theArgs: dict, template_name: str = 'newCmd') -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs, template_name)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr

def cmdCodeBlock(theArgs: dict, template_name: str = 'newCmd') -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]

    # Import the specified template
    try:
        template_module = __import__(f'myPack.commands.templates.{template_name}', fromlist=['cmdDefTemplate', 'argDefTemplate'])
        cmdDefTemplate = template_module.cmdDefTemplate
        argDefTemplate = template_module.argDefTemplate
    except ImportError:
        printIt(f"Could not import template '{template_name}', using default", lable.WARN)
        from .templates.newCmd import cmdDefTemplate, argDefTemplate

    rtnStr = cmdDefTemplate.substitute(
        packName=packName, defName=cmdName,
    )
    argIndex = 1
    while argIndex < len(argNames): # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argDefTemplate.substitute(argName=argName)
        argIndex += 1
    return rtnStr

def updateCMDJson(cmdObj: Commands, theArgs:  dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defDiscription = theArgs[argNames[0]]
    commands[defName] = {}
    commands[defName][f'{defName}{cmdDescriptionTagStr}'] = defDiscription
    argIndex = 1
    while argIndex < len(theArgs): # add subarg functions
        argName = argNames[argIndex]
        commands[defName][argName] = theArgs[argName]
        argIndex += 1
    cmdObj.commands = commands
""")

modCmdStr = dedent("""import os, copy
from ..defs.logIt import printIt, lable
from ..classes.argParse import ArgParse
from .commands import Commands, cmdDescriptionTagStr
from .templates.newCmd import cmdDefTemplate, argDefTemplate
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

cmdObj = Commands()
commands = cmdObj.commands

def modCmd(argParse: ArgParse):
    args = argParse.args
    #cmd = args.commands
    cmdObj = Commands()
    modCmdName = args.arguments[0]
    if modCmdName in cmdObj.commands.keys():
        theArgs = verifyArgsWithDiscriptions(cmdObj, args.arguments)
        if len(theArgs.keys()) > 0:
            updateCMDJson(cmdObj, modCmdName, theArgs)
            printIt(f'"{modCmdName}" modified.',lable.ModCmd)
        else:
            printIt(f'"{modCmdName}" unchanged.',lable.INFO)
    else:
        printIt(f'"{modCmdName}" does not exists. use newCmd or add it.',lable.INFO)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        if argName[0] == '-':
            if len(argName) >= 2:
                if argName[2] == '-':
                    printIt("Only single hyphen options allowed.",lable.WARN)
                    exit(0)
                else:
                    theDisc = input(f'Enter help description for {argName}:\\n')
                    if theDisc == '': theDisc = f'no help for {argName}'
            else:
                printIt("Missing ascii letters after hyphen.",lable.WARN)
                exit(0)
        else:
            theDisc = ''
            saveDisc = False
            if argIndex == 0 and len(theArgs) == 1:
                chgDisc = input(f'Replace description for {argName} (y/N): ')
                if chgDisc.lower() == 'y':
                    saveDisc = True
            elif argIndex > 0:
                if argName in cmdObj.commands[cmdName].keys():
                    chgDisc = input(f'Replace description for {argName} (y/N): ')
                    if chgDisc.lower() == 'y':
                        saveDisc = True
                else: # add new arg
                    saveDisc = True
                    newArg = True
            if saveDisc:
                theDisc = input(f'Enter help description for {argName}:\\n')
                if theDisc == '': theDisc = f'no help for {argName}'
        if saveDisc:
            # only poulate rtnDict with modified discriptions
            rtnDict[argName] = theDisc
        argIndex += 1
    return rtnDict

def writeCodeFile(theArgs: dict) -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr

def cmdCodeBlock(theArgs: dict) -> str:
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defTemp = cmdDefTemplate
    argTemp = argDefTemplate
    rtnStr = defTemp.substitute(
        defName=defName
    )
    argIndex = 1
    while argIndex < len(argNames): # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argTemp.substitute(argName=theArgs[argName])
        argIndex += 1
    return rtnStr

def updateCMDJson(cmdObj: Commands, modCmdName: str, theArgs:  dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    if modCmdName in argNames:
        commands[modCmdName][f'{modCmdName}{cmdDescriptionTagStr}'] = theArgs[modCmdName]
        argIndex = 1
    else: argIndex = 0
    while argIndex < len(theArgs): # add subarg functions
        argName = argNames[argIndex]
        commands[modCmdName][argName] = theArgs[argName]
        argIndex += 1
    cmdObj.commands = commands
""")
rmCmdStr = dedent("""import os, json
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

cmdObj = Commands()
commands = cmdObj.commands
theDir = os.path.dirname(os.path.realpath(__file__))
jsonFileName = os.path.join(theDir,'commands.json')

def rmCmd(argParse):
    global commands
    args = argParse.args
    theArgs = args.arguments
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands and len(theArgs) == 1:
            if anArg == cmdName:
                if anArg in ["newCmd", "modCmd", "rmCmd"]:
                    printIt(f'Permission denied for "{anArg}".',lable.WARN)
                    exit(0)
                chkRm: str = input(f"Perminantly delete {anArg} (y/N): ")
                if chkRm == '': chkRm = 'N'
                if chkRm.lower() == 'y':
                    removeCmd(anArg)
            else:
                printIt(f'Command "{anArg}" must be removed seperataly from "{cmdName}".',lable.WARN)
        elif cmdName in commands:
            if anArg in commands[cmdName]:
                chkRm: str = input(f"Perminantly delete {anArg} (y/N): ")
                if chkRm == '': chkRm = 'N'
                if chkRm.lower() == 'y':
                    removeCmdArg(cmdName, anArg)
        else:
            printIt(f'"{cmdName}" is not currently a Command.',lable.WARN)
            argIndex = len(theArgs)
        argIndex += 1

def removeCmdArg(cmdName, argName):
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        del theJson[cmdName][argName]
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)
    printIt(argName,lable.RmArg)

def removeCmd(cmdName):
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        del theJson[cmdName]
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)
    pyFileName = f'{cmdName}.py'
    pyFileName = os.path.join(theDir, pyFileName)
    if os.path.isfile(pyFileName):
        os.remove(pyFileName)
    printIt(cmdName,lable.RmCmd)
""")
commandsJsonDict = {
  "switcheFlags": {},
  "newCmd": {
    "newCmd_description": "Add new command <cmdName> with [argNames...]. Also creates a file cmdName.py.",
    "cmdName": "Name of new command",
    "argName": "(argName...), Optional names of argument to associate with the new command."
  },
  "modCmd": {
    "modCmd_description": "Modify a command or argument discriptions, or add another argument for command. The cmdName.py file will not be modified.",
    "cmdName": "Name of command being modified",
    "argName": "(argName...) Optional names of argument(s) to modify."
  },
  "rmCmd": {
    "rmCmd_description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
    "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
    "argName": "Optional names of argument to remove.v It is and I am both pi."
  }
}
commandsFileStr = dedent("""import json, os
from copy import copy
import inspect

cmdDescriptionTagStr = "_description"

class Commands(object):
    def __init__(self) -> None:
        self.cmdFileDir = os.path.dirname(inspect.getfile(self.__class__))
        self.cmdFileName = os.path.join(self.cmdFileDir, "commands.json" )
        with open(self.cmdFileName, "r") as fr:
            rawJson = json.load(fr)
            self._switchFlags = {}
            try:
                self._switchFlags["switcheFlags"] = copy(rawJson["switcheFlags"])
                del rawJson["switcheFlags"]
            except: self._switchFlags["switcheFlags"] = {}
            self._commands = rawJson
        self.checkForUpdates()

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
            if aFile[:-2] == "py":
                chkName = aFile[:-3]
                if chkName not in self.commands and chkName != "commands":
                    self.commands[chkName] = [" - No argument"]
""")
optSwitchesTemplate = Template(dedent("""import json
from pathlib import Path
from ..defs.logIt import printIt, lable


rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath(f'.${name}rc')

class OptSwitches():
    def __init__(self, switchFlags: dict) -> None:
        self.switchFlags = switchFlags
        self.optSwitches = readOptSwitches()

    def toggleSwitchFlag(self, switchFlag: str):
        optSwitches = {}
        optSwitches["switcheFlags"] = {}
        currSwitchFlag = switchFlag[1:]
        if switchFlag[0] in '+':
            currSwitchValue = True # not (self.optSwitches["switcheFlags"][currSwitchFlag] == True)
        else:
            currSwitchValue  = False
        try:
            self.optSwitches["switcheFlags"][currSwitchFlag] = currSwitchValue
        except:
            print('here')
            self.optSwitches["switcheFlags"][currSwitchFlag] = True
        writeOptJson(self.optSwitches, self.switchFlags)

def readOptSwitches() -> dict:
    global rcFileName
    optSwitches = {}
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRcJson = json.load(rf)
        optSwitches["switcheFlags"] = rawRcJson["switcheFlags"]
    else:
        optSwitches["switcheFlags"] = {}
    return optSwitches

def writeOptJson(optSwitches: dict, switchFlags: dict) -> dict:
    global rcFileName
    rawRC = {}
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwitches
    for switchFlag in switchFlags.keys(): # fill in missing items'
        try: _ = rawRC["switcheFlags"][switchFlag]
        except: rawRC["switcheFlags"][switchFlag] = False
    printIt(formatOptStr(rawRC["switcheFlags"]), lable.INFO)
    with open(rcFileName, 'w') as wf:
        json.dump(rawRC, wf, indent=2)

def formatOptStr(optSwitches: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwitches:
        rtnStr += f'-{cmdOpt}={optSwitches[cmdOpt]}, '
    rtnStr = rtnStr[:-2]
    return rtnStr
"""))
argParseTemplate = Template(dedent("""import os, sys, argparse, shlex
from ..defs.logIt import color, cStr
from ..commands.commands import Commands, cmdDescriptionTagStr

class PiHelpFormatter(argparse.RawTextHelpFormatter):
    # Corrected _max_action_length for the indenting of subactions
    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = 'x'*indent_chg
                print('added_indent', added_indent)
                invocations.append(added_indent+get_invocation(subaction))
            #print('inv', invocations)

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length,
                                          action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])

def str_or_int(arg):
    try:
        return int(arg)  # try convert to int
    except ValueError:
        pass
    if type(arg) == str:
        return arg
    raise argparse.ArgumentTypeError("arguments must be an integer or string")

class ArgParse():

    def __init__(self):
        # Parse command-specific options (double hyphen) before main parsing
        self.cmd_options = {}
        self.filtered_args = self._extract_cmd_options(sys.argv[1:])
        if not sys.stdin.isatty():
            self.parser = argparse.ArgumentParser(add_help=False)
            self.parser.add_argument('commands', nargs=1)
            self.parser.add_argument('arguments', nargs='*')
            self.args = self.parser.parse_args(self.filtered_args)
        else:
            _, tCols = os.popen('stty size', 'r').read().split()
            tCols = int(tCols)
            indentPad = 8
            formatter_class=lambda prog: PiHelpFormatter(prog, max_help_position=8,width=tCols)
            commandsHelp = ""
            argumentsHelp = ""
            theCmds = Commands()
            commands = theCmds.commands
            switchFlag = theCmds.switchFlags["switcheFlags"]
            for cmdName in commands:
                needCmdDescription = True
                needArgDescription = True
                arguments = commands[cmdName]
                argumentsHelp += cStr(cmdName, color.YELLOW) + ': \\n'
                for argName in arguments:
                    if argName[-len(cmdDescriptionTagStr):] == cmdDescriptionTagStr:
                        cmdHelp = cStr(cmdName, color.YELLOW) + ': ' + f'{arguments[argName]}'
                        if len(cmdHelp) > tCols:
                            indentPad = len(cmdName) + 2
                            cmdHelp = formatHelpWidth(cmdHelp, tCols, indentPad)
                        else:
                            cmdHelp += '\\n'
                        commandsHelp += cmdHelp
                        needCmdDescription = False
                    else:
                        argHelp = cStr(f'  <{argName}> ', color.CYAN) + f'{arguments[argName]}'
                        if len(argHelp) > tCols:
                            indentPad = len(argName) + 5
                            argHelp = ' ' + formatHelpWidth(argHelp, tCols, indentPad)
                        else:
                            argHelp += '\\n'
                        argumentsHelp += argHelp
                        needArgDescription = False
                if needArgDescription:
                    argumentsHelp = argumentsHelp[:-1]
                    argumentsHelp += "no arguments\\n"
                if needCmdDescription:
                    commandsHelp += cStr(cmdName, color.WHITE) + '\\n'
            #   commandsHelp = commandsHelp[:-1]

            self.parser = argparse.ArgumentParser(
                description = "pi pip package pip package pip package",
                epilog="Have Fun!", formatter_class=formatter_class)

            self.parser.add_argument("commands",
                type=str,
                nargs=1,
                metavar= f'{cStr(cStr("Commands", color.YELLOW), color.UNDERLINE)}:',
                help=commandsHelp)

            self.parser.add_argument("arguments",
                type=str_or_int,
                nargs="*",
                metavar= f'{cStr(cStr("Arguments", color.CYAN), color.UNDERLINE)}:',
                #metavar="arguments:",
                help=argumentsHelp)

            for optFlag in switchFlag:
                flagHelp = switchFlag[optFlag]
                self.parser.add_argument(f'-{optFlag}', action='store_true', help=flagHelp)
            self.args = self.parser.parse_args(self.filtered_args)

    def _extract_cmd_options(self, args):
        '''Extract command-specific options(--option) from arguments'''
        filtered_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Handle command-specific options
                option_name = arg[2:]  # Remove --
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    # Option with value
                    self.cmd_options[option_name] = args[i + 1]
                    i += 2  # Skip both option and value
                else:
                    # Option without value (flag)
                    self.cmd_options[option_name] = True
                    i += 1
            else:
                filtered_args.append(arg)
                i += 1
        return filtered_args

def formatHelpWidth(theText, tCols, indentPad=1) -> str:
    # this uses the screen with to estabhish tCols

    #tCols = int(tCols) - 20
    #print(tCols)
    # tCols = 60
    spPaddingStr = ' '*indentPad
    rtnStr = ''
    outLine = ''
    tokens = shlex.split(theText)
    # print(tokens)
    # exit()
    for token in tokens:  # loop though tokens
        chkStr = outLine + token + ' '
        if len(chkStr) <= tCols:                # check line length after concatinating each word
            outLine = chkStr                    # less the the colums of copy over to outline
        else:
            if len(token) > tCols:
                # when the match word is longer then the terminal character width (tCols),
                # DEBUG how it should be handeled here.
                print(f'here with long match.group():\\n{token}')
                exit()
                chkStr = token
                while len(chkStr) > tCols: # a single word may be larger the tCols
                    outLine += chkStr[:tCols]
                    chkStr = f'\\n{chkStr[tCols:]}'
                outLine += chkStr
            else:
                rtnStr += outLine
                outLine = f'\\n{spPaddingStr}{token} '
    rtnStr += f'{outLine}\\n'
    #rtnStr = rtnStr[:-1]
    return rtnStr
"""))
logPrintTemplate = Template(dedent("""import os, time
from inspect import currentframe, getframeinfo

# Class of different termianl styles
class color():

    BLACK = "\\033[30m"
    RED = "\\033[31m"
    GREEN = "\\033[32m"
    YELLOW = "\\033[33m"
    BLUE = "\\033[34m"
    MAGENTA = "\\033[35m"
    CYAN = "\\033[36m"
    WHITE = "\\033[37m"
    UNDERLINE = "\\033[4m"
    RESET = "\\033[0m"

    # message: color
    l2cDict: dict = {
        "BK": RESET,
        "ERROR: ": RED,
        "PASS: ": GREEN,
        "WARN: ": YELLOW,
        "SAVED: ": BLUE,
        "DEBUG: ": MAGENTA,
        "REPLACED: ": CYAN,
        "INFO: ": WHITE,
        "IMPORT: ": UNDERLINE,
        "RESET": RESET,
        "File Not Found: ": YELLOW,
        "FAIL: ": RED,
        "Useage: ": WHITE,
        "DELETE: ": YELLOW,
        "EXISTS: ": GREEN,
        "READ: ": GREEN,
        "TOUCHED: ": GREEN,
        "MKDIR: ": GREEN,
        "NEW CMD ADDED: ": GREEN,
        "CMD MODIFIED: ": GREEN,
        "CMD REMOVED: ": GREEN,
        "ARG REMOVED: ": GREEN,
        "IndexError: ": RED,
        "Testing: ": CYAN,
        "Update: ": CYAN
        }


class lable():
    SAVED = "SAVED: "
    REPLACED = "REPLACED: "
    BLANK = "BK"
    ERROR = "ERROR: "
    PASS = "PASS: "
    WARN = "WARN: "
    DEBUG = "DEBUG: "
    INFO = "INFO: "
    IMPORT = "IMPORT: "
    RESET = "RESET"
    FileNotFound = "File Not Found: "
    FAIL = "FAIL: "
    Useage = "Useage: "
    MKDIR = "MKDIR: "
    DELETE = "DELETE: "
    EXISTS = "EXISTS: "
    READ = "READ: "
    TOUCHED = "TOUCHED: "
    NewCmd = "NEW CMD ADDED: "
    ModCmd = "CMD MODIFIED: "
    RmCmd = "CMD REMOVED: "
    RmArg = "ARG REMOVED: "
    IndexError = "IndexError: "
    TESTING = "Testing: "
    UPDATE = "Update: "


# log function
def logIt(*message, logFileName="${name}.log"):
    # write log
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    prtStr = ""
    needClip = False
    if len(message) > 0:
        for mess in message:
            if mess == lable.BLANK:
                pass
            elif mess in color.l2cDict:
                prtStr = mess + prtStr
            else:
                needClip = True
                prtStr += str(mess) + " "
        if needClip:
            prtStr = prtStr[:-1]

    prtStr = "["+now+"] "+prtStr+"\\n"

    with open(logFileName, "a") as f:
        f.write(prtStr)

def printIt(*message):
    prtStr = ""
    rtnStr = ""
    needClip = False
    if len(message) > 0:
        for mess in message:
            if mess == lable.BLANK:
                prtStr += message
                rtnStr += message
            elif mess in color.l2cDict:
                prtStr = color.l2cDict[mess] + mess + color.RESET + prtStr
                rtnStr = mess + rtnStr
            else:
                needClip = True
                prtStr += str(mess) + " "
                rtnStr += str(mess) + " "
        if needClip:
            prtStr = prtStr[:-1]
            rtnStr = rtnStr[:-1]
    print(prtStr)
    return rtnStr

def cStr(inStr:str, cVal:str):
    return cVal + inStr + color.RESET

def deleteLog(logFileName="${name}.log"):
    if os.path.isfile(logFileName): os.remove(logFileName)

def getCodeFile():
    cf = currentframe()
    codeObj =cf.f_back.f_code
    codeObjStr = str(codeObj).split(",")[1].split(\'"\')[1]
    codeObjStr = os.path.basename(codeObjStr)
    return codeObjStr

def getCodeLine():
    cf = currentframe()
    return cf.f_back.f_lineno
"""))