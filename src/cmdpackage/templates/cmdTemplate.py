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

cmdSwitchbordFile = Template(dedent("""import sys, traceback
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
"""))

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
""")
)

modCmdTemplate = Template(dedent("""import os, copy, json, re
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
""")
)

runTestTemplate = Template(dedent("""# Generated using argCmdDef template
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
"""))

fileDiffTemplate = Template(dedent("""import sys
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
        return None"""))

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
    "description": "Modify a command or argument descriptions, or add another argument for command. The cmdName.py file will not be modified.",
    "switchFlags": {},
    "cmdName": "Name of command being modified",
    "argName": "(argName...) Optional names of argument(s) to modify."
  },
  "rmCmd": {
    "description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
    "switchFlags": {},
    "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
    "argName": "Optional names of argument to remove."
  },
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
  },
  "fileDiff": {
    "description": "Show the differnces between two files.",
    "origFile": "Original file name",
    "newFile": "New file name"
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

validationTemplate = Template(dedent("""\"\"\"
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
    
    return valid_args"""))
