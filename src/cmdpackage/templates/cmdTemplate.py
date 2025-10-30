#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

# Template source file mappings
templateSources = {
    "argCmdDef": "src/${packName}/commands/templates/argCmdDef.py",
    "asyncDef": "src/${packName}/commands/templates/asyncDef.py",
    "classCall": "src/${packName}/commands/templates/classCall.py",
    "cmdOptSwitchbordFileStr": "src/${packName}/commands/cmdOptSwitchbord.py",
    "cmdSwitchbordFile": "src/${packName}/commands/cmdSwitchbord.py",
    "commandsFileStr": "src/${packName}/commands/commands.py",
    "commandsJsonDict": "src/${packName}/commands/commands.json",
    "fileDiffTemplate": "src/${packName}/commands/fileDiff.py",
    "argParseTemplate": "src/${packName}/classes/argParse.py",
    "logPrintTemplate": "src/${packName}/defs/logIt.py",
    "mainFile": "src/${packName}/main.py",
    "modCmd": "src/${packName}/commands/modCmd.py",
    "newCmd": "src/${packName}/commands/newCmd.py",
    "optSwitchesTemplate": "src/${packName}/classes/optSwitches.py",
    "rmCmd": "src/${packName}/commands/rmCmd.py",
    "runTest": "src/${packName}/commands/runTest.py",
    "simple": "src/${packName}/commands/templates/simple.py",
    "validationTemplate": "src/${packName}/defs/validation.py",
}

mainFile = dedent(
    """import sys, os
from .classes.argParse import ArgParse
from .commands.cmdSwitchbord import cmdSwitchbord

def main():
        #packName = os.path.basename(sys.argv[0])
        argParse = ArgParse()
        cmdSwitchbord(argParse)

if __name__ == '__main__':
    main()
"""
)

cmdSwitchbordFile = Template(
    dedent(
        """import sys, traceback
from argparse import Namespace
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands
from .cmdOptSwitchbord import cmdOptSwitchbord
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdSwitchFlags, toggleCmdSwitchFlag

cmdObj = Commands()
commands = cmdObj.commands
switchFlags = cmdObj.switchFlags["switchFlags"]
                              
def printCommandHelp(cmdName: str):
    \"\"\"Print help for a specific command\"\"\"
    if cmdName not in commands:
        printIt(f"Command '{cmdName}' not found", lable.ERROR)
        return
    
    cmdInfo = commands[cmdName]
    
    # Print command description
    description = cmdInfo.get('description', 'No description available')
    printIt(f"\\n{cStr(cmdName, color.YELLOW)}: {description}\\n", lable.INFO)
    
    # Build usage line
    usage_parts = [f"${packName} {cmdName}"]
    
    # Add arguments
    args = []
    for key, value in cmdInfo.items():
        if key not in ['description', 'switchFlags'] and isinstance(value, str):
            args.append(f"<{key}>")
    
    if args:
        usage_parts.extend(args)
    
    # Add option flags
    switchFlags = cmdInfo.get('switchFlags', {})
    if switchFlags:
        flag_parts = []
        for flagName, flagInfo in switchFlags.items():
            if flagInfo.get('type') == 'bool':
                flag_parts.append(f"[+{flagName}|-{flagName}]")
            elif flagInfo.get('type') == 'str':
                flag_parts.append(f"[--{flagName} <value>]")
        usage_parts.extend(flag_parts)
    
    # Print usage
    usage = " ".join(usage_parts)
    printIt(f"{cStr('Usage:', color.CYAN)} {usage}\\n", lable.INFO)
    
    # Print arguments section
    if args:
        printIt(f"{cStr('Arguments:', color.CYAN)}", lable.INFO)
        for key, value in cmdInfo.items():
            if key not in ['description', 'switchFlags'] and isinstance(value, str):
                printIt(f"  {cStr(f'<{key}>', color.WHITE)}  {value}", lable.INFO)
        print()  # Extra line
    
    # Print option flags section
    if switchFlags:
        printIt(f"{cStr('Option Flags:', color.CYAN)}", lable.INFO)
        for flagName, flagInfo in switchFlags.items():
            flagType = flagInfo.get('type', 'unknown')
            flagDesc = flagInfo.get('description', 'No description')
            
            if flagType == 'bool':
                printIt(f"  {cStr(f'+{flagName}', color.GREEN)}   Enable: {flagDesc}", lable.INFO)
                printIt(f"  {cStr(f'-{flagName}', color.RED)}   Disable: {flagDesc}", lable.INFO)
            elif flagType == 'str':
                printIt(f"  {cStr(f'--{flagName}', color.YELLOW)} <value>  {flagDesc}", lable.INFO)
        print()  # Extra line
    
    # Print examples if the command has flags
    if switchFlags:
        printIt(f"{cStr('Examples:', color.CYAN)}", lable.INFO)
        example_parts = [f"${packName} {cmdName}"]
        if args:
            example_parts.append("arg1")
        
        # Show flag examples
        bool_flags = [name for name, info in switchFlags.items() if info.get('type') == 'bool']
        str_flags = [name for name, info in switchFlags.items() if info.get('type') == 'str']
        
        if str_flags:
            example_parts.append(f"--{str_flags[0]} value")
        if bool_flags:
            example_parts.append(f"+{bool_flags[0]}")
        
        printIt(f"  {' '.join(example_parts)}", lable.INFO)
        
        if bool_flags:
            printIt(f"  ${packName} {cmdName} -{bool_flags[0]}  # Disable {bool_flags[0]} flag", lable.INFO)

def cmdSwitchbord(argParse: ArgParse):
    global commands
    theCmd = 'notSet'
    flag_toggle_occurred = False  # Track if a flag toggle happened
    try:
        if len(sys.argv) > 1:
            # Handle direct help flags like '${packName} -h'
            if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
                argParse.parser.print_help()
                exit()
            
            if len(sys.argv) > 2:
                # Handle command-specific help: ${packName} command -h or ${packName} command --help
                if sys.argv[2] in ["-h", "--help"]:
                    cmdName = sys.argv[1]
                    printCommandHelp(cmdName)
                    exit()
                
                # Check for flag toggle operations anywhere in the arguments
                cmdName = sys.argv[1]
                for i in range(2, len(sys.argv)):
                    arg = sys.argv[i]
                    if arg[0] in '-+?' and not arg.startswith('--') and len(arg) > 1:
                        flagName = arg[1:]
                        
                        # Check if it's a global switch flag first
                        if flagName in switchFlags.keys():
                            cmdOptSwitchbord(arg, switchFlags)
                        
                        # Check if it's a command-specific flag
                        if cmdName in commands and 'switchFlags' in commands[cmdName]:
                            cmdSwitchFlags = commands[cmdName]['switchFlags']
                            if flagName in cmdSwitchFlags and cmdSwitchFlags[flagName].get('type') == 'bool':
                                # This is a command-specific boolean flag
                                setValue = arg[0] == '+'
                                toggleCmdSwitchFlag(cmdName, flagName, setValue)
                                flag_toggle_occurred = True
                
                # Handle old logic for backward compatibility only if flag toggle didn't occur above
                if not flag_toggle_occurred:
                    switchFlagChk = sys.argv[2]
                    # Only handle single hyphen options here, let double hyphen pass through
                    if len(sys.argv) == 3 and switchFlagChk[0] in '-+?' and not switchFlagChk.startswith('--'):
                        flagName = switchFlagChk[1:]
                    
                         # Check if it's a global switch flag first
                        if flagName in switchFlags.keys():
                            cmdOptSwitchbord(switchFlagChk, switchFlags)
                            exit()
                    
                        # Check if it's a command-specific flag
                        cmdName = sys.argv[1]
                        if cmdName in commands and 'switchFlags' in commands[cmdName]:
                            cmdSwitchFlags = commands[cmdName]['switchFlags']
                            if flagName in cmdSwitchFlags and cmdSwitchFlags[flagName].get('type') == 'bool':
                                # This is a command-specific boolean flag
                                setValue = switchFlagChk[0] == '+'
                                toggleCmdSwitchFlag(cmdName, flagName, setValue)
                                flag_toggle_occurred = True
                                # Don't exit here - let the command execute with the new flag setting
                    
                        # Not a recognized flag
                        if not flag_toggle_occurred:
                            if switchFlagChk not in ["-h", "--help"]:
                                printIt(f'{switchFlagChk} not defined',lable.WARN)
                            else:
                                argParse.parser.print_help()
                            exit()

            args: Namespace = argParse.args
            theCmd = args.commands[0]
            if theCmd in commands.keys():
                # Save command-specific switch flags before executing command
                # Skip if a flag toggle already occurred to avoid overwriting the toggle
                if hasattr(argParse, 'cmd_options') and argParse.cmd_options and not flag_toggle_occurred:
                    cmdSwitchFlags = commands[theCmd].get('switchFlags', {})
                    if cmdSwitchFlags:
                        saveCmdSwitchFlags(theCmd, argParse.cmd_options, cmdSwitchFlags)
              
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
"""
    )
)

cmdOptSwitchbordFileStr = dedent(
    """from ..classes.optSwitches import OptSwitches

def cmdOptSwitchbord(switchFlag: str, switchFlags: dict):
    optSwitches = OptSwitches(switchFlags)
    optSwitches.toggleSwitchFlag(switchFlag)
"""
)

argCmdDefTemplateStr = dedent(
    """# Generated using argCmdDef template
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

cmdObj = Commands()
commands = cmdObj.commands

def ${defName}(argParse):
    global commands
    args = argParse.args
    theCmd = args.commands[0]
    theArgNames = list(commands[theCmd].keys())
    # filter out 'description'a 'switchFlags' from argument names
    theArgNames = [arg for arg in theArgNames if arg not in ['description', 'switchFlags']]
    theArgs = args.arguments
    argIndex = 0
    nonCmdArg = True
    # printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.DEBUG)
    # delete place holder code bellow that loops though arguments provided
    # when this command is called when not needed.
    # Note: that function having a name that is entered as an argument part
    # of this code and is called using the built in exec function. while argIndex < len(theArgs):
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands[theCmd]:
            nonCmdArg = False
            exec(f"{anArg}(argParse)")
        # process know and unknown aregument for this {packName} {defName} command
        elif nonCmdArg:
            if argIndex+1 > len(theArgNames):
                printIt(f"unknown argument: {anArg}", lable.INFO)
            else:
                printIt(f"{theArgNames[argIndex]}: {anArg}", lable.INFO)
        argIndex += 1
    if len(theArgs) == 0:
        printIt("no argument(s) entered", lable.INFO)

"""
)

argDefTemplateStr = dedent(
    """def ${argName}(argParse):
    args = argParse.args
    printIt("def ${defName} executed.", lable.INFO)
    printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.INFO)
    printIt(str(args), lable.INFO)

"""
)

asyncDefTemplateStr = dedent(
    """# Generated using asyncDef template
import asyncio
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

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
)

classCallTemplateStr = dedent(
    """# Generated using classCall template
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

${commandJsonDict}

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
)

simpleTemplateStr = dedent(
    """# Generated using simple template
from ..defs.logIt import printIt, lable

${commandJsonDict}

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
)

newCmdTemplate = Template(
    dedent(
        """import os, sys, copy
import importlib
import readline
from json import dumps
from ..defs.logIt import printIt, lable
from ..defs.validation import validate_argument_name, check_command_uses_argcmddef_template
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdSwitchFlags
from .commands import Commands
from .templates.argCmdDef import cmdDefTemplate, argDefTemplate
from .templates.argCmdDef import cmdDefTemplate, argDefTemplate

${commandJsonDict}

readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

def newCmd(argParse: ArgParse):
    args = argParse.args

    # Handle --templates option to list available templates
    if hasattr(argParse, 'cmd_options') and 'templates' in argParse.cmd_options:
        # If templates option has a value, use it as template name
        if argParse.cmd_options['templates'] != '__STRING_OPTION__' and argParse.cmd_options['templates'] is not True:
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
        template_name = 'argCmdDef'  # default
        if hasattr(argParse, 'cmd_options'):
            # Check for --template option
            if 'template' in argParse.cmd_options:
                template_name = argParse.cmd_options['template']
            # Check for --templates=value option
            elif 'templates' in argParse.cmd_options and argParse.cmd_options['templates'] not in ['__STRING_OPTION__', True]:
                template_name = argParse.cmd_options['templates']
            
            # Validate template exists - EXIT with error if invalid
            if template_name != 'argCmdDef' and not template_exists(template_name):
                printIt(f"ERROR: Template '{template_name}' not found.", lable.ERROR)
                list_templates()
                return
        
        # Combine regular arguments with option flags from cmd_options
        combined_args = list(args.arguments)
        
        for option_name, option_value in argParse.cmd_options.items():
            # Skip newCmd-specific options that aren't part of the command being created
            if option_name in ['template', 'templates']:
                continue
                
            if isinstance(option_value, bool):
                # Boolean flag (single hyphen) - add regardless of value for flag definition
                combined_args.append(f'-{option_name}')
            elif option_value == '__STRING_OPTION__' or not isinstance(option_value, bool):
                # String option (double hyphen) - either has a value or is marked as string option
                combined_args.append(f'--{option_name}')
        
        theArgs = verifyArgsWithDiscriptions(cmdObj, combined_args, template_name)
        newCommandCMDJson = updateCMDJson(cmdObj, theArgs)

        writeCodeFile(theArgs, newCommandCMDJson, template_name)
        
        # Save newCmd-specific options to .${packName}rc for the newCmd command itself
        if hasattr(argParse, 'cmd_options') and argParse.cmd_options:
            # Save newCmd-specific options like --template
            newcmd_flags = {}
            newcmd_switch_flags = {}
            for option_name, option_value in argParse.cmd_options.items():
                if option_name in ['template', 'templates']:
                    # Save template option for newCmd command
                    if option_name == 'template':
                        newcmd_flags['template'] = option_value
                        newcmd_switch_flags['template'] = {"type": "str"}
                    elif option_name == 'templates' and option_value not in ['__STRING_OPTION__', True]:
                        # --templates=value format, treat as template
                        newcmd_flags['template'] = option_value
                        newcmd_switch_flags['template'] = {"type": "str"}

            # Save newCmd-specific flags if any were found
            if newcmd_flags:
                saveCmdSwitchFlags('newCmd', newcmd_flags, newcmd_switch_flags)

            # Extract boolean flags for the new command being created
            new_cmd_flags = {}
            for option_name, option_value in argParse.cmd_options.items():
                # Skip newCmd-specific options
                if option_name in ['template', 'templates']:
                    continue
                # Only save boolean flags (single hyphen options) with default value False
                if isinstance(option_value, bool):
                    new_cmd_flags[option_name] = False  # Default to False for new command flags
            
            # Save the flags if any were found
            if new_cmd_flags:
                # Create switchFlags dict for the new command
                new_cmd_switch_flags = {}
                for flag_name in new_cmd_flags.keys():
                    new_cmd_switch_flags[flag_name] = {"type": "bool"}
                saveCmdSwitchFlags(newCmdName, new_cmd_flags, new_cmd_switch_flags)
        
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

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs, template_name: str = 'simple') -> dict:
    rtnDict = {}
    optionFlags = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
                                 
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        
        if argName.startswith('--'):
            # Double hyphen option (stores value)
            if len(argName) <= 2:
                printIt("Missing option name after double hyphen.", lable.WARN)
                exit(0)
            optionName = argName[2:]  # Remove --
            theDict = input(f'Enter help description for option {argName} (stores value):\\n')
            if theDict == '': 
                theDict = f'Value option {argName}'
            optionFlags[optionName] = {
                "description": theDict,
                "type": "str"
            }
        elif argName.startswith('-'):
            # Single hyphen option (boolean flag)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            theDict = input(f'Enter help description for flag {argName} (true/false):\\n')
            if theDict == '': 
                theDict = f'Boolean flag {argName}'
            optionFlags[optionName] = {
                "description": theDict,
                "type": "bool"
            }
        else:
            # Regular argument
            # Validate argument name if using argCmdDef template (creates functions)
            if template_name == 'argCmdDef' and argIndex > 0:  # Skip command name validation
                if not validate_argument_name(argName, cmdName):
                    printIt(f"Skipping invalid argument '{argName}' - cannot be used as function name", lable.WARN)
                    argIndex += 1
                    continue
            theDict = input(f'Enter help description for argument {argName}:\\n')
            if theDict == '': 
                theDict = f'no help for {argName}'
            rtnDict[argName] = theDict
        
        argIndex += 1
    
    # Store option flags separately for later processing
    rtnDict['_optionFlags'] = optionFlags
    return rtnDict

def writeCodeFile(theArgs: dict, newCommandCMDJson: dict, template_name: str = 'simple') -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs, newCommandCMDJson, template_name)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr

def cmdCodeBlock(theArgs: dict, newCommandCMDJson: dict, template_name: str = 'simple') -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]
                                 
    # Import the specified template
    try:
        template_module = __import__(f'${packName}.commands.templates.{template_name}', fromlist=['cmdDefTemplate', 'argDefTemplate'])
        cmdDefTemplate = template_module.cmdDefTemplate
        # Check if argDefTemplate exists, some templates may not need it
        argDefTemplate = getattr(template_module, 'argDefTemplate', None)
    except ImportError:
        printIt(f"Could not import template '{template_name}', using default", lable.WARN)
        from .templates.argCmdDef import cmdDefTemplate, argDefTemplate

    cmdCodeBlockJsonDict = {}
    cmdCodeBlockJsonDict[cmdName] = newCommandCMDJson
    commandJsonDictStr = 'commandJsonDict = ' + dumps(cmdCodeBlockJsonDict, indent=2)

    # Add regular arguments to the code block (skip _optionFlags)
    for argName in argNames:
        if argName != '_optionFlags':
            cmdCodeBlockJsonDict[argName] = theArgs[argName]
    
    rtnStr = cmdDefTemplate.substitute(
        packName=packName,
        defName=cmdName,
        commandJsonDict=commandJsonDictStr
    )
    
    argIndex = 1
    while argIndex < len(argNames): # add subarg functions
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry when generating argument functions
        if argName != '_optionFlags':
            # Only add argument functions if template has argDefTemplate
            if argDefTemplate is not None:
                rtnStr += argDefTemplate.substitute(argName=argName, defName=cmdName, packName=packName)
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
    optionFlags = theArgs.get('_optionFlags', {})
    newCommandCMDJson["switchFlags"] = optionFlags
    
    argIndex = 1
    while argIndex < len(theArgs): # add subarg functions
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry
        if argName != '_optionFlags':
            newCommandCMDJson[argName] = theArgs[argName]
        argIndex += 1
    commands[argNames[0]] = newCommandCMDJson
    cmdObj.commands = commands
    return newCommandCMDJson
"""
    )
)

modCmdTemplate = Template(
    dedent(
        """import os, copy, json, re
from ..defs.logIt import printIt, lable
from ..defs.validation import validate_argument_name, check_command_uses_argcmddef_template
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdSwitchFlags
from .commands import Commands
from .templates.argCmdDef import cmdDefTemplate, argDefTemplate
import readline
                   
${commandJsonDict}

readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

cmdObj = Commands()
commands = cmdObj.commands

def modCmd(argParse: ArgParse):
    args = argParse.args
    cmdObj = Commands()
    argsDict = args.arguments

    if len(argsDict) == 0:
        printIt("Command name required", lable.ERROR)
        return

    modCmdName = args.arguments[0]
    if modCmdName in cmdObj.commands.keys():
        # Combine regular arguments with option flags from cmd_options
        combined_args = list(args.arguments)

        # Add option flags to arguments for processing
        if hasattr(argParse, 'cmd_options') and argParse.cmd_options:
            for option_name, option_value in argParse.cmd_options.items():
                if isinstance(option_value, bool):
                    # Boolean flag (single hyphen) - add regardless of value for flag definition
                    combined_args.append(f'-{option_name}')
                elif option_value == '__STRING_OPTION__' or not isinstance(option_value, bool):
                    # String option (double hyphen) - either has a value or is marked as string option
                    combined_args.append(f'--{option_name}')

        # Check if command uses argCmdDef template for validation
        uses_argcmddef = check_command_uses_argcmddef_template(modCmdName)
        theArgs, tracking = verifyArgsWithDiscriptions(cmdObj, combined_args, uses_argcmddef)
        # Check if there are actual modifications (excluding _optionFlags)
        actual_modifications = {k: v for k, v in theArgs.items() if k != '_optionFlags'}
        if len(actual_modifications) > 0 or (theArgs.get('_optionFlags') and len(theArgs['_optionFlags']) > 0):
            updateCMDJson(cmdObj, modCmdName, theArgs)

            # If command uses argCmdDef template, add new argument functions to the .py file
            if uses_argcmddef:
                add_new_argument_functions(modCmdName, theArgs, tracking)

            # Save new option flags to .${packName}rc if any were added
            option_flags = theArgs.get('_optionFlags', {})
            if option_flags:
                # Extract flags for the command being modified
                new_cmd_flags = {}
                                 
                for option_name, flag_def in option_flags.items():
                    flag_type = flag_def.get('type', 'str')
                    if flag_type == 'bool':
                        # Boolean flag - save with default value False
                        new_cmd_flags[option_name] = False
                    elif flag_type == 'str':
                        # String option - save with empty string default
                        new_cmd_flags[option_name] = ""

                # Save the flags to .${packName}rc using the saveCmdSwitchFlags function
                if new_cmd_flags:
                    saveCmdSwitchFlags(modCmdName, new_cmd_flags, option_flags)

            # Print detailed modification results
            print_modification_results(modCmdName, tracking)
        else:
            # Check if anything was requested but all rejected
            if len(tracking['requested']) > 0:
                if len(tracking['rejected']) == len(tracking['requested']):
                    printIt(f'All requested modifications for "{modCmdName}" were rejected.', lable.WARN)
                else:
                    printIt(f'"{modCmdName}" unchanged.', lable.INFO)
            else:
                printIt(f'"{modCmdName}" unchanged.', lable.INFO)
    else:
        printIt(f'"{modCmdName}" does not exists. use newCmd or add it.',lable.INFO)
def print_modification_results(cmd_name: str, tracking: dict) -> None:
    \"\"\"Print detailed results of modification operations\"\"\"
    modified = tracking.get('modified', [])
    rejected = tracking.get('rejected', [])
    requested = tracking.get('requested', [])
    
    if len(modified) > 0:
        if len(modified) == 1:
            printIt(f'"{cmd_name}" - modified {modified[0]}.', lable.ModCmd)
        else:
            mod_list = ', '.join(modified)
            printIt(f'"{cmd_name}" - modified {mod_list}.', lable.ModCmd)
    
    # Only show rejection summary if some items were modified (mixed results)
    if len(rejected) > 0 and len(modified) > 0:
        if len(rejected) == 1:
            printIt(f'Note: {rejected[0]} was rejected.', lable.INFO)
        else:
            rej_list = ', '.join(rejected)
            printIt(f'Note: {rej_list} were rejected.', lable.INFO)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs, uses_argcmddef: bool = False) -> tuple[dict, dict]:
    rtnDict = {}
    optionFlags = {}
    cmdName = theArgs[0]
    
    # Track what was processed vs rejected
    tracking = {
        'modified': [],
        'rejected': [],
        'requested': []
    }
    
    # First pass: validate all arguments and separate them by type
    valid_args = []
    for argIndex in range(len(theArgs)):
        argName = theArgs[argIndex]
        
        # Track all requested items (skip command name)
        if argIndex > 0:
            tracking['requested'].append(argName)
            
            # Pre-validate regular arguments for argCmdDef template
            if not argName.startswith('-') and uses_argcmddef:
                if not validate_argument_name(argName, cmdName):
                    printIt(f"Skipping invalid argument '{argName}' - cannot be used as function name", lable.WARN)
                    tracking['rejected'].append(f'argument {argName}')
                    continue
            
            valid_args.append((argIndex, argName))
                                 
    # Special case: if only command name provided, handle command description modification
    if len(theArgs) == 1:
        cmdName = theArgs[0]
        chgDisc = input(f'Replace description for {cmdName} (y/N): ')
        if chgDisc.lower() == 'y':
            theDict = input(f'Enter help description for argument {cmdName}:\\n')
            if theDict == '': 
                theDict = f'no help for {cmdName}'
            rtnDict[cmdName] = theDict
            tracking['modified'].append(f'command {cmdName}')

    # Second pass: process only valid arguments with prompts
    for argIndex, argName in valid_args:
        saveDict = False
        
        if argName.startswith('--'):
            # Double hyphen option (stores value)
            if len(argName) <= 2:
                printIt("Missing option name after double hyphen.", lable.WARN)
                exit(0)
            optionName = argName[2:]  # Remove --
            theDict = input(f'Enter help description for option {argName} (stores value):\\n')
            if theDict == '': 
                theDict = f'Value option {argName}'
            optionFlags[optionName] = {
                "description": theDict,
                "type": "str"
            }
            tracking['modified'].append(f'option {argName}')
        elif argName.startswith('-'):
            # Single hyphen option (boolean flag)
            if len(argName) <= 1:
                printIt("Missing option name after single hyphen.", lable.WARN)
                exit(0)
            optionName = argName[1:]  # Remove -
            theDict = input(f'Enter help description for flag {argName} (true/false):\\n')
            if theDict == '': 
                theDict = f'Boolean flag {argName}'
            optionFlags[optionName] = {
                "description": theDict,
                "type": "bool"
            }
            tracking['modified'].append(f'flag {argName}')
        else:
            # Regular argument (not command description - that's handled above)
            theDict = ''
            saveDict = False
            
            if argName in cmdObj.commands[cmdName].keys():
                chgDisc = input(f'Replace description for {argName} (y/N): ')
                if chgDisc.lower() == 'y':
                    saveDict = True
            else: # add new arg
                saveDict = True
                newArg = True
                
            if saveDict:
                theDict = input(f'Enter help description for argument {argName}:\\n')
                if theDict == '': theDict = f'no help for {argName}'
                # only populate rtnDict with modified descriptions
                rtnDict[argName] = theDict
                tracking['modified'].append(f'argument {argName}')
            
        argIndex += 1
    
    # Store option flags separately for later processing
    rtnDict['_optionFlags'] = optionFlags
    return rtnDict, tracking

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

def add_new_argument_functions(cmdName: str, theArgs: dict, tracking: dict) -> None:
    \"\"\"Add new argument functions to the command's .py file if using argCmdDef template\"\"\"
    
    # Get list of newly added arguments (exclude command name, _optionFlags, and existing modifications)
    new_arguments = []
    modified_items = tracking.get('modified', [])
    
    for item in modified_items:
        if item.startswith('argument ') and not item.startswith('argument ' + cmdName):
            # Extract argument name from "argument argname" format
            arg_name = item.replace('argument ', '')
            # Only add if this is a new argument (not command description modification)
            if arg_name != cmdName and arg_name in theArgs and arg_name != '_optionFlags':
                new_arguments.append(arg_name)
    
    if not new_arguments:
        return
        
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{cmdName}.py')
    
    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return
    
    # Read the current file content
    with open(fileName, 'r') as fr:
        fileContent = fr.read()
    
    # Generate new function definitions using argDefTemplate
    new_functions = ""
    for argName in new_arguments:
        # Create function definition using the template
        argDescription = theArgs.get(argName, f'no help for {argName}')
        function_code = argDefTemplate.substitute(
            argName=argName,
            defName=cmdName,
            packName="${packName}"  # Use the package name
        )
        new_functions += function_code
    
    # Append new functions to the end of the file
    if new_functions:
        updated_content = fileContent + "\\n" + new_functions
        
        # Write the updated content back to the file
        with open(fileName, 'w') as fw:
            fw.write(updated_content)
        
        arg_list = ', '.join(new_arguments)
        printIt(f"Added function definitions for arguments: {arg_list}", lable.INFO)

def updateCMDJson(cmdObj: Commands, modCmdName: str, theArgs: dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    
    # Handle command description update if present
    if modCmdName in argNames:
        commands[modCmdName]['description'] = theArgs[modCmdName]
        argIndex = 1
    else: 
        argIndex = 0
    
    # Handle option flags if they exist
    optionFlags = theArgs.get('_optionFlags', {})
    if optionFlags:
        # Initialize switchFlags if it doesn't exist
        if 'switchFlags' not in commands[modCmdName]:
            commands[modCmdName]['switchFlags'] = {}
        # Add new option flags to the command's switchFlags
        commands[modCmdName]['switchFlags'].update(optionFlags)
    
    # Add regular arguments (skip _optionFlags)
    while argIndex < len(theArgs):
        argName = argNames[argIndex]
        # Skip the special _optionFlags entry
        if argName != '_optionFlags':
            commands[modCmdName][argName] = theArgs[argName]
        argIndex += 1
    
    cmdObj.commands = commands
    
    # Also update the source file's commandJsonDict
    updateSourceFileCommandJsonDict(modCmdName, commands[modCmdName])

def updateSourceFileCommandJsonDict(cmdName: str, cmdDict: dict) -> None:
    \"\"\"Update the commandJsonDict in the source file\"\"\"
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{cmdName}.py')

    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return

    # Read the current file content
    with open(fileName, 'r') as fr:
        fileContent = fr.read()

    # Create the new commandJsonDict string
    newCommandJsonDict = {cmdName: cmdDict}
    jsonStr = json.dumps(newCommandJsonDict, indent=2)

    # Pattern to match the existing commandJsonDict
    pattern = r'commandJsonDict\\s*=\\s*\\{[^}]*\\}'

    # Check if it's a simple dict or nested dict
    if '{' in fileContent and '}' in fileContent:
        # Look for the commandJsonDict pattern with proper nesting
        lines = fileContent.split('\\n')
        start_line = -1
        end_line = -1
        brace_count = 0
        in_dict = False

        for i, line in enumerate(lines):
            if 'commandJsonDict' in line and '=' in line and '{' in line:
                start_line = i
                in_dict = True
                brace_count = line.count('{') - line.count('}')
            elif in_dict:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    end_line = i
                    break

        if start_line != -1 and end_line != -1:
            # Replace the commandJsonDict section
            before_lines = lines[:start_line]
            after_lines = lines[end_line + 1:]

            new_lines = before_lines + [f'commandJsonDict = {jsonStr}'] + after_lines

            # Write the updated content back to the file
            with open(fileName, 'w') as fw:
                fw.write('\\n'.join(new_lines))

            printIt(f"Updated commandJsonDict in {fileName}", lable.INFO)
        else:
            printIt(
                f"Could not find commandJsonDict pattern in {fileName}", lable.WARN) 
"""
    )
)

rmCmdTemplate = Template(
    dedent(
        """import os, json
from ..defs.logIt import printIt, lable, cStr, color
from ..classes.optSwitches import removeCmdSwitchFlags
from .commands import Commands

${commandJsonDict}
                  
cmdObj = Commands()
commands = cmdObj.commands
theDir = os.path.dirname(os.path.realpath(__file__))
jsonFileName = os.path.join(theDir,'commands.json')

def rmCmd(argParse):
    # Reload commands to get current state
    cmdObj = Commands()
    commands = cmdObj.commands
    
    args = argParse.args
    theArgs = args.arguments
                                
    if len(theArgs) == 0:
        printIt("Command name required", lable.ERROR)
        return
        
    cmdName = theArgs[0]
    
    # If only one argument provided, remove the entire command
    if len(theArgs) == 1:
        if cmdName in commands:
            if cmdName in ["newCmd", "modCmd", "rmCmd"]:
                printIt(f'Permission denied for "{cmdName}".', lable.WARN)
                return
            chkRm: str = input(f"Permanently delete {cmdName} (y/N):\\n")
            if chkRm == '': chkRm = 'N'
            if chkRm[0].lower() == 'y':
                removeCmd(cmdName)
                printIt(cmdName, lable.RmCmd)
            else:
                printIt(f'Command "{cmdName}" not removed.', lable.INFO)
        else:
            printIt(f'"{cmdName}" is not currently a Command.', lable.WARN)
    else:
        # Multiple arguments - remove specific items from the command
        if cmdName not in commands:
            printIt(f'"{cmdName}" is not currently a Command.', lable.WARN)
            return
            
        for argIndex in range(1, len(theArgs)):
            anArg = theArgs[argIndex]
            
            # Check if anArg is a switch flag name (check if it exists in switchFlags)
            if 'switchFlags' in commands[cmdName] and anArg in commands[cmdName]['switchFlags']:
                # Handle switch flag removal by flag name (without -)
                chkRm: str = input(f"Permanently delete switch flag '-{anArg}' from {cmdName} (y/N):\\n")                               
                if chkRm == '': chkRm = 'N'
                if chkRm[0].lower() == 'y':
                    removeCmdSwitchFlag(cmdName, anArg)
                    printIt(f'Switch flag "-{anArg}" removed from command "{cmdName}"', lable.RmArg)
                else:
                    printIt(f'Switch flag "-{anArg}" not removed from command "{cmdName}"', lable.INFO)
            # Check if anArg is a switch flag (starts with -) - legacy support
            elif anArg.startswith('-'):
                # Handle switch flag removal with dash prefix
                flagName = anArg.lstrip('-')  # Remove - or -- prefix
                if 'switchFlags' in commands[cmdName] and flagName in commands[cmdName]['switchFlags']:
                    chkRm: str = input(f"Permanently delete switch flag {anArg} from {cmdName} (y/N):\\n")
                    if chkRm == '': chkRm = 'N'
                    if chkRm[0].lower() == 'y':
                        removeCmdSwitchFlag(cmdName, flagName)
                        printIt(f'Switch flag "{anArg}" removed from command "{cmdName}"', lable.RmArg)
                    else:
                        printIt(f'Switch flag "{anArg}" not removed from command "{cmdName}"', lable.INFO)
                else:
                    printIt(f'Switch flag "{anArg}" is not defined for command "{cmdName}"', lable.WARN)
            elif anArg in commands[cmdName]:
                chkRm: str = input(f"Permanently delete argument {anArg} (y/N):\\n")
                if chkRm == '': chkRm = 'N'
                if chkRm[0].lower() == 'y':
                    removeCmdArg(cmdName, anArg)
                    printIt(anArg, lable.RmArg)
                else:
                    printIt(f'Argument "{anArg}" not removed from command "{cmdName}".', lable.INFO)
            else:
                printIt(f'"{anArg}" is not an argument or switch flag for command "{cmdName}".', lable.WARN)

def removeCmdArg(cmdName, argName):
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        del theJson[cmdName][argName]
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)

    # Remove the function from the source file
    removeFunctionFromSourceFile(cmdName, argName)
    
    # Update source file's commandJsonDict
    updateSourceFileAfterRemoval(cmdName, theJson[cmdName])

def removeCmdSwitchFlag(cmdName, flagName):
    \"\"\"Remove a switch flag from commands.json, .${packName}rc, and source file\"\"\"
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        if 'switchFlags' in theJson[cmdName] and flagName in theJson[cmdName]['switchFlags']:
            del theJson[cmdName]['switchFlags'][flagName]
            # If switchFlags becomes empty, we can leave it empty
            if not theJson[cmdName]['switchFlags']:
                theJson[cmdName]['switchFlags'] = {}
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)
    
    # Remove flag from .${packName}rc file
    ${packName}rc_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(jsonFileName))), '.${packName}rc')
    
    if os.path.exists(${packName}rc_file):
        try:
            with open(${packName}rc_file, 'r') as pf:
                ${packName}rc_data = json.load(pf)
            
            # Remove the flag from commandFlags if it exists
            if ('commandFlags' in ${packName}rc_data and 
                cmdName in ${packName}rc_data['commandFlags'] and 
                flagName in ${packName}rc_data['commandFlags'][cmdName]):
                
                del ${packName}rc_data['commandFlags'][cmdName][flagName]
                
                # If command has no more flags, remove the command entry
                if not ${packName}rc_data['commandFlags'][cmdName]:
                    del ${packName}rc_data['commandFlags'][cmdName]
                
                with open(${packName}rc_file, 'w') as pf:
                    json.dump(${packName}rc_data, pf, indent=2)
                
                printIt(f"Removed flag '{flagName}' from .${packName}rc", lable.INFO)
                
        except (json.JSONDecodeError, KeyError) as e:
            printIt(f"Warning: Could not update .${packName}rc file: {e}", lable.WARN)
    
    # Update source file's commandJsonDict
    updateSourceFileAfterRemoval(cmdName, theJson[cmdName])

def updateSourceFileAfterRemoval(cmdName: str, cmdDict: dict) -> None:
    \"\"\"Update the commandJsonDict in the source file after removing an argument or switch flag\"\"\"
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{cmdName}.py')
    
    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return
    
    # Read the current file content
    with open(fileName, 'r') as fr:
        fileContent = fr.read()
    
    # Create the new commandJsonDict string
    newCommandJsonDict = {cmdName: cmdDict}
    jsonStr = json.dumps(newCommandJsonDict, indent=2)
    
    # Look for the commandJsonDict pattern with proper nesting
    lines = fileContent.split('\\n')
    start_line = -1
    end_line = -1
    brace_count = 0
    in_dict = False
    
    for i, line in enumerate(lines):
        if 'commandJsonDict' in line and '=' in line and '{' in line:
            start_line = i
            in_dict = True
            brace_count = line.count('{') - line.count('}')
        elif in_dict:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                end_line = i
                break
    
    if start_line != -1 and end_line != -1:
        # Replace the commandJsonDict section
        before_lines = lines[:start_line]
        after_lines = lines[end_line + 1:]
        
        new_lines = before_lines + [f'commandJsonDict = {jsonStr}'] + after_lines
        
        # Write the updated content back to the file
        with open(fileName, 'w') as fw:
            fw.write('\\n'.join(new_lines))
        
        printIt(f"Updated commandJsonDict in {fileName}", lable.INFO)
    else:
        printIt(f"Could not find commandJsonDict pattern in {fileName}", lable.WARN)
                                
def removeFunctionFromSourceFile(cmdName: str, argName: str) -> None:
    \"\"\"Remove a function definition from the source file\"\"\"
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{cmdName}.py')

    if not os.path.isfile(fileName):
        printIt(f"Source file {fileName} not found", lable.WARN)
        return

    # Read the current file content
    with open(fileName, 'r') as fr:
        fileContent = fr.read()

    lines = fileContent.split('\\n')
    
    # Find the function definition and its end
    function_start = -1
    function_end = -1
    indent_level = 0
    
    for i, line in enumerate(lines):
        # Look for the function definition
        if line.strip().startswith(f'def {argName}('):
            function_start = i
            # Find the indentation level of this function
            indent_level = len(line) - len(line.lstrip())
            continue
        
        # If we're inside a function, look for the end
        if function_start != -1 and i > function_start:
            # If we hit a non-empty line that's at the same or lesser indent level as the function,
            # or another function definition, we've found the end
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and not line.strip().startswith('#'):
                    function_end = i - 1  # Previous line was the end
                    break
            # If we reach the end of file
            elif i == len(lines) - 1:
                function_end = i
                break

    # If function was found, remove it
    if function_start != -1:
        if function_end == -1:
            function_end = len(lines) - 1  # Function goes to end of file
        
        # Remove the function lines (including any trailing empty lines that belong to it)
        # Also remove leading empty lines before the function if they exist
        start_remove = function_start
        end_remove = function_end
        
        # Look backwards for empty lines to remove before function
        while start_remove > 0 and not lines[start_remove - 1].strip():
            start_remove -= 1
            
        # Look forwards for empty lines to remove after function  
        while end_remove < len(lines) - 1 and not lines[end_remove + 1].strip():
            end_remove += 1

        # Create new content without the function
        new_lines = lines[:start_remove] + lines[end_remove + 1:]
        
        # Write the updated content back to the file
        with open(fileName, 'w') as fw:
            fw.write('\\n'.join(new_lines))
        
        printIt(f"Removed function '{argName}' from {fileName}", lable.INFO)
    else:
        printIt(f"Function '{argName}' not found in {fileName}", lable.WARN)

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

    # Remove command flags from .${packName}rc
    removeCmdSwitchFlags(cmdName)
"""
    )
)

runTestTemplate = Template(
    dedent(
        """# Generated using argCmdDef template
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

commandJsonDict = {
  "runTest": {
    "description": "Run test(s) in ./tests directory. Use 'listTests' to see available tests.",
    "switchFlags": {
      "verbose": {
        "description": "Verbose output flag",
        "type": "bool"
      },
      "stop": {
        "description": "Stop on failure flag",
        "type": "bool"
      },
      "summary": {
        "description": "Summary only flag",
        "type": "bool"
      }
    },
    "testName": "Optional name of specific test to run (without .py extension)",
    "listTests": "List all available tests in the tests directory"
  }
}

cmdObj = Commands()
commands = cmdObj.commands

class TestRunner:
    \"\"\"Class to handle test discovery and execution\"\"\"

    def __init__(self, verbose: bool = False, stop_on_failure: bool = False, summary_only: bool = False):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.verbose = verbose
        self.stop_on_failure = stop_on_failure
        self.summary_only = summary_only
        self.results: Dict[str, Tuple[bool, str, float]] = {}

    def discover_tests(self) -> List[Path]:
        \"\"\"Discover all test files in the tests directory\"\"\"
        if not self.tests_dir.exists():
            printIt(
                f"Tests directory not found: {self.tests_dir}", lable.ERROR)
            return []

        test_files = []
        for file_path in self.tests_dir.glob("test_*.py"):
            if file_path.is_file():
                test_files.append(file_path)

        return sorted(test_files)

    def run_single_test(self, test_file: Path) -> Tuple[bool, str, float]:
        \"\"\"Run a single test file and return (success, output, duration)\"\"\"
        start_time = time.time()

        try:
            # Change to project directory and activate virtual environment
            cmd = f"cd {self.project_root} && source env/${packName}/bin/activate && python {test_file}"

            if not self.summary_only and self.verbose:
                printIt(f"Running: {cmd}", lable.DEBUG)

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Combine stdout and stderr for complete output
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\\nSTDERR:\\n{result.stderr}"

            return success, output, duration

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Exception running test: {str(e)}", duration

    def run_all_tests(self, test_files: List[Path]) -> Dict[str, Tuple[bool, str, float]]:
        \"\"\"Run all discovered test files\"\"\"
        results = {}

        printIt(f"Running {len(test_files)} test(s)...", lable.INFO)
        print()

        for i, test_file in enumerate(test_files, 1):
            test_name = test_file.stem

            if not self.summary_only:
                printIt(
                    f"[{i}/{len(test_files)}] Running {test_name}...", lable.INFO)

            success, output, duration = self.run_single_test(test_file)
            results[test_name] = (success, output, duration)

            # Show individual test results if not summary only
            if not self.summary_only:
                if success:
                    status = cStr("PASS", color.GREEN)
                else:
                    status = cStr("FAIL", color.RED)
                print(f"  {status} ({duration:.2f}s)")

                if self.verbose or not success:
                    # Show output for failed tests or when verbose is enabled
                    if output.strip():
                        print("  " + "\\n  ".join(output.strip().split('\\n')))
                print()

            # Stop on first failure if requested
            if not success and self.stop_on_failure:
                printIt(
                    f"Stopping due to test failure in {test_name}", lable.WARN)
                break

        return results

    def print_summary(self, results: Dict[str, Tuple[bool, str, float]]):
        \"\"\"Print test execution summary\"\"\"
        total_tests = len(results)
        passed_tests = sum(1 for success, _, _ in results.values() if success)
        failed_tests = total_tests - passed_tests
        total_time = sum(duration for _, _, duration in results.values())

        print("=" * 60)
        printIt("TEST EXECUTION SUMMARY", lable.INFO)
        print("=" * 60)

        print(f"Total Tests:  {total_tests}")
        print(f"{cStr('Passed:', color.GREEN)}       {passed_tests}")
        print(f"{cStr('Failed:', color.RED)}       {failed_tests}")
        print(f"Total Time:   {total_time:.2f}s")

        if failed_tests > 0:
            print(f"\\n{cStr('Failed Tests:', color.RED)}")
            for test_name, (success, output, duration) in results.items():
                if not success:
                    print(f"  • {test_name} ({duration:.2f}s)")
                    if self.verbose and output.strip():
                        # Show first few lines of error output
                        lines = output.strip().split('\\n')
                        for line in lines[:5]:  # Show first 5 lines
                            print(f"    {line}")
                        if len(lines) > 5:
                            print(f"    ... ({len(lines) - 5} more lines)")

        print("=" * 60)

        if failed_tests == 0:
            printIt("🎉 All tests passed!", lable.PASS)
        else:
            printIt(f"❌ {failed_tests} test(s) failed", lable.ERROR)

def runTest(argParse):
    \"\"\"Main runTest function - entry point for the command\"\"\"
    args = argParse.args
    # Filter out flag arguments (starting with + or -)
    theArgs = [arg for arg in args.arguments if not (
        isinstance(arg, str) and len(arg) > 1 and arg[0] in '+-')]

    # Get command-line flags from .${packName}rc file after flag processing
    from ..classes.optSwitches import getCmdSwitchFlags
    cmd_flags = getCmdSwitchFlags('runTest')
    verbose = cmd_flags.get('verbose', False)
    stop_on_failure = cmd_flags.get('stop', False)
    summary_only = cmd_flags.get('summary', False)

    runner = TestRunner(
        verbose=verbose, stop_on_failure=stop_on_failure, summary_only=summary_only)

    if len(theArgs) == 0:
        # Run all tests
        test_files = runner.discover_tests()
        if not test_files:
            printIt("No test files found in ./tests directory", lable.WARN)
            return

        results = runner.run_all_tests(test_files)
        runner.print_summary(results)

        # Exit with error code if any tests failed
        failed_count = sum(
            1 for success, _, _ in results.values() if not success)
        if failed_count > 0:
            sys.exit(1)

    elif len(theArgs) == 1:
        # Check if it's the listTests argument
        if theArgs[0] == "listTests":
            listTests(argParse)
            return

        # Run specific test
        test_name = theArgs[0]
        if not test_name.endswith('.py'):
            test_name += '.py'

        test_file = runner.tests_dir / test_name
        if not test_file.exists():
            printIt(f"Test file not found: {test_name}", lable.ERROR)
            printIt("Use '${packName} runTest listTests' to see available tests", lable.INFO)
            return

        printIt(f"Running specific test: {test_name}", lable.INFO)
        success, output, duration = runner.run_single_test(test_file)

        if success:
            status = cStr("PASSED", color.GREEN)
        else:
            status = cStr("FAILED", color.RED)
        print(f"Test {status} ({duration:.2f}s)")

        if output.strip() and (verbose or not success):
            print(output)

        if not success:
            sys.exit(1)
    else:
        printIt(
            "Too many arguments. Usage: ${packName} runTest [testName] or ${packName} runTest listTests", lable.ERROR)

def listTests(argParse):
    \"\"\"List all available tests in the tests directory\"\"\"
    runner = TestRunner()
    test_files = runner.discover_tests()

    if not test_files:
        printIt("No test files found in ./tests directory", lable.WARN)
        return

    printIt(f"Available tests in {runner.tests_dir}:", lable.INFO)
    print()

    for i, test_file in enumerate(test_files, 1):
        test_name = test_file.stem

        # Try to get test description from file
        description = "No description available"
        try:
            with open(test_file, 'r') as f:
                lines = f.readlines()
                # Look for docstring in first few lines
                for line in lines[:10]:
                    if '\"\"\"' in line and line.strip() != '\"\"\"':
                        description = line.strip().replace('\"\"\"', '').strip()
                        break
        except Exception:
            pass

        print(f"{i:2d}. {cStr(test_name, color.CYAN)}")
        print(f"    {description}")
        print(f"    File: {test_file.name}")
        print()

    print(f"Usage:")
    print(f"  ${packName} runTest                       # Run all tests")
    print(f"  ${packName} runTest {test_files[0].stem}  # Run specific test")
    print(f"  ${packName} runTest -verbose              # Run all tests with verbose output")
    print(f"  ${packName} runTest -stop                 # Stop on first failure")
    print(f"  ${packName} runTest -summary              # Show only summary")
"""
    )
)

fileDiffTemplate = Template(
    dedent(
        """import sys
import os
import difflib
from difflib import unified_diff
from pathlib import Path
from ${packName}.defs.logIt import printIt, lable, cStr, color

import black
from black import FileMode
from black.report import NothingChanged

commandJsonDict = {
    "fileDiff": {
    "description": "Show the differnces between two files.",
    "origFile": "Original file name",
    "newFile": "New file name"
}
}

def fileDiff(argParse):
    global commands
    args = argParse.args
    theArgs = args.arguments
    if len(theArgs) == 2:
        origFileName: str = theArgs[0]
        newFileName: str = theArgs[1]
        compare_python_files(origFileName, newFileName)

def compare_python_files(origFileName: str, newFileName: str, chkBlack = False) -> bool:
    \"\"\"
    Compares two Python files and prints their differences.
    Return True if no differenc found or error occred.

    Args:
        origFileName (str): The path to the first Python file (e.g., the original).
        newFileName (str): The path to the second Python file (e.g., the modified).
    \"\"\"
    rtnBool = False
    # 1. Validate file paths
    if not os.path.exists(origFileName):
        print(f"Error: File not found at '{origFileName}'", file=sys.stderr)
        return rtnBool
    if not os.path.exists(newFileName):
        print(f"Error: File not found at '{newFileName}'", file=sys.stderr)
        return rtnBool
    if not os.path.isfile(origFileName):
        print(f"Error: '{origFileName}' is not a file.", file=sys.stderr)
        return rtnBool
    if not os.path.isfile(newFileName):
        print(f"Error: '{newFileName}' is not a file.", file=sys.stderr)
        return rtnBool

    # 2. Read file contents as lists of lines
    try:
        with open(origFileName, 'r', encoding='utf-8') as f1:
            lines1 = f1.readlines()
        with open(newFileName, 'r', encoding='utf-8') as f2:
            lines2 = f2.readlines()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return rtnBool
    except UnicodeDecodeError:
        print(f"Error: Could not decode file with UTF-8. Try a different encoding if known.", file=sys.stderr)
        return rtnBool

    # 3. Generate differences using difflib.unified_diff
    # unified_diff produces a diff in the unified format, like 'diff -u'
    # 'lineterm=' is important if readlines() keeps newlines, to avoid double spacing in output.
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile=origFileName,
        tofile=newFileName
    )
        #lineterm=''  # Ensures difflib doesn't add an extra newline if lines already have them
    
    # Convert diff generator to list to check if it has content
    diff_lines = list(diff)
    
    # 4. check if black foprmatting removes diff
    if chkBlack:
        # print('------------ chkBlack')
        diff_result = compare_black_diff(origFileName, newFileName)
        if diff_result:
            diff_lines = diff_result.splitlines(keepends=True)
        else:
            diff_lines = []

    if diff_lines:
        # 5. Print the differences with optional color coding
        print("\\n--- Differences ---")
        for line in diff_lines:
            # ANSI escape codes for coloring output in terminals
            if line.startswith('+'):
                print(f"\\033[92m{line}\\033[0m", end='')  # Green for added lines
            elif line.startswith('-'):
                print(f"\\033[91m{line}\\033[0m", end='')  # Red for removed lines
            elif line.startswith('@'):
                print(f"\\033[94m{line}\\033[0m", end='')  # Blue for hunk headers
            else:
                print(line, end='')  # Default color for context lines
        print("\\n" + "=" * 60 + "\\n")
        rtnBool = False  # Differences found
    else:
        print(f"No differences found between {origFileName} and {newFileName}.")
        rtnBool = True  # No differences found
    return rtnBool

def compare_black_diff(origFileName, newFileName):
    \"\"\"
    Returns the diff of a Python file after black formatting, as a string.
    Returns None if no changes are needed.
    \"\"\"
    orig_file_path = Path(origFileName)
    new_file_path = Path(newFileName)
    try:
        # Read the original content
        orig_code = orig_file_path.read_text(encoding="utf-8")

        # Format the code using Black
        orig_formatted_code = black.format_file_contents(
            orig_code, fast=True, mode=FileMode(line_length=88)
        )

        # Read the new content
        new_code = new_file_path.read_text(encoding="utf-8")

        # Format the code using Black
        new_formatted_code = black.format_file_contents(
            new_code, fast=True, mode=FileMode(line_length=88)
        )

        # Split the original and formatted code into lines
        original_lines = orig_formatted_code.splitlines(keepends=True)
        new_lines = new_formatted_code.splitlines(keepends=True)

        # Generate the unified diff
        diff = unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{origFileName}",
            tofile=f"b/{newFileName}"
        )
        if not diff:
            new_file_path.write_text(new_formatted_code, encoding="utf-8")
        return "".join(diff)

    except NothingChanged:
        return None
    except Exception as e:
        print(f"Error processing {new_file_path}: {e}")
        return None"""
    )
)

syncTemplate = Template(
    dedent(
        """# Generated using classCall template
\"\"\"
${packName} sync command - Synchronize files generated from templates

This command synchronizes modifications made to files that were generated from template files.
It handles different file types (.md, .json, .py) differently and uses genTempSyncData.json
to track template sources, checksums, and field substitutions.
\"\"\"

import os, sys
import json
import hashlib
import re
import copy
from string import Template
from textwrap import dedent
from typing import Dict, Any, List, Optional, Union, Tuple

from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

commandJsonDict = {
    "sync": {
        "description": "Sync modified files to originating template file",
        "switchFlags": {
            "dry-run": {
                "description": "Show what would be synced without making changes",
                "type": "bool"
            },
            "force": {
                "description": "Force sync even if files appear to have user modifications",
                "type": "bool"
            },
            "backup": {
                "description": "Create backup files before syncing",
                "type": "bool"
            }
        },
        "filePattern": "Optional file patterns to sync (e.g., '*.py', 'commands/*')",
        "action": "Action to perform: 'sync' (default), 'list', 'status', 'make', 'rmTemp'"
    }
}


class TemplateSyncer:
    \"\"\"Handles synchronization of template-generated files by creating new template files\"\"\"

    def __init__(self, project_root: str, dry_run: bool = False, force: bool = False, backup: bool = False):
        # Use current working directory as project root
        self.project_root = os.getcwd()
        self.sync_data_file = os.path.join(self.project_root, 'genTempSyncData.json')
        self.new_templates_dir = os.path.join(self.project_root, 'newTemplates')
        self.sync_data = {}
        self.dry_run = dry_run
        self.force = force
        self.backup = backup

        # Load the sync data file
        self._load_sync_data()

    def _load_sync_data(self):
        \"\"\"Load the synchronization data from JSON file in current working directory\"\"\"
        if not os.path.exists(self.sync_data_file):
            printIt(
                f"genTempSyncData.json not found in current directory: {self.project_root}", lable.ERROR)
            printIt(
                "Please run this command from a project directory containing genTempSyncData.json", lable.INFO)
            return

        try:
            with open(self.sync_data_file, 'r', encoding='utf-8') as f:
                self.sync_data = json.load(f)
            
            # Clean up entries for files that no longer exist
            initial_count = len([k for k in self.sync_data.keys() if k != 'fields'])
            self._cleanup_missing_files()
            final_count = len([k for k in self.sync_data.keys() if k != 'fields'])
            
            if initial_count > final_count:
                printIt(f"Cleaned up {initial_count - final_count} entries for missing files", lable.INFO)
                # Save the cleaned data immediately
                self._save_sync_data()
            
            printIt(
                f"Loaded sync data from: {os.path.relpath(self.sync_data_file, self.project_root)}", lable.INFO)
            printIt(
                f"Tracking {final_count} files", lable.INFO)
        except Exception as e:
            printIt(f"Error loading sync data: {e}", lable.ERROR)
            self.sync_data = {}

    def _save_sync_data(self):
        \"\"\"Save the synchronization data back to JSON file\"\"\"
        if self.dry_run:
            printIt("Dry run: Would save sync data", lable.INFO)
            return

        try:
            with open(self.sync_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_data, f, indent=4, ensure_ascii=False)
            printIt("Sync data updated", lable.SAVED)
        except Exception as e:
            printIt(f"Error saving sync data: {e}", lable.ERROR)

    def _cleanup_missing_files(self):
        \"\"\"Remove entries for files that no longer exist on the filesystem\"\"\"
        missing_files = []
        
        # Check each tracked file (skip 'fields' entry)
        for file_path in list(self.sync_data.keys()):
            if file_path == 'fields':
                continue
                
            # Check if file exists
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                
        # Remove entries for missing files
        for file_path in missing_files:
            del self.sync_data[file_path]
            printIt(f"Removed missing file from tracking: {os.path.relpath(file_path, self.project_root)}", lable.WARN)

    def _calculate_md5(self, file_path: str) -> str:
        \"\"\"Calculate MD5 hash of a file\"\"\"
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            printIt(f"Error calculating MD5 for {file_path}: {e}", lable.ERROR)
            return ""

    def _escape_string_for_template(self, text: str) -> str:
        \"\"\"Escape special characters in strings for Python template generation\"\"\"
        # For multi-line strings in triple quotes, we need to escape backslashes and triple quotes
        escaped = text.replace('\\\\', '\\\\\\\\')  # Escape backslashes first
        escaped = escaped.replace(
            '\"\"\"', '\\\\"\\\\"\\\\"')  # Escape triple quotes to \\"\\"\\"
        return escaped

    def _escape_string_for_json(self, text: str) -> str:
        \"\"\"Escape special characters for JSON template generation\"\"\"
        escaped = text.replace('\\\\', '\\\\\\\\')  # Escape backslashes first
        escaped = escaped.replace('"', '\\\\"')  # Escape double quotes
        return escaped

    def _convert_literals_to_placeholders(self, content: str) -> str:
        \"\"\"Convert literal field values in content to template placeholders\"\"\"
        if 'fields' not in self.sync_data:
            return content
        
        fields = self.sync_data['fields']
        modified_content = content
        
        # Create mapping of field names to placeholder names, ordered by specificity
        # (more specific patterns first to avoid partial replacements)
        field_mappings = [
            ('authorsEmail', 'authorsEmail'),
            ('maintainersEmail', 'maintainersEmail'),
            ('name', 'packName'),
            ('version', 'version'), 
            ('description', 'description'),
            ('readme', 'readme'),
            ('license', 'license'),
            ('authors', 'authors'),
            ('maintainers', 'maintainers'),
            ('classifiers', 'classifiers')
        ]
        
        # Replace literal values with placeholders
        for field_key, placeholder_name in field_mappings:
            if field_key in fields and fields[field_key]:
                field_value = str(fields[field_key])
                if field_value and field_value.strip():  # Only replace non-empty values
                    placeholder = '${' + placeholder_name + '}'
                    # Special handling for 'name' field (packName) which appears in compound words
                    if field_key == 'name':
                        # Handle compound patterns like "${packName}rc", "syncTemplates", etc.
                        compound_patterns = [
                            (f'{field_value}rc', f'${{{placeholder_name}}}rc'),
                            (f'{field_value}Templates', f'${{{placeholder_name}}}Templates'),
                            (f'.{field_value}rc', f'.${{{placeholder_name}}}rc'),
                        ]
                        for compound_pattern, compound_replacement in compound_patterns:
                            modified_content = modified_content.replace(compound_pattern, compound_replacement)
                        
                        # Also handle standalone occurrences with word boundaries
                        pattern = r'\\b' + re.escape(field_value) + r'\\b'
                        modified_content = re.sub(pattern, placeholder, modified_content)
                    else:
                        # Use word boundaries for other fields to avoid partial replacements
                        pattern = r'\\b' + re.escape(field_value) + r'\\b'
                        modified_content = re.sub(pattern, placeholder, modified_content)
        
        return modified_content

    def _load_template_content(self, template_file: str, template_name: str) -> Optional[str]:
        \"\"\"Load template content from template file\"\"\"
        # Use the new templates directory copy instead of the original path
        template_file_name = os.path.basename(template_file)
        local_template_path = os.path.join(
            self.new_templates_dir, template_file_name)

        if not os.path.exists(local_template_path):
            printIt(
                f"Template file not found: {local_template_path}", lable.ERROR)
            return None

        try:
            with open(local_template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the template content to find the specific template
            template_content = self._extract_template_from_file(
                content, template_name)
            return template_content

        except Exception as e:
            printIt(
                f"Error loading template {template_name} from {local_template_path}: {e}", lable.ERROR)
            return None

    def _extract_template_from_file(self, file_content: str, template_name: str) -> Optional[str]:
        \"\"\"Extract specific template from a template file\"\"\"
        # Look for different template patterns

        # Pattern 1: dedent(\"\"\"...\"\"\") assignments
        dedent_pattern = rf'^{re.escape(template_name)}\\s*=\\s*dedent\\(\"\"\"(.*?)\"\"\"\\)'
        match = re.search(dedent_pattern, file_content,
                          re.DOTALL | re.MULTILINE)
        if match:
            return match.group(1)

        # Pattern 2: Template(dedent(\"\"\"...\"\"\")) assignments
        template_pattern = rf'^{re.escape(template_name)}\\s*=\\s*Template\\(dedent\\(\"\"\"(.*?)\"\"\"\\)\\)'
        match = re.search(template_pattern, file_content,
                          re.DOTALL | re.MULTILINE)
        if match:
            return match.group(1)

        # Pattern 3: JSON dictionary assignments
        json_pattern = rf'^{re.escape(template_name)}\\s*=\\s*(\\{{.*?\\}})'
        match = re.search(json_pattern, file_content, re.DOTALL | re.MULTILINE)
        if match:
            try:
                # Try to parse as JSON and return formatted version
                # Using eval for Python dict syntax
                json_data = eval(match.group(1))
                return json.dumps(json_data, indent=2, ensure_ascii=False)
            except:
                return match.group(1)

        printIt(f"Template '{template_name}' not found in file", lable.WARN)
        return None

    def _substitute_template_fields(self, template_content: str, fields: Dict[str, Any]) -> str:
        \"\"\"Substitute field placeholders in template content\"\"\"
        try:
            # Use string.Template for safe substitution
            template = Template(template_content)
            return template.safe_substitute(fields)
        except Exception as e:
            printIt(f"Error substituting template fields: {e}", lable.WARN)
            return template_content

    def _extract_command_json_dict(self, file_path: str) -> Optional[str]:
        \"\"\"Extract commandJsonDict from a source file\"\"\"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Look for commandJsonDict = { ... } with proper brace matching
            lines = file_content.split('\\n')
            start_line = -1
            end_line = -1
            brace_count = 0
            in_dict = False
            
            for i, line in enumerate(lines):
                if 'commandJsonDict' in line and '=' in line and '{' in line:
                    start_line = i
                    in_dict = True
                    brace_count = line.count('{') - line.count('}')
                elif in_dict:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0:
                        end_line = i
                        break
            
            if start_line != -1 and end_line != -1:
                # Extract the dictionary content
                dict_lines = lines[start_line:end_line + 1]
                dict_content = '\\n'.join(dict_lines)
                
                # Remove the variable assignment part to get just the dictionary
                dict_content = dict_content.split('=', 1)[1].strip()
                
                try:
                    # Use eval to parse Python dict syntax
                    json_data = eval(dict_content)
                    return json.dumps(json_data, indent=2, ensure_ascii=False)
                except Exception as e:
                    printIt(f"Error parsing commandJsonDict from {file_path}: {e}", lable.WARN)
                    return None
            
            return None
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.WARN)
            return None

    def _build_complete_commands_json_dict(self) -> str:
        \"\"\"Build complete commandsJsonDict from all command files in the sync data\"\"\"
        commands_dict = {
            "switchFlags": {},
            "description": "Dictionary of commands, their discription and switches, and their argument discriptions.",
            "_globalSwitcheFlags": {}
        }
        
        # Collect command JSONs from all command files
        commands_dir = os.path.join(self.project_root, 'src', '${packName}', 'commands')
        
        for file_path, file_info in self.sync_data.items():
            if file_path == 'fields':  # Skip the fields section
                continue
                
            if not isinstance(file_info, dict):
                continue
                
            # Check if this is a command file
            file_dir = os.path.dirname(os.path.abspath(file_path))
            if file_dir.startswith(commands_dir) and file_path.endswith('.py'):
                # Extract command JSON from this file
                command_json_dict = self._extract_command_json_dict(file_path)
                if command_json_dict:
                    try:
                        cmd_data = json.loads(command_json_dict)
                        # Merge command data into the main dict
                        commands_dict.update(cmd_data)
                    except Exception as e:
                        printIt(f"Error parsing command JSON from {file_path}: {e}", lable.WARN)
        
        return json.dumps(commands_dict, indent=2, ensure_ascii=False)

    def _create_backup(self, file_path: str) -> bool:
        \"\"\"Create a backup of the file\"\"\"
        if not self.backup:
            return True

        try:
            backup_path = file_path + '.backup'
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            printIt(
                f"Created backup: {os.path.basename(backup_path)}", lable.INFO)
            return True
        except Exception as e:
            printIt(f"Error creating backup for {file_path}: {e}", lable.ERROR)
            return False

    def _sync_file(self, file_path: str, file_info: Dict[str, Any]) -> bool:
        \"\"\"Generate new template for a modified file\"\"\"
        if not os.path.exists(file_path):
            printIt(
                f"File not found: {os.path.relpath(file_path, self.project_root)}", lable.WARN)
            return False

        # Calculate current MD5
        current_md5 = self._calculate_md5(file_path)
        stored_md5 = file_info.get('fileMD5', '')

        if current_md5 == stored_md5:
            printIt(
                f"File unchanged: {os.path.relpath(file_path, self.project_root)}", lable.INFO)
            return True

        printIt(
            f"File modified: {os.path.relpath(file_path, self.project_root)}", lable.WARN)

        # Get template info
        template_name = file_info.get('template', '')
        template_file = file_info.get('tempFileName', '')

        if not template_name or not template_file:
            printIt(f"Missing template info for {file_path}", lable.ERROR)
            return False

        # Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        # Handle different file types
        file_ext = os.path.splitext(file_path)[1].lower()

        if self.dry_run:
            printIt(
                f"Dry run: Would generate new template for {os.path.relpath(file_path, self.project_root)}", lable.INFO)
            return True

        if file_ext == '.json':
            success = self._generate_json_template(
                file_path, current_content, template_name, template_file)
        elif file_ext == '.md':
            success = self._generate_markdown_template(
                file_path, current_content, template_name, template_file)
        elif file_ext == '.py':
            success = self._generate_python_template(
                file_path, current_content, template_name, template_file)
        else:
            success = self._generate_generic_template(
                file_path, current_content, template_name, template_file)

        if success:
            # Update stored MD5 to reflect that we've synced this version
            self.sync_data[file_path]['fileMD5'] = current_md5

        return success

    def _generate_json_template(self, file_path: str, current_content: str, template_name: str, template_file: str) -> bool:
        \"\"\"Generate new JSON template from modified file\"\"\"
        printIt(f"Generating JSON template: {template_name}", lable.INFO)

        try:
            # Parse current JSON content
            current_json = json.loads(current_content)

            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(
                self.new_templates_dir, template_file_name)

            # Generate Python code for the JSON template
            json_str = json.dumps(current_json, indent=2, ensure_ascii=False)

            # Convert JSON string to Python dict format for embedding in Python file
            template_code = f"{template_name} = {current_content}\\n"

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code)

            printIt(
                f"JSON template generated: {template_name} -> {os.path.basename(new_template_path)}", lable.PASS)
            return True

        except Exception as e:
            printIt(
                f"Error generating JSON template for {file_path}: {e}", lable.ERROR)
            return False

    def _generate_markdown_template(self, file_path: str, current_content: str, template_name: str, template_file: str) -> bool:
        \"\"\"Generate new Markdown template from modified file\"\"\"
        printIt(f"Generating Markdown template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(
                self.new_templates_dir, template_file_name)

            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(current_content)

            # Generate Python code with dedent string
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code)

            printIt(
                f"Markdown template generated: {template_name} -> {os.path.basename(new_template_path)}", lable.PASS)
            return True

        except Exception as e:
            printIt(
                f"Error generating Markdown template for {file_path}: {e}", lable.ERROR)
            return False

    def _generate_python_template(self, file_path: str, current_content: str, template_name: str, template_file: str) -> bool:
        \"\"\"Generate new Python template from modified file\"\"\"
        printIt(f"Generating Python template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(
                self.new_templates_dir, template_file_name)

            # Extract commandJsonDict from the source file and prepare for substitution
            command_json_dict = self._extract_command_json_dict(file_path)
            
            # Apply field substitutions including commandJsonDict
            fields = self.sync_data.get('fields', {})
            if command_json_dict:
                fields = fields.copy()  # Don't modify the original
                fields['commandJsonDict'] = command_json_dict
            
            # Apply field substitutions to content before creating template
            content_with_substitutions = self._substitute_template_fields(current_content, fields)
            
            # Determine template format based on template name patterns
            if 'Template' in template_name and template_name.endswith('Template'):
                # This is a Template() object - use Template(dedent(\"\"\"...\"\"\"))
                escaped_content = self._escape_string_for_template(
                    content_with_substitutions)
                template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
            else:
                # This is a simple dedent string
                escaped_content = self._escape_string_for_template(
                    content_with_substitutions)
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code)

            printIt(
                f"Python template generated: {template_name} -> {os.path.basename(new_template_path)}", lable.PASS)
            return True

        except Exception as e:
            printIt(
                f"Error generating Python template for {file_path}: {e}", lable.ERROR)
            return False

    def _generate_generic_template(self, file_path: str, current_content: str, template_name: str, template_file: str) -> bool:
        \"\"\"Generate new generic template from modified file\"\"\"
        printIt(f"Generating generic template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(
                self.new_templates_dir, template_file_name)

            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(current_content)

            # Generate Python code with dedent string
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code)

            printIt(
                f"Generic template generated: {template_name} -> {os.path.basename(new_template_path)}", lable.PASS)
            return True

        except Exception as e:
            printIt(
                f"Error generating generic template for {file_path}: {e}", lable.ERROR)
            return False

    def _merge_json_structures(self, template: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Merge JSON structures, preserving user modifications where possible\"\"\"
        merged = copy.deepcopy(template)

        # Recursively merge structures
        def merge_recursive(tmpl_obj, curr_obj, path=""):
            if isinstance(tmpl_obj, dict) and isinstance(curr_obj, dict):
                for key in curr_obj:
                    if key in tmpl_obj:
                        if isinstance(tmpl_obj[key], (dict, list)):
                            tmpl_obj[key] = merge_recursive(
                                tmpl_obj[key], curr_obj[key], f"{path}.{key}")
                        else:
                            # Keep user's value if it differs from template
                            tmpl_obj[key] = curr_obj[key]
                    else:
                        # This is a user addition, keep it
                        tmpl_obj[key] = curr_obj[key]
            elif isinstance(tmpl_obj, list) and isinstance(curr_obj, list):
                # For lists, we keep the current version to preserve user modifications
                return curr_obj
            else:
                # For primitive types, keep current value
                return curr_obj

            return tmpl_obj

        return merge_recursive(merged, current)

    def _is_template_file_valid(self, template_file_path: str) -> bool:
        \"\"\"Check if a template file has valid structure (basic checks only)\"\"\"
        try:
            with open(template_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip Python syntax compilation check for .py template files
            # Template files contain template variables like $${packName} which aren't valid Python
            # We only check for structural corruption patterns
            
            # Check for common corruption patterns
            corruption_patterns = [
                r'\"\"\"\\)def ',  # Missing newline after template ending with \"\"\")
                r'\"\"\"\\)class ',  # Missing newline after template ending with \"\"\")
                r'\"\"\"\\)[a-zA-Z]',  # Missing newline after template (general)
            ]

            import re
            for pattern in corruption_patterns:
                if re.search(pattern, content):
                    printIt(
                        f"Template corruption detected in {template_file_path}: pattern {pattern}", lable.WARN)
                    return False
            
            return True

        except Exception as e:
            printIt(
                f"Error validating template file {template_file_path}: {e}", lable.WARN)
            return False

    def _write_to_template_file(self, template_file_path: str, template_name: str, template_code: str):
        \"\"\"Write or update template code in a template file, maintaining original structure and order\"\"\"
        # Get the original template file from the new templates directory
        template_file_name = os.path.basename(template_file_path)
        original_template_path = os.path.join(
            self.new_templates_dir, template_file_name)

        # Load original template file to maintain structure
        if os.path.exists(original_template_path):
            with open(original_template_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        else:
            printIt(
                f"Original template file not found: {original_template_path}", lable.WARN)
            original_content = ""

        # Load existing new template file content if it exists
        if os.path.exists(template_file_path):
            with open(template_file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = original_content  # Start with original structure

        # Find and replace the specific template
        import re

        # First, try to find existing template in the content and replace it
        template_pattern = rf'^({re.escape(template_name)}\\s*=.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*\\s*=|\\Z)'
        match = re.search(template_pattern, existing_content,
                          re.MULTILINE | re.DOTALL)

        if match:
            # Replace existing template
            new_content = re.sub(template_pattern, template_code.rstrip(
            ), existing_content, flags=re.MULTILINE | re.DOTALL)
        else:
            # Template doesn't exist in new file, try to find it in original and replace
            original_match = re.search(
                template_pattern, original_content, re.MULTILINE | re.DOTALL)
            if original_match:
                # Add the template in the same position as original
                new_content = re.sub(template_pattern, template_code.rstrip(
                ), original_content, flags=re.MULTILINE | re.DOTALL)

                # Now merge any other updates from existing_content
                if existing_content != original_content:
                    # This is complex - for now, just replace the content
                    new_content = existing_content
                    new_content = re.sub(template_pattern, template_code.rstrip(
                    ), new_content, flags=re.MULTILINE | re.DOTALL)
            else:
                # Template not found anywhere, append at end
                if existing_content and not existing_content.endswith('\\n'):
                    existing_content += '\\n'
                new_content = existing_content + '\\n' + template_code

        # Ensure necessary imports are present
        imports_needed = []
        if 'dedent(' in new_content and 'from textwrap import dedent' not in new_content:
            imports_needed.append('from textwrap import dedent')
        if 'Template(' in new_content and 'from string import Template' not in new_content:
            imports_needed.append('from string import Template')

        if imports_needed:
            import_lines = '\\n'.join(imports_needed) + '\\n'
            if new_content.startswith('#!'):
                # Find end of shebang and encoding lines
                lines = new_content.split('\\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith('#') and ('coding' in line or 'encoding' in line or line.startswith('#!')):
                        insert_pos = i + 1
                    else:
                        break
                lines.insert(insert_pos, import_lines)
                new_content = '\\n'.join(lines)
            else:
                new_content = import_lines + '\\n' + new_content

        # Ensure the directory exists
        os.makedirs(os.path.dirname(template_file_path), exist_ok=True)

        # Write the file
        with open(template_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def sync_all_files(self, file_patterns: Optional[List[str]] = None) -> bool:
        \"\"\"Synchronize all tracked files or files matching patterns\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return False

        fields = self.sync_data.get('fields', {})
        if not fields:
            printIt("No field data found in sync data", lable.WARN)

        # Group files by their template files to process them together
        template_file_groups = {}
        files_to_sync = []

        for file_path, file_info in self.sync_data.items():
            if file_path == 'fields':  # Skip the fields section
                continue

            if not isinstance(file_info, dict):
                continue

            # If patterns specified, check if file matches
            if file_patterns:
                matches = False
                for pattern in file_patterns:
                    if pattern in file_path or pattern in os.path.basename(file_path):
                        matches = True
                        break
                if not matches:
                    continue

            files_to_sync.append(file_path)

            # Group by template file
            template_file = file_info.get('tempFileName', '')
            if template_file:
                template_file_name = os.path.basename(template_file)
                if template_file_name not in template_file_groups:
                    template_file_groups[template_file_name] = []
                template_file_groups[template_file_name].append(
                    (file_path, file_info))

        if not files_to_sync:
            printIt("No files to sync", lable.INFO)
            return True

        action_verb = "Would generate templates for" if self.dry_run else "Generating templates for"
        printIt(f"{action_verb} {len(files_to_sync)} files...", lable.INFO)

        success_count = 0

        # Process each template file group
        for template_file_name, file_group in template_file_groups.items():
            if self._sync_template_file_group(template_file_name, file_group):
                success_count += len(file_group)

            # Also process individual files for reporting
            for file_path, file_info in file_group:
                self._report_file_sync(file_path, file_info)

        verb = "Would generate templates for" if self.dry_run else "Generated templates for"
        printIt(f"{verb} {success_count}/{len(files_to_sync)} files", lable.INFO)

        # Save updated sync data
        if success_count > 0:
            self._save_sync_data()

        # Show untracked files in dry-run mode
        if self.dry_run:
            untracked_files = self._discover_untracked_files()
            if untracked_files:
                printIt("\\n" + cStr("Untracked files discovered:", color.CYAN), lable.INFO)
                printIt("-" * 80, lable.INFO)
                for file_path in untracked_files:
                    try:
                        rel_path = os.path.relpath(file_path, self.project_root)
                    except ValueError:
                        rel_path = file_path
                    printIt(f"  {cStr('UNTRACKED', color.CYAN)} {rel_path}", lable.INFO)
                printIt(f"\\n  To track these files, use: {cStr('${packName} sync make <file>', color.GREEN)}", lable.INFO)

        return success_count == len(files_to_sync)

    def _sync_template_file_group(self, template_file_name: str, file_group: List[Tuple[str, Dict[str, Any]]]) -> bool:
        \"\"\"Sync a group of files that belong to the same template file\"\"\"
        
        # Check if this is using the special newMakeTemplate marker
        # This marker indicates files that are authorized for make action
        if template_file_name == 'newMakeTemplate':
            # Create standalone template files for each modified file in this group
            return self._create_standalone_templates_for_group(file_group)
        
        if self.dry_run:
            printIt(
                f"Dry run: Would generate new template file: {template_file_name}", lable.INFO)
            return True

        # Get the original template file path from the first file in the group
        original_template_path = None
        for file_path, file_info in file_group:
            temp_file_name = file_info.get('tempFileName', '')
            if temp_file_name and temp_file_name != 'string':
                original_template_path = temp_file_name
                break

        # If no valid template file found, skip this group
        if not original_template_path:
            printIt(
                f"No valid template file path found for template: {template_file_name}", lable.WARN)
            return False

        # Print the original template location
        printIt(
            f"Original template location: {original_template_path}", lable.INFO)

        # Check if we have a newer version in newTemplates directory first
        new_template_path = os.path.join(
            self.new_templates_dir, template_file_name)

        # Check if newTemplates version exists and is valid
        use_new_template = False
        if os.path.exists(new_template_path):
            if self._is_template_file_valid(new_template_path):
                base_template_path = new_template_path
                use_new_template = True
                printIt(
                    f"Using existing newTemplates version: {template_file_name}", lable.INFO)
            else:
                printIt(
                    f"Corrupted newTemplates file detected, using original: {template_file_name}", lable.WARN)
                base_template_path = original_template_path
        elif os.path.exists(original_template_path):
            base_template_path = original_template_path
            printIt(
                f"Using original template: {template_file_name}", lable.INFO)
        else:
            printIt(
                f"Template file not found: {original_template_path}", lable.ERROR)
            return False

        try:
            with open(base_template_path, 'r', encoding='utf-8') as f:
                base_content = f.read()
        except Exception as e:
            printIt(f"Error reading base template file: {e}", lable.ERROR)
            return False

        # Start with the base content (either original or existing newTemplates version)
        new_content = base_content

        # Replace each modified template
        for file_path, file_info in file_group:
            if not os.path.exists(file_path):
                continue

            # Check if file is modified
            current_md5 = self._calculate_md5(file_path)
            stored_md5 = file_info.get('fileMD5', '')

            if current_md5 == stored_md5:
                continue  # File unchanged

            # Generate new template content for this file
            template_name = file_info.get('template', '')
            if not template_name:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_file_content = f.read()
            except Exception as e:
                printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
                continue

            # Generate template code based on file type
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.json':
                template_code = f"{template_name} = {current_file_content}"
            elif file_ext in ['.py', '.md'] or template_name.endswith('Template'):
                escaped_content = self._escape_string_for_template(
                    current_file_content)
                if 'Template' in template_name and template_name.endswith('Template'):
                    template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))'
                else:
                    template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")'
            else:
                escaped_content = self._escape_string_for_template(
                    current_file_content)
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")'

            # Replace the template in the content
            import re
            template_pattern = rf'^({re.escape(template_name)}\\s*=.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*\\s*=|\\Z)'
            new_content = re.sub(
                template_pattern, template_code, new_content, flags=re.MULTILINE | re.DOTALL)

            # Update the MD5 in sync data
            self.sync_data[file_path]['fileMD5'] = current_md5

        # Write the new template file
        new_template_path = os.path.join(
            self.new_templates_dir, template_file_name)

        # Ensure the newTemplates directory exists
        os.makedirs(self.new_templates_dir, exist_ok=True)

        # Special handling for cmdTemplate.py - update the hardcoded commandsJsonDict
        if template_file_name == 'cmdTemplate.py':
            import re
            complete_commands_dict = self._build_complete_commands_json_dict()
            # Replace the hardcoded commandsJsonDict with the complete version
            pattern = r'(commandsJsonDict\\s*=\\s*)\\{.*?\\n\\}'
            replacement = f'\\\\1{complete_commands_dict}\\n'
            new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)

        try:
            with open(new_template_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            printIt(
                f"Template file generated: {template_file_name}", lable.PASS)
            return True
        except Exception as e:
            printIt(f"Error writing new template file: {e}", lable.ERROR)
            return False

    def _create_standalone_templates_for_group(self, file_group: List[Tuple[str, Dict[str, Any]]]) -> bool:
        \"\"\"Create standalone template files for files in newMakeTemplate group\"\"\"
        success_count = 0
        total_processed = 0
        
        for file_path, file_info in file_group:
            if not os.path.exists(file_path):
                total_processed += 1  # Count as processed (file missing is handled gracefully)
                success_count += 1   # This is not an error condition
                continue

            template_name = file_info.get('template', '')
            if not template_name:
                total_processed += 1  # Count as processed (no template name to work with)
                success_count += 1   # This is not an error condition
                continue

            total_processed += 1  # Count this file as being processed

            # Check if file comes from commands parent directory
            # If so, it should go into the combined cmdTemplate.py file
            file_dir = os.path.dirname(os.path.abspath(file_path))
            commands_dir = os.path.join(self.project_root, 'src', '${packName}', 'commands')
            is_from_commands_dir = file_dir.startswith(commands_dir)

            # Check if the template file already exists
            template_exists = self._check_template_exists(file_path, file_info, is_from_commands_dir)

            # Check if file is modified
            current_md5 = self._calculate_md5(file_path)
            stored_md5 = file_info.get('fileMD5', '')
            is_modified = current_md5 != stored_md5

            # Skip if template exists and file is unchanged
            if template_exists and not is_modified:
                success_count += 1  # No work needed - this is success
                continue

            if self.dry_run:
                if template_exists and is_modified:
                    action = "Would update"
                elif not template_exists:
                    action = "Would create"
                else:
                    continue  # No action needed
                
                if is_from_commands_dir:
                    printIt(f"Dry run: {action} template '{template_name}' in combined file: cmdTemplate.py", lable.INFO)
                else:
                    filename = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    if file_ext == '.json':
                        template_filename = filename
                    else:
                        template_filename = f"{name_without_ext}.py"
                    
                    printIt(f"Dry run: {action} standalone template file: {template_filename}", lable.INFO)
                printIt(f"Template name: {template_name}", lable.INFO)
                success_count += 1
                continue

            # Create or update template file (standalone or combined)
            if is_from_commands_dir:
                if self._add_to_combined_template_file(file_path, file_info):
                    success_count += 1
                    # Update the MD5 in sync data
                    self.sync_data[file_path]['fileMD5'] = current_md5
                # If it failed, success_count is not incremented, but total_processed already is
            else:
                if self._create_standalone_template_file(file_path, file_info):
                    success_count += 1
                    # Update the MD5 in sync data
                    self.sync_data[file_path]['fileMD5'] = current_md5
                # If it failed, success_count is not incremented, but total_processed already is

        return success_count == total_processed

    def _check_template_exists(self, file_path: str, file_info: Dict[str, Any], is_from_commands_dir: bool) -> bool:
        \"\"\"Check if the template file exists for this source file\"\"\"
        template_name = file_info.get('template', '')
        
        if is_from_commands_dir:
            # Check if template exists in combined cmdTemplate.py
            combined_template_path = os.path.join(self.new_templates_dir, 'cmdTemplate.py')
            if not os.path.exists(combined_template_path):
                return False
            
            try:
                with open(combined_template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                pattern = rf'^{re.escape(template_name)}\\s*='
                return bool(re.search(pattern, content, re.MULTILINE))
            except Exception:
                return False
        else:
            # Check if standalone template file exists
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                template_filename = filename
            else:
                template_filename = f"{name_without_ext}.py"
            
            template_file_path = os.path.join(self.new_templates_dir, template_filename)
            return os.path.exists(template_file_path)

    def _create_standalone_template_file(self, file_path: str, file_info: Dict[str, Any]) -> bool:
        \"\"\"Create a standalone template file for a single file\"\"\"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        template_name = file_info.get('template', '')
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(file_path)[1].lower()

        # Determine template file name
        if file_ext == '.json':
            template_filename = filename
        else:
            template_filename = f"{name_without_ext}.py"

        new_template_path = os.path.join(self.new_templates_dir, template_filename)

        # Ensure the newTemplates directory exists
        os.makedirs(self.new_templates_dir, exist_ok=True)

        # Generate template content based on file type
        if file_ext == '.json':
            try:
                # Validate JSON
                json.loads(file_content)
                template_file_content = file_content
            except json.JSONDecodeError as e:
                printIt(f"Invalid JSON in file {file_path}: {e}", lable.ERROR)
                return False
        else:
            # For other files, create a full Python template file structure
            # Convert literal values to placeholders first
            content_with_placeholders = self._convert_literals_to_placeholders(file_content)
            escaped_content = self._escape_string_for_template(content_with_placeholders)
            
            # Determine template format
            if file_ext == '.md' or template_name.lower().endswith('template'):
                template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
            else:
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Create full template file content
            imports_needed = []
            if 'dedent(' in template_code:
                imports_needed.append('from textwrap import dedent')
            if 'Template(' in template_code:
                imports_needed.append('from string import Template')
            
            import_lines = '\\n'.join(imports_needed) if imports_needed else ''
            
            template_file_content = f\"\"\"#!/usr/bin/python
# -*- coding: utf-8 -*-
{import_lines}

{template_code}
\"\"\"

        try:
            with open(new_template_path, 'w', encoding='utf-8') as f:
                f.write(template_file_content)
            printIt(f"Standalone template file created: {template_filename}", lable.PASS)
            printIt(f"Template name: {template_name}", lable.INFO)
            return True
        except Exception as e:
            printIt(f"Error writing template file {new_template_path}: {e}", lable.ERROR)
            return False

    def _add_to_combined_template_file(self, file_path: str, file_info: Dict[str, Any]) -> bool:
        \"\"\"Add a template to the combined cmdTemplate.py file\"\"\"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        template_name = file_info.get('template', '')
        combined_template_path = os.path.join(self.new_templates_dir, 'cmdTemplate.py')

        # Ensure the newTemplates directory exists
        os.makedirs(self.new_templates_dir, exist_ok=True)

        # Read existing combined template file or create new
        if os.path.exists(combined_template_path):
            with open(combined_template_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            # Create new template file with header
            existing_content = \"\"\"#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

\"\"\"

        # Check if template already exists in file
        import re
        pattern = rf'^{re.escape(template_name)}\\s*='
        if re.search(pattern, existing_content, re.MULTILINE):
            printIt(f"Template '{template_name}' already exists in cmdTemplate.py", lable.WARN)
            # Replace existing template instead of skipping
            content_with_placeholders = self._convert_literals_to_placeholders(file_content)
            escaped_content = self._escape_string_for_template(content_with_placeholders)
            template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))'
            
            # Replace the existing template
            template_pattern = rf'^{re.escape(template_name)}\\s*=\\s*Template\\(dedent\\(\"\"\".*?\"\"\"\\)\\)'
            updated_content = re.sub(template_pattern, template_code, existing_content, flags=re.MULTILINE | re.DOTALL)
            
            # If Template pattern didn't match, try dedent pattern
            if updated_content == existing_content:
                template_pattern = rf'^{re.escape(template_name)}\\s*=\\s*dedent\\(\"\"\".*?\"\"\"\\)'
                updated_content = re.sub(template_pattern, template_code, existing_content, flags=re.MULTILINE | re.DOTALL)
        else:
            # Generate template code for commands (always use Template format)
            content_with_placeholders = self._convert_literals_to_placeholders(file_content)
            escaped_content = self._escape_string_for_template(content_with_placeholders)
            template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'

            # Insert after the last command template
            # Command templates match: *CmdTemplate, runTestTemplate, or syncTemplate
            lines = existing_content.split('\\n')
            last_cmd_template_end = -1
            
            # Find the last line of the last command template
            in_template = False
            paren_count = 0
            for i, line in enumerate(lines):
                # Check if this is a command template definition
                match = re.match(r'^(\\w+Template)\\s*=\\s*Template\\(dedent\\(', line)
                if match:
                    template_var_name = match.group(1)
                    # Check if this is a command template (not utility template)
                    # Command templates: *CmdTemplate, runTestTemplate, syncTemplate, fileDiffTemplate
                    # Utility templates: *TemplateStr, *Template (but not the above)
                    is_cmd_template = (
                        template_var_name.endswith('CmdTemplate') or 
                        template_var_name in ['runTestTemplate', 'syncTemplate', 'fileDiffTemplate']
                    )
                    if is_cmd_template:
                        in_template = True
                        paren_count = line.count('(') - line.count(')')
                elif in_template:
                    paren_count += line.count('(') - line.count(')')
                    if paren_count == 0:
                        # Found the end of this template
                        last_cmd_template_end = i
                        in_template = False
            
            if last_cmd_template_end != -1:
                # Insert after the last command template
                before_lines = lines[:last_cmd_template_end + 1]
                after_lines = lines[last_cmd_template_end + 1:]
                updated_content = '\\n'.join(before_lines) + '\\n\\n' + template_code.rstrip() + '\\n' + '\\n'.join(after_lines)
            else:
                # No command templates found, append at end
                updated_content = existing_content.rstrip() + '\\n\\n' + template_code

        try:
            with open(combined_template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            printIt(f"Template added to combined file: cmdTemplate.py", lable.PASS)
            printIt(f"Template name: {template_name}", lable.INFO)
            return True
        except Exception as e:
            printIt(f"Error writing combined template file: {e}", lable.ERROR)
            return False

    def _report_file_sync(self, file_path: str, file_info: Dict[str, Any]):
        \"\"\"Report on the sync status of a single file\"\"\"
        if not os.path.exists(file_path):
            printIt(
                f"File not found: {os.path.relpath(file_path, self.project_root)}", lable.WARN)
            return

        # Calculate current MD5
        current_md5 = self._calculate_md5(file_path)
        # Use the potentially updated MD5 from sync_data, not the old file_info
        stored_md5 = self.sync_data.get(file_path, {}).get('fileMD5', '')

        if current_md5 == stored_md5:
            printIt(
                f"File unchanged: {os.path.relpath(file_path, self.project_root)}", lable.INFO)
        else:
            printIt(
                f"File modified: {os.path.relpath(file_path, self.project_root)}", lable.WARN)
            template_name = file_info.get('template', '')
            if self.dry_run:
                printIt(
                    f"Dry run: Would update template: {template_name}", lable.INFO)
            else:
                printIt(f"Updated template: {template_name}", lable.PASS)

    def list_tracked_files(self):
        \"\"\"List all files tracked in the sync data\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return

        printIt("\\nTracked files:", lable.INFO)
        printIt("-" * 80, lable.INFO)

        for file_path, file_info in self.sync_data.items():
            if file_path == 'fields':
                continue

            if not isinstance(file_info, dict):
                continue

            # Check if file exists and if it's modified
            exists = os.path.exists(file_path)
            if exists:
                current_md5 = self._calculate_md5(file_path)
                stored_md5 = file_info.get('fileMD5', '')
                status = "OK" if current_md5 == stored_md5 else "MODIFIED"
                status_color = color.GREEN if status == "OK" else color.YELLOW
            else:
                status = "MISSING"
                status_color = color.RED

            template_name = file_info.get('template', 'Unknown')
            rel_path = os.path.relpath(file_path, self.project_root)

            printIt(
                f"{cStr(status, status_color):10} {rel_path:50} ({template_name})", lable.INFO)

    def show_status(self):
        \"\"\"Show status of all tracked files\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return

        total_files = 0
        ok_files = 0
        modified_files = 0
        missing_files = 0
        modified_file_list = []
        missing_file_list = []

        printIt("\\nFile synchronization status:", lable.INFO)
        printIt("=" * 80, lable.INFO)

        for file_path, file_info in self.sync_data.items():
            if file_path == 'fields':
                continue

            if not isinstance(file_info, dict):
                continue

            total_files += 1

            # Check if file exists and if it's modified
            exists = os.path.exists(file_path)
            if exists:
                current_md5 = self._calculate_md5(file_path)
                stored_md5 = file_info.get('fileMD5', '')
                if current_md5 == stored_md5:
                    ok_files += 1
                else:
                    modified_files += 1
                    template_name = file_info.get('template', 'unknown')
                    modified_file_list.append((file_path, template_name))
            else:
                missing_files += 1
                template_name = file_info.get('template', 'unknown')
                missing_file_list.append((file_path, template_name))

        printIt(f"Total tracked files: {total_files}", lable.INFO)
        printIt(f"{cStr('Files in sync:', color.GREEN)} {ok_files}", lable.INFO)
        if modified_files > 0:
            printIt(
                f"{cStr('Modified files:', color.YELLOW)} {modified_files}", lable.INFO)
        if missing_files > 0:
            printIt(
                f"{cStr('Missing files:', color.RED)} {missing_files}", lable.INFO)

        # List modified files
        if modified_file_list:
            printIt("\\n" + cStr("Modified files:", color.YELLOW), lable.INFO)
            printIt("-" * 80, lable.INFO)
            for file_path, template_name in modified_file_list:
                # Show relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, self.project_root)
                except ValueError:
                    rel_path = file_path
                printIt(f"  {cStr('MODIFIED', color.YELLOW)} {rel_path}", lable.INFO)
                printIt(f"           Template: {template_name}", lable.INFO)

        # List missing files
        if missing_file_list:
            printIt("\\n" + cStr("Missing files:", color.RED), lable.INFO)
            printIt("-" * 80, lable.INFO)
            for file_path, template_name in missing_file_list:
                # Show relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, self.project_root)
                except ValueError:
                    rel_path = file_path
                printIt(f"  {cStr('MISSING', color.RED)} {rel_path}", lable.INFO)
                printIt(f"          Template: {template_name}", lable.INFO)

        # List untracked files
        untracked_files = self._discover_untracked_files()
        if untracked_files:
            printIt("\\n" + cStr("Untracked files (consider using 'make'):", color.CYAN), lable.INFO)
            printIt("-" * 80, lable.INFO)
            for file_path in untracked_files:
                # Show relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, self.project_root)
                except ValueError:
                    rel_path = file_path
                printIt(f"  {cStr('UNTRACKED', color.CYAN)} {rel_path}", lable.INFO)
            printIt(f"\\n  To track these files, use: {cStr('${packName} sync make <file>', color.GREEN)}", lable.INFO)

    def _discover_untracked_files(self) -> List[str]:
        \"\"\"Discover files that exist but aren't tracked in genTempSyncData.json\"\"\"
        untracked = []
        
        # Get list of tracked files
        tracked_files = set()
        for file_path in self.sync_data.keys():
            if file_path != 'fields' and isinstance(self.sync_data[file_path], dict):
                # Normalize to absolute path
                if os.path.isabs(file_path):
                    tracked_files.add(file_path)
                else:
                    tracked_files.add(os.path.join(self.project_root, file_path))
        
        # Directories to scan for potential template files
        scan_dirs = [
            os.path.join(self.project_root, 'tests'),
            os.path.join(self.project_root, 'src'),
        ]
        
        # File patterns to look for
        patterns = [
            'test_*.py',  # Test files
            '*.py',       # Python files
        ]
        
        # Files/directories to exclude
        exclude_patterns = [
            '__pycache__',
            '__init__.py',
            '.pyc',
            'env/',
            'venv/',
            '.git/',
            'build/',
            'dist/',
            '.egg-info',
        ]
        
        for scan_dir in scan_dirs:
            if not os.path.exists(scan_dir):
                continue
                
            for root, dirs, files in os.walk(scan_dir):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(excl in d for excl in exclude_patterns)]
                
                for file in files:
                    # Skip excluded files
                    if any(excl in file for excl in exclude_patterns):
                        continue
                    
                    # Check if file matches any pattern
                    file_path = os.path.join(root, file)
                    
                    # Only include Python files for now
                    if not file.endswith('.py'):
                        continue
                    
                    # Skip if already tracked
                    if file_path in tracked_files:
                        continue
                    
                    # Add to untracked list
                    untracked.append(file_path)
        
        return sorted(untracked)

    def _generate_template_code(self, file_path: str, file_content: str, template_name: str) -> str:
        \"\"\"Generate template code from file content\"\"\"
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            # For JSON files, validate and return as-is
            try:
                json.loads(file_content)
                return file_content
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        
        # For Python and other text files
        escaped_content = self._escape_string_for_template(file_content)
        
        # Check if this should use Template() wrapper
        if file_path.lower().endswith('template.py') or template_name.lower().endswith('template'):
            return f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
        else:
            return f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

    def make_template_from_file(self, file_path: str) -> bool:
        \"\"\"Create a new template file from the specified file\"\"\"
        if not os.path.exists(file_path):
            printIt(f"File not found: {file_path}", lable.ERROR)
            return False

        # Make file_path relative to project root if it's absolute
        if os.path.isabs(file_path):
            try:
                file_path = os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If file is on different drive, keep absolute path
                pass

        # Check if file is tracked in sync data
        # If tempFileName is NOT "newMakeTemplate", require authorization
        absolute_file_path = os.path.abspath(file_path)
        if absolute_file_path in self.sync_data:
            temp_file_name = self.sync_data[absolute_file_path].get('tempFileName', '')
            
            # Only require authorization if tempFileName is NOT "newMakeTemplate"
            if temp_file_name != "newMakeTemplate":
                printIt(f"WARNING: File '{file_path}' is already tracked in genTempSyncData.json", lable.WARN)
                existing_template = self.sync_data[absolute_file_path].get('template', 'Unknown')
                printIt(f"Current template: {existing_template}", lable.INFO)
                printIt(f"Current template file: {temp_file_name}", lable.INFO)
                printIt("Creating a new template could interfere with existing synchronization.", lable.WARN)
                
                try:
                    response = input("Do you want to proceed anyway? (yes/no): ").strip().lower()
                    if response not in ['yes', 'y']:
                        printIt("Template creation cancelled by user", lable.INFO)
                        return False
                except (EOFError, KeyboardInterrupt):
                    printIt("\\nTemplate creation cancelled by user", lable.INFO)
                    return False

        printIt(f"Creating template from file: {file_path}", lable.INFO)

        # Check if files in the same directory share a common template file
        # If so, we should insert into that shared template instead of creating standalone
        shared_template_file = None
        absolute_file_path = os.path.abspath(file_path)
        file_dir = os.path.dirname(absolute_file_path)
        
        # Look for other files in the same directory that are tracked
        for tracked_path, tracked_data in self.sync_data.items():
            tracked_dir = os.path.dirname(tracked_path)
            if tracked_dir == file_dir:
                # Found a file in same directory
                temp_file = tracked_data.get('tempFileName', '')
                # If it has a real template file (not "newMakeTemplate"), use it
                if temp_file and temp_file != "newMakeTemplate" and os.path.exists(temp_file):
                    shared_template_file = temp_file
                    break
        
        # If we found a shared template file, we should insert there
        # Otherwise, create a standalone template file
        if shared_template_file:
            printIt(f"File is from directory that uses shared template: {os.path.basename(shared_template_file)}", lable.INFO)
            # We'll need to use _generate_template_code and insert into shared file
            use_shared_template = True
            target_template_file = shared_template_file
        else:
            use_shared_template = False
            target_template_file = ""

        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        # Determine template name based on filename
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # For shared templates (like cmdTemplate.py), use <cmdName>Template naming pattern
        if use_shared_template:
            # Check if this is being inserted into cmdTemplate.py
            template_basename = os.path.basename(target_template_file)
            if template_basename == 'cmdTemplate.py':
                template_name = f"{name_without_ext}Template"
            else:
                template_name = f"{name_without_ext}_template"
        else:
            template_name = f"{name_without_ext}_template"

        # If using shared template, insert the template code there
        if use_shared_template:
            # Extract commandJsonDict from the source file and prepare for substitution
            command_json_dict = self._extract_command_json_dict(file_path)
            
            # Apply field substitutions including commandJsonDict
            fields = self.sync_data.get('fields', {})
            if command_json_dict:
                fields = fields.copy()  # Don't modify the original
                fields['commandJsonDict'] = command_json_dict
            
            # Apply field substitutions to content before creating template
            content_with_substitutions = self._substitute_template_fields(file_content, fields)
            
            # Generate template code for this file
            # For cmdTemplate.py, always use Template(dedent()) format
            template_basename = os.path.basename(target_template_file)
            if template_basename == 'cmdTemplate.py':
                escaped_content = self._escape_string_for_template(content_with_substitutions)
                template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
            else:
                template_code = self._generate_template_code(file_path, content_with_substitutions, template_name)
            
            # Determine the output template file path in newTemplates/
            template_basename = os.path.basename(target_template_file)
            new_template_path = os.path.join(self.new_templates_dir, template_basename)
            
            if self.dry_run:
                printIt(f"Dry run: Would insert template '{template_name}' into: {new_template_path}", lable.INFO)
                return True
            
            # Ensure directory exists
            os.makedirs(self.new_templates_dir, exist_ok=True)
            
            # Read existing template file or create new
            if os.path.exists(new_template_path):
                with open(new_template_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            elif os.path.exists(target_template_file):
                # Use original template file
                with open(target_template_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                # Create new template file with header
                existing_content = \"\"\"#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

\"\"\"
            
            # Check if template already exists in file
            pattern = rf'^{re.escape(template_name)}\\s*='
            if re.search(pattern, existing_content, re.MULTILINE):
                printIt(f"Template '{template_name}' already exists in {template_basename}", lable.WARN)
                printIt("Skipping duplicate template insertion", lable.INFO)
                return False
            
            # For cmdTemplate.py, insert after the last command template
            # Command templates are: *CmdTemplate, runTestTemplate, syncTemplate
            # (as opposed to utility templates like validationTemplate, argCmdDefTemplateStr, etc.)
            if template_basename == 'cmdTemplate.py' and template_name.endswith('Template'):
                # Find all command template positions
                # Command templates match: newCmdTemplate, modCmdTemplate, rmCmdTemplate, runTestTemplate, syncTemplate
                # Pattern: ends with 'CmdTemplate' OR is 'runTestTemplate' OR is 'syncTemplate'
                lines = existing_content.split('\\n')
                last_cmd_template_end = -1
                
                # Find the last line of the last command template
                in_template = False
                paren_count = 0
                for i, line in enumerate(lines):
                    # Check if this is a command template definition
                    # Match: <name>CmdTemplate, runTestTemplate, or syncTemplate (but not the one we're adding)
                    match = re.match(r'^(\\w+Template)\\s*=\\s*Template\\(dedent\\(', line)
                    if match:
                        template_var_name = match.group(1)
                        # Check if this is a command template (not utility template)
                        # Command templates: *CmdTemplate, runTestTemplate, syncTemplate, fileDiffTemplate
                        is_cmd_template = (
                            template_var_name.endswith('CmdTemplate') or 
                            template_var_name in ['runTestTemplate', 'syncTemplate', 'fileDiffTemplate'] and template_var_name != template_name
                        )
                        if is_cmd_template:
                            in_template = True
                            paren_count = line.count('(') - line.count(')')
                    elif in_template:
                        paren_count += line.count('(') - line.count(')')
                        if paren_count == 0:
                            # Found the end of this template
                            last_cmd_template_end = i
                            in_template = False
                
                if last_cmd_template_end != -1:
                    # Insert after the last command template
                    before_lines = lines[:last_cmd_template_end + 1]
                    after_lines = lines[last_cmd_template_end + 1:]
                    updated_content = '\\n'.join(before_lines) + '\\n\\n' + template_code.rstrip() + '\\n' + '\\n'.join(after_lines)
                else:
                    # No command templates found, append at end
                    updated_content = existing_content.rstrip() + '\\n\\n' + template_code
            else:
                # For other template files, just append at the end
                updated_content = existing_content.rstrip() + '\\n\\n' + template_code
            
            try:
                with open(new_template_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                printIt(f"Template inserted into: {new_template_path}", lable.PASS)
                printIt(f"Template name: {template_name}", lable.INFO)
                
                # Add the original file to genTempSyncData.json tracking
                absolute_file_path = os.path.abspath(file_path)
                current_md5 = self._calculate_md5(file_path)
                
                # Add entry to sync data
                self.sync_data[absolute_file_path] = {
                    "fileMD5": current_md5,
                    "template": template_name,
                    "tempFileName": "newMakeTemplate"
                }
                
                # Save the updated sync data
                self._save_sync_data()
                printIt(f"Added {file_path} to sync tracking", lable.INFO)
                
                return True
            except Exception as e:
                printIt(f"Error writing template file: {e}", lable.ERROR)
                return False

        # Create template file name for standalone template
        template_filename = f"{filename}"

        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        # Determine template name based on filename
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        template_name = f"{name_without_ext}_template"

        # Determine file type and generate appropriate template code
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # For .md files, convert literal values to template placeholders
        if file_ext == '.md':
            file_content = self._convert_literals_to_placeholders(file_content)

        # Create template file name - for non-Python files that generate Python templates, use .py extension
        if file_ext == '.json':
            template_filename = f"{filename}"  # JSON files keep their extension
        else:
            template_filename = f"{name_without_ext}.py"  # Other files get .py extension

        if file_ext == '.json':
            try:
                # Validate JSON
                json.loads(file_content)
                # For JSON files, we'll use the raw content directly in template file
                template_code = file_content
            except json.JSONDecodeError as e:
                printIt(f"Invalid JSON in file {file_path}: {e}", lable.ERROR)
                return False
        elif file_ext in ['.py', '.md', '.txt'] or template_name.lower().endswith('template'):
            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(file_content)
            # .md files should always use Template(dedent()) format
            if file_ext == '.md' or ('template' in template_name.lower() and template_name.lower().endswith('template')):
                template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
            else:
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'
        else:
            # Generic template for other file types
            escaped_content = self._escape_string_for_template(file_content)
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

        # Create the template file path
        new_template_path = os.path.join(self.new_templates_dir, template_filename)

        if self.dry_run:
            printIt(f"Dry run: Would create template file: {new_template_path}", lable.INFO)
            printIt(f"Template name: {template_name}", lable.INFO)
            return True

        # Ensure the newTemplates directory exists
        os.makedirs(self.new_templates_dir, exist_ok=True)

        # Create template file content based on file type
        if file_ext == '.json':
            # For JSON files, just write the template code without Python headers
            template_file_content = template_code
        else:
            # For other files, create a full Python template file structure
            imports_needed = []
            if 'dedent(' in template_code:
                imports_needed.append('from textwrap import dedent')
            if 'Template(' in template_code:
                imports_needed.append('from string import Template')
            
            import_lines = '\\n'.join(imports_needed) if imports_needed else ''
            
            template_file_content = f\"\"\"#!/usr/bin/python
# -*- coding: utf-8 -*-
{import_lines}

{template_code}
\"\"\"

        try:
            with open(new_template_path, 'w', encoding='utf-8') as f:
                f.write(template_file_content)
            printIt(f"Template file created: {new_template_path}", lable.PASS)
            printIt(f"Template name: {template_name}", lable.INFO)
            
            # Add the original file to genTempSyncData.json tracking
            if not self.dry_run:
                absolute_file_path = os.path.abspath(file_path)
                current_md5 = self._calculate_md5(file_path)
                
                # Add entry to sync data
                self.sync_data[absolute_file_path] = {
                    "fileMD5": current_md5,
                    "template": template_name,
                    "tempFileName": "newMakeTemplate"
                }
                
                # Save the updated sync data
                self._save_sync_data()
                printIt(f"Added {file_path} to sync tracking", lable.INFO)
            
            return True
        except Exception as e:
            printIt(f"Error writing template file: {e}", lable.ERROR)
            return False

    def remove_template_from_file(self, file_path: str) -> bool:
        \"\"\"Remove a template that was created from the specified file\"\"\"
        if not os.path.exists(file_path):
            printIt(f"File not found: {file_path}", lable.ERROR)
            return False

        # Make file_path relative to project root if it's absolute
        if os.path.isabs(file_path):
            try:
                file_path = os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If file is on different drive, keep absolute path
                pass

        # Check if file is tracked in sync data
        absolute_file_path = os.path.abspath(file_path)
        if absolute_file_path not in self.sync_data:
            printIt(f"File '{file_path}' is not tracked in genTempSyncData.json", lable.ERROR)
            printIt("Only files created with 'make' action can be removed with 'rmTemp'", lable.INFO)
            return False

        file_info = self.sync_data[absolute_file_path]
        temp_file_name = file_info.get('tempFileName', '')
        template_name = file_info.get('template', '')

        # Only allow removal of templates created with 'make' action (tempFileName: "newMakeTemplate")
        if temp_file_name != "newMakeTemplate":
            printIt(f"File '{file_path}' was not created with 'make' action", lable.ERROR)
            printIt(f"Current template file: {temp_file_name}", lable.INFO)
            printIt("Only files created with 'make' action can be removed with 'rmTemp'", lable.INFO)
            return False

        printIt(f"Removing template for file: {file_path}", lable.INFO)
        printIt(f"Template name: {template_name}", lable.INFO)

        if self.dry_run:
            printIt(f"Dry run: Would remove template '{template_name}'", lable.INFO)
            return True

        # Determine if this file should use combined template file (cmdTemplate.py)
        file_dir = os.path.dirname(os.path.abspath(file_path))
        commands_dir = os.path.join(self.project_root, 'src', '${packName}', 'commands')
        is_from_commands_dir = file_dir.startswith(commands_dir)
        
        if is_from_commands_dir:
            # Files from commands directory use the combined cmdTemplate.py
            template_filename = "cmdTemplate.py"
            template_file_path = os.path.join(self.new_templates_dir, template_filename)
        else:
            # Other files use standalone template files
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # For .md files and others that generate Python templates, use .py extension
            if file_ext == '.json':
                template_filename = filename  # JSON files keep their extension
            else:
                template_filename = f"{name_without_ext}.py"  # Other files get .py extension

            template_file_path = os.path.join(self.new_templates_dir, template_filename)

        # Remove the template file if it exists
        if os.path.exists(template_file_path):
            try:
                if is_from_commands_dir:
                    # Files from commands directory are always in shared cmdTemplate.py
                    with open(template_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    updated_content = self._remove_template_from_shared_file(content, template_name)
                    if updated_content:
                        with open(template_file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        printIt(f"Template '{template_name}' removed from shared file: {template_filename}", lable.PASS)
                    else:
                        printIt(f"Failed to remove template from shared file", lable.ERROR)
                        return False
                else:
                    # For standalone files, check if it's actually a shared template file
                    with open(template_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Count how many templates are in this file
                    import re
                    template_pattern = r'^(\\w+_template|\\w+Template)\\s*='
                    template_matches = re.findall(template_pattern, content, re.MULTILINE)
                    
                    if len(template_matches) > 1:
                        # This is a shared template file, remove only this template
                        updated_content = self._remove_template_from_shared_file(content, template_name)
                        if updated_content:
                            with open(template_file_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            printIt(f"Template '{template_name}' removed from shared file: {template_filename}", lable.PASS)
                        else:
                            printIt(f"Failed to remove template from shared file", lable.ERROR)
                            return False
                    else:
                        # This is a standalone template file, remove the entire file
                        os.unlink(template_file_path)
                        printIt(f"Template file removed: {template_filename}", lable.PASS)

            except Exception as e:
                printIt(f"Error removing template file: {e}", lable.ERROR)
                return False
        else:
            printIt(f"Template file not found: {template_filename} (may have been already removed)", lable.WARN)

        # Remove the entry from genTempSyncData.json
        try:
            del self.sync_data[absolute_file_path]
            self._save_sync_data()
            printIt(f"Removed {file_path} from sync tracking", lable.INFO)
        except Exception as e:
            printIt(f"Error updating sync data: {e}", lable.ERROR)
            return False

        return True

    def _remove_template_from_shared_file(self, content: str, template_name: str) -> Optional[str]:
        \"\"\"Remove a specific template from a shared template file\"\"\"
        import re
        
        # Find the template definition and remove it
        # Pattern matches: template_name = Template(dedent(\"\"\"...\"\"\")) or template_name = dedent(\"\"\"...\"\"\")
        
        # First try Template(dedent(...)) pattern
        template_pattern = rf'^{re.escape(template_name)}\\s*=\\s*Template\\(dedent\\(\"\"\".*?\"\"\"\\)\\)'
        match = re.search(template_pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            # Remove the matched template
            updated_content = re.sub(template_pattern, '', content, flags=re.DOTALL | re.MULTILINE)
        else:
            # Try dedent(...) pattern
            template_pattern = rf'^{re.escape(template_name)}\\s*=\\s*dedent\\(\"\"\".*?\"\"\"\\)'
            match = re.search(template_pattern, content, re.DOTALL | re.MULTILINE)
            
            if match:
                updated_content = re.sub(template_pattern, '', content, flags=re.DOTALL | re.MULTILINE)
            else:
                printIt(f"Template pattern not found for: {template_name}", lable.ERROR)
                return None
        
        # Clean up extra blank lines
        updated_content = re.sub(r'\\n\\s*\\n\\s*\\n', '\\n\\n', updated_content)
        
        return updated_content


class syncCommand:
    def __init__(self, argParse):
        self.argParse = argParse
        self.cmdObj = Commands()
        self.commands = self.cmdObj.commands
        self.args = argParse.args
        self.theCmd = self.args.commands[0]
        self.theArgNames = list(self.commands[self.theCmd].keys())
        self.theArgs = self.args.arguments

        # Use current working directory as project root
        self.project_root = os.getcwd()

        # Get command-line flags from .${packName}rc file after flag processing
        from ..classes.optSwitches import getCmdSwitchFlags
        cmd_flags = getCmdSwitchFlags('sync')
        # don't use commandFlags persistance for dry-run, check sys.argv directly
        if '-dry-run' in sys.argv or '--dry-run' in sys.argv or '+dry-run' in sys.argv or '++dry-run' in sys.argv:
            self.dry_run = True
        else:
            self.dry_run = False
        print(f'self.dry_run: {self.dry_run}')
        self.force = cmd_flags.get('force', False)
        self.backup = cmd_flags.get('backup', False)

    def execute(self):
        '''Main execution method for sync command'''
        printIt(f"Template synchronization tool", lable.INFO)

        # Initialize syncer
        syncer = TemplateSyncer(
            self.project_root, self.dry_run, self.force, self.backup)

        if not syncer.sync_data_file:
            printIt("Cannot proceed without genTempSyncData.json", lable.ERROR)
            return

        # Filter out flag arguments (starting with + or -)
        theArgs = [arg for arg in self.theArgs if not (
            isinstance(arg, str) and len(arg) > 1 and arg[0] in '+-')]

        # Parse arguments
        file_patterns = []
        action = 'sync'  # default action
        make_file = None
        rmtemp_file = None

        for i, arg in enumerate(theArgs):
            if arg in ['list', 'ls']:
                action = 'list'
            elif arg in ['status', 'stat']:
                action = 'status'
            elif arg == 'sync':
                action = 'sync'
            elif arg == 'make':
                action = 'make'
                # Next argument should be the file to make template from
                if i + 1 < len(theArgs):
                    make_file = theArgs[i + 1]
                    # Skip the next argument since we consumed it
                    theArgs = theArgs[:i+1] + theArgs[i+2:]
                    break
            elif arg == 'rmTemp':
                action = 'rmTemp'
                # Next argument should be the file to remove template for
                if i + 1 < len(theArgs):
                    rmtemp_file = theArgs[i + 1]
                    # Skip the next argument since we consumed it
                    theArgs = theArgs[:i+1] + theArgs[i+2:]
                    break
            else:
                file_patterns.append(arg)

        # Execute based on action
        if action == 'list':
            syncer.list_tracked_files()
        elif action == 'status':
            syncer.show_status()
        elif action == 'make':
            if not make_file:
                printIt("Error: 'make' action requires a filename", lable.ERROR)
                printIt("Usage: ${packName} sync make <filename>", lable.INFO)
                printIt("Example: ${packName} sync make tests/test_setLogPref_roundtrip.py", lable.INFO)
                return
            
            success = syncer.make_template_from_file(make_file)
            if success:
                printIt("Template file created successfully", lable.PASS)
            else:
                printIt("Template file creation failed", lable.ERROR)
                import sys
                sys.exit(1)
        elif action == 'rmTemp':
            if not rmtemp_file:
                printIt("Error: 'rmTemp' action requires a filename", lable.ERROR)
                printIt("Usage: ${packName} sync rmTemp <filename>", lable.INFO)
                printIt("Example: ${packName} sync rmTemp tests/test_setLogPref_roundtrip.py", lable.INFO)
                return
            
            success = syncer.remove_template_from_file(rmtemp_file)
            if success:
                printIt("Template removed successfully", lable.PASS)
            else:
                printIt("Template removal failed", lable.ERROR)
                import sys
                sys.exit(1)
        else:  # sync
            if file_patterns:
                printIt(
                    f"Generating templates for files matching patterns: {', '.join(file_patterns)}", lable.INFO)
            else:
                printIt(
                    "Generating templates for all modified tracked files...", lable.INFO)

            success = syncer.sync_all_files(
                file_patterns if file_patterns else None)

            if success:
                printIt("Template generation completed successfully", lable.PASS)
            else:
                printIt("Template generation completed with some errors", lable.WARN)


def sync(argParse):
    '''Entry point for sync command'''
    command_instance = syncCommand(argParse)
    command_instance.execute()
"""
    )
)

commandsJsonDict = {
    "switchFlags": {},
    "description": "Dictionary of commands, their discription and switches, and their argument discriptions.",
    "_globalSwitcheFlags": {},
    "newCmd": {
        "description": "Add new command <cmdName> with [argNames...]. Also creates a file cmdName.py.",
        "switchFlags": {},
        "cmdName": "Name of new command",
        "argName": "(argName...), Optional names of argument to associate with the new command.",
    },
    "modCmd": {
        "description": "Modify a command or argument descriptions, or add another argument for command. The cmdName.py file will not be modified.",
        "switchFlags": {},
        "cmdName": "Name of command being modified",
        "argName": "(argName...) Optional names of argument(s) to modify.",
    },
    "rmCmd": {
        "description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
        "switchFlags": {},
        "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
        "argName": "Optional names of argument to remove.",
    },
    "runTest": {
        "description": "Run test(s) in ./tests directory. Use 'listTests' to see available tests.",
        "switchFlags": {
            "verbose": {"description": "Verbose output flag", "type": "bool"},
            "stop": {"description": "Stop on failure flag", "type": "bool"},
            "summary": {"description": "Summary only flag", "type": "bool"},
        },
        "testName": "Optional name of specific test to run (without .py extension)",
        "listTests": "List all available tests in the tests directory",
    },
    "fileDiff": {
        "description": "Show the differnces between two files.",
        "origFile": "Original file name",
        "newFile": "New file name",
    },
    "sync": {
        "description": "Sync modified files to originating template file",
        "switchFlags": {
            "dry-run": {
                "description": "Show what would be synced without making changes",
                "type": "bool",
            },
            "force": {
                "description": "Force sync even if files appear to have user modifications",
                "type": "bool",
            },
            "backup": {
                "description": "Create backup files before syncing",
                "type": "bool",
            },
        },
        "filePattern": "Optional file patterns to sync (e.g., '*.py', 'commands/*')",
        "action": "Action to perform: 'sync' (default), 'list', 'status', 'make', 'rmTemp'",
    },
}

commandsFileStr = dedent(
    """import json, os
from copy import copy
import inspect

class Commands(object):
    def __init__(self) -> None:
        self.cmdFileDir = os.path.dirname(inspect.getfile(self.__class__))
        self.cmdFileName = os.path.join(self.cmdFileDir, "commands.json" )
        try:
            with open(self.cmdFileName, "r") as fr:
                rawJson = json.load(fr)
                self._switchFlags = {}
                try:
                    self._switchFlags["switchFlags"] = copy(rawJson["switchFlags"])
                    del rawJson["switchFlags"]
                except: self._switchFlags["switchFlags"] = {}
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
            if not aFile in ["commands.py", "__init__.py", "cmdOptSwitchboard.py", "cmdSwitchboard.py"]:
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
            if not aFile in ["commands.py", "__init__.py", "cmdOptSwitchboard.py", "cmdSwitchboard.py"]:
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
"""
)

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

argParseTemplate = Template(
    dedent(
        """import os, sys, argparse, shlex
from ..defs.logIt import color, cStr
from ..commands.commands import Commands

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
            switchFlag = theCmds.switchFlags["switchFlags"]
            for cmdName in commands:
                # Skip metadata entries that are not actual commands
                if cmdName in ["description", "_globalSwitcheFlags"] or not isinstance(commands[cmdName], dict):
                    continue

                needCmdDescription = True
                needArgDescription = True
                arguments = commands[cmdName]
                argumentsHelp += cStr(cmdName, color.YELLOW) + ': \\n'
                for argName in arguments:
                    if argName == "description":
                        cmdHelp = cStr(cmdName, color.YELLOW) + ': ' + f'{arguments[argName]}'
                        if len(cmdHelp) > tCols:
                            indentPad = len(cmdName) + 2
                            cmdHelp = formatHelpWidth(cmdHelp, tCols, indentPad)
                        else:
                            cmdHelp += '\\n'
                        commandsHelp += cmdHelp
                        needCmdDescription = False
                    elif argName not in ["switchFlags"]:
                        # Only process actual arguments, not metadata
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
                description = "Command Line Tool for creating and managing commands.",
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
        '''Extract command-specific options(--option and -option) from arguments'''
        # Get global switch flags to differentiate from command-specific flags
        theCmds = Commands()
        global_switch_flags = theCmds.switchFlags.get("switchFlags", {})                           

        filtered_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Handle help flags - only preserve for general help (when no command specified)
                if arg == '--help':
                    # If this is the first argument, it's general help (${packName} --help)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (${packName} command --help), don't pass to argparse
                        i += 1
                # Handle command-specific options with double hyphen
                elif '=' in arg:
                    # Handle --option=value format
                    option_name, option_value = arg[2:].split('=', 1)  # Remove -- and split on first =
                    self.cmd_options[option_name] = option_value
                    i += 1
                else:
                    option_name = arg[2:]  # Remove --
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        # Option with value
                        self.cmd_options[option_name] = args[i + 1]
                        i += 2  # Skip both option and value
                    else:
                        # Double hyphen option without value - still treat as string type
                        # Mark it specially so we know it's a string option during command creation
                        self.cmd_options[option_name] = '__STRING_OPTION__'
                        i += 1
            elif arg.startswith('-') and len(arg) > 1:
                # Handle single-hyphen options that might be command-specific
                # Check if this is a known global flag first
                option_name = arg[1:]
                
                # Handle help flags - only preserve for general help (when no command specified)
                if option_name in ['h']:
                    # If this is the first argument, it's general help (${packName} -h)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (${packName} command -h), don't pass to argparse
                        i += 1
                elif option_name in global_switch_flags:
                    # This is a global flag, let argparse handle it
                    filtered_args.append(arg)
                    i += 1
                else:
                    # This might be a command-specific flag, treat as such
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
"""
    )
)

logPrintTemplate = Template(
    dedent(
        """import os, time
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
        "STEP: ": MAGENTA,
        "IMPORT: ": UNDERLINE,
        "RESET": RESET,
        "File Not Found: ": YELLOW,
        "Directory Not Found: ": YELLOW,
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
        "Update: ": CYAN,
        "TODO: ": CYAN,
        "ABORTPRT": YELLOW,
        "Unknown PiSeedType: ": RED,
        "Incorect PiValue Path: ": RED
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
    STEP = "STEP: "
    IMPORT = "IMPORT: "
    RESET = "RESET"
    FileNotFound = "File Not Found: "
    DirNotFound = "Directory Not Found: "
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
    TODO = "TODO: "
    ABORTPRT = "ABORTPRT"
    UnknownPiSeedType = "Unknown PiSeedType: "
    IncorectPiValuePath = "Incorect PiValue Path: "

# log function
def logIt(*message, logFileName="${packName}.log"):
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

def printIt(*message, asStr: bool = False) -> str:
    prtStr = ""
    rtnStr = ""
    needClip = False
    abortPrt = False
    for mess in message:
        if mess == lable.ABORTPRT:
            abortPrt = True
    if not abortPrt:
        if len(message) > 0:
            for mess in message:
                if mess == lable.BLANK:
                    prtStr = message[0]
                    rtnStr = message[0]
                    needClip = False
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
        if not asStr:
            print(prtStr)
    return rtnStr

def cStr(inStr:str, cVal:str):
    return cVal + inStr + color.RESET

def deleteLog(logFileName="${packName}.log"):
    if os.path.isfile(logFileName): os.remove(logFileName)

def getCodeFile():
    cf = currentframe()
    codeObj = ''
    if cf:
        if cf.f_back: codeObj = cf.f_back.f_code
    if codeObj:
        codeObjStr = str(codeObj).split(",")[1].split('"')[1]
        codeObjStr = os.path.basename(codeObjStr)
    else:
        codeObjStr = 'file-no-found'
    return codeObjStr

def getCodeLine():
    cf = currentframe()
    codeObj = None
    if cf:
        if cf.f_back:
            codeObj = cf.f_back.f_code
    return codeObj

def germDbug(loc: str, currPi, nextPi):
    loc += currPi.piSeedKeyType
    if nextPi == None:
        print(loc, currPi.piSeedKeyDepth, nextPi)
        print("piType:", currPi.piType, nextPi)
        print("piTitle:", currPi.piTitle, nextPi)
        print("piSD:", currPi.piSD, nextPi)
    else:
        print(loc, currPi.piSeedKeyDepth, nextPi.piSeedKeyDepth)
        print("piType:", currPi.piType, nextPi.piType)
        print("piTitle:", currPi.piTitle, nextPi.piTitle)
        print("piSD:", currPi.piSD, nextPi.piSD)
    print("--------------------")

"""
    )
)

validationTemplate = Template(
    dedent(
        """\"\"\"
Validation utilities for command and argument names
\"\"\"
import keyword
import builtins
import os
from .logIt import printIt, lable

def is_python_keyword_or_builtin(name: str) -> bool:
    \"\"\"Check if a name is a Python keyword or built-in function/type\"\"\"
    return keyword.iskeyword(name) or hasattr(builtins, name)

def get_reserved_names() -> set:
    \"\"\"Get all reserved Python names that should not be used as function names\"\"\"
    reserved = set()
    
    # Add Python keywords
    reserved.update(keyword.kwlist)
    
    # Add built-in functions and types
    reserved.update(dir(builtins))
    
    # Add some common problematic names that might not be in builtins
    additional_reserved = {
        'exec', 'eval', 'compile', 'globals', 'locals', 'vars',
        'dir', 'help', 'input', 'print', 'open', 'file',
        'exit', 'quit', 'license', 'copyright', 'credits'
    }
    reserved.update(additional_reserved)
    
    return reserved

def validate_argument_name(arg_name: str, cmd_name: str | None = None) -> bool:
    \"\"\"
    Validate that an argument name is safe to use as a function name
    Returns True if valid, False if invalid
    \"\"\"
    if not arg_name:
        printIt("Argument name cannot be empty", lable.ERROR)
        return False
    
    # Check if it's a valid Python identifier
    if not arg_name.isidentifier():
        printIt(f"'{arg_name}' is not a valid Python identifier", lable.ERROR)
        return False
    
    # Check if it's a reserved name
    if is_python_keyword_or_builtin(arg_name):
        printIt(f"'{arg_name}' is a Python keyword or built-in name and cannot be used as a function name", lable.ERROR)
        return False
    
    return True

def check_command_uses_argcmddef_template(cmd_name: str) -> bool:
    \"\"\"Check if a command file was generated using argCmdDef template\"\"\"
    file_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to src/${packName}
    file_path = os.path.join(file_dir, 'commands', f'{cmd_name}.py')
    
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            return 'argCmdDef template' in first_line
    except Exception:
        return False

def validate_arguments_for_argcmddef(arg_names: list, cmd_name: str) -> list:
    \"\"\"
    Validate argument names for argCmdDef template usage
    Returns list of valid argument names, prints errors for invalid ones
    \"\"\"
    valid_args = []
    
    for arg_name in arg_names:
        if validate_argument_name(arg_name, cmd_name):
            valid_args.append(arg_name)
        else:
            printIt(f"Skipping invalid argument name: '{arg_name}'", lable.WARN)
    
    return valid_args"""
    )
)
