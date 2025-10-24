#!/usr/bin/python
# -*- coding: utf-8 -*-
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
    usage_parts = [f"tc {cmdName}"]
    
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
        example_parts = [f"tc {cmdName}"]
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
            printIt(f"  tc {cmdName} -{bool_flags[0]}  # Disable {bool_flags[0]} flag", lable.INFO)

def cmdSwitchbord(argParse: ArgParse):
    global commands
    theCmd = 'notSet'
    flag_toggle_occurred = False  # Track if a flag toggle happened
    try:
        if len(sys.argv) > 1:
            # Handle direct help flags like 'tc -h'
            if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
                argParse.parser.print_help()
                exit()
            
            if len(sys.argv) > 2:
                # Handle command-specific help: tc command -h or tc command --help
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
                
                # Handle old logic for backward compatibility
                switchFlagChk = sys.argv[2]
                # Only handle single hyphen options here, let double hyphen pass through
                if len(sys.argv) == 3 and switchFlagChk[0] in '-+?' and not switchFlagChk.startswith('--'):
                    flagName = switchFlagChk[1:]
                    
                    # Check if it's a global switch flag first
                    if flagName in switchFlags.keys():
                        cmdOptSwitchbord(switchFlagChk, switchFlags)
                    
                    # Check if it's a command-specific flag
                    cmdName = sys.argv[1]
                    if cmdName in commands and 'switchFlags' in commands[cmdName]:
                        cmdSwitchFlags = commands[cmdName]['switchFlags']
                        if flagName in cmdSwitchFlags and cmdSwitchFlags[flagName].get('type') == 'bool':
                            # This is a command-specific boolean flag
                            setValue = switchFlagChk[0] == '+'
                            toggleCmdSwitchFlag(cmdName, flagName, setValue)
                            flag_toggle_occurred = True
                            exit()
                    
                    # Not a recognized flag
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
""")
cmdOptSwitchbordFileStr = dedent("""from ..classes.optSwitches import OptSwitches

def cmdOptSwitchbord(switchFlag: str, switchFlags: dict):
    optSwitches = OptSwitches(switchFlags)
    optSwitches.toggleSwitchFlag(switchFlag)
""")
argCmdDefTemplateStr = dedent("""# Generated using argCmdDef template
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

""")
argDefTemplateStr = dedent("""def ${argName}(argParse):
    args = argParse.args
    printIt("def ${defName} executed.", lable.INFO)
    printIt("Modify default behavour in src/${packName}/commands/${defName}.py", lable.INFO)
    printIt(str(args), lable.INFO)

""")
asyncDefTemplateStr = dedent("""# Generated using asyncDef template
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

""")
classCallTemplateStr = dedent("""# Generated using classCall template
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


""")
simpleTemplateStr = dedent("""# Generated using simple template
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


""")
newCmdTemplate = Template(dedent("""import os, sys, copy
import importlib
import readline
from json import dumps
from ..defs.logIt import printIt, lable
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
        
        theArgs = verifyArgsWithDiscriptions(cmdObj, combined_args)
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

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
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
""")
)
modCmdTemplate = Template(dedent("""import os, copy, json, re
from ..defs.logIt import printIt, lable
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

        theArgs = verifyArgsWithDiscriptions(cmdObj, combined_args)
        if len(theArgs.keys()) > 0:
            updateCMDJson(cmdObj, modCmdName, theArgs)
            
            # Save new option flags to .${packName}rc if any were added
            if hasattr(argParse, 'cmd_options') and argParse.cmd_options:
                # Extract flags for the command being modified
                new_cmd_flags = {}
                new_cmd_switch_flags = {}
                
                for option_name, option_value in argParse.cmd_options.items():
                    if isinstance(option_value, bool):
                        # Boolean flag - save with default value False
                        new_cmd_flags[option_name] = False
                        new_cmd_switch_flags[option_name] = {"type": "bool"}
                    elif option_value == '__STRING_OPTION__' or not isinstance(option_value, bool):
                        # String option - save with empty string default or the provided value
                        if option_value == '__STRING_OPTION__':
                            new_cmd_flags[option_name] = ""
                        else:
                            new_cmd_flags[option_name] = str(option_value)
                        new_cmd_switch_flags[option_name] = {"type": "str"}

                # Save the flags if any were found
                if new_cmd_flags:
                    saveCmdSwitchFlags(modCmdName, new_cmd_flags, new_cmd_switch_flags)

            printIt(f'"{modCmdName}" modified.',lable.ModCmd)
        else:
            printIt(f'"{modCmdName}" unchanged.',lable.INFO)
    else:
        printIt(f'"{modCmdName}" does not exists. use newCmd or add it.',lable.INFO)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    optionFlags = {}
    saveDict = False
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
            theDict = ''
            if argIndex == 0 and len(theArgs) == 1:
                chgDisc = input(f'Replace description for {argName} (y/N): ')
                if chgDisc.lower() == 'y':
                    saveDict = True
            elif argIndex > 0:
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
            
            if saveDict:
                # only populate rtnDict with modified descriptions
                rtnDict[argName] = theDict
            
        argIndex += 1
    
    # Store option flags separately for later processing
    rtnDict['_optionFlags'] = optionFlags
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
""")
)
rmCmdTemplate = Template(dedent("""import os, json
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
""")
)
commandsJsonDict = {
  "switchFlags": {},
  "description": "Dictionary of commands, their discription and switches, and their argument discriptions.",
  "_globalSwitcheFlags": {},
  "newCmd": {
    "description": "Add new command <cmdName> with [argNames...]. Also creates a file cmdName.py.",
    "switchFlags": {},
    "cmdName": "Name of new command",
    "argName": "(argName...), Optional names of argument to associate with the new command."
  },
  "modCmd": {
    "description": "Modify a command or argument discriptions, or add another argument for command. The cmdName.py file will not be modified.",
    "switchFlags": {},
    "cmdName": "Name of command being modified",
    "argName": "(argName...) Optional names of argument(s) to modify."
  },
  "rmCmd": {
    "description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
    "switchFlags": {},
    "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
    "argName": "Optional names of argument to remove."
  }
}
commandsFileStr = dedent("""import json, os
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
""")
optSwitchesTemplate = Template(dedent("""import json
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
"""))
argParseTemplate = Template(dedent("""import os, sys, argparse, shlex
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
                    # If this is the first argument, it's general help (tc --help)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (tc command --help), don't pass to argparse
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
                    # If this is the first argument, it's general help (tc -h)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (tc command -h), don't pass to argparse
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

"""))