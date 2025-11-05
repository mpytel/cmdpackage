#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

cmdSwitchbord_template = Template(dedent("""import sys, traceback
from argparse import Namespace
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands
from .cmdOptSwitchbord import cmdOptSwitchbord
from ..classes.argParse import ArgParse
from ..classes.optSwitches import saveCmdswitchFlags, toggleCmdSwtcFlag

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
    description = cmdInfo.get("description", "No description available")
    printIt(f"\\n{cStr(cmdName, color.YELLOW)}: {description}\\n", lable.INFO)

    # Build usage line
    usage_parts = [f"${packName} {cmdName}"]

    # Add arguments
    args = []
    for key, value in cmdInfo.items():
        if key not in ["description", "switchFlags"] and isinstance(value, str):
            args.append(f"<{key}>")

    if args:
        usage_parts.extend(args)

    # Add option flags
    switchFlags = cmdInfo.get("switchFlags", {})
    if switchFlags:
        flag_parts = []
        for flagName, flagInfo in switchFlags.items():
            if flagInfo.get("type") == "bool":
                flag_parts.append(f"[+{flagName}|-{flagName}]")
            elif flagInfo.get("type") == "str":
                flag_parts.append(f"[--{flagName} <value>]")
        usage_parts.extend(flag_parts)

    # Print usage
    usage = " ".join(usage_parts)
    printIt(f"{cStr('Usage:', color.CYAN)} {usage}\\n", lable.INFO)

    # Print arguments section
    if args:
        printIt(f"{cStr('Arguments:', color.CYAN)}", lable.INFO)
        for key, value in cmdInfo.items():
            if key not in ["description", "switchFlags"] and isinstance(value, str):
                printIt(f"  {cStr(f'<{key}>', color.WHITE)}  {value}", lable.INFO)
        print()  # Extra line

    # Print option flags section
    if switchFlags:
        printIt(f"{cStr('Option Flags:', color.CYAN)}", lable.INFO)
        for flagName, flagInfo in switchFlags.items():
            flagType = flagInfo.get("type", "unknown")
            flagDesc = flagInfo.get("description", "No description")

            if flagType == "bool":
                printIt(
                    f"  {cStr(f'+{flagName}', color.GREEN)}   Enable: {flagDesc}",
                    lable.INFO,
                )
                printIt(
                    f"  {cStr(f'-{flagName}', color.RED)}   Disable: {flagDesc}",
                    lable.INFO,
                )
            elif flagType == "str":
                printIt(
                    f"  {cStr(f'--{flagName}', color.YELLOW)} <value>  {flagDesc}",
                    lable.INFO,
                )
        print()  # Extra line

    # Print examples if the command has flags
    if switchFlags:
        printIt(f"{cStr('Examples:', color.CYAN)}", lable.INFO)
        example_parts = [f"${packName} {cmdName}"]
        if args:
            example_parts.append("arg1")

        # Show flag examples
        bool_flags = [name for name, info in switchFlags.items() if info.get("type") == "bool"]
        str_flags = [name for name, info in switchFlags.items() if info.get("type") == "str"]

        if str_flags:
            example_parts.append(f"--{str_flags[0]} value")
        if bool_flags:
            example_parts.append(f"+{bool_flags[0]}")

        printIt(f"  {' '.join(example_parts)}", lable.INFO)

        if bool_flags:
            printIt(
                f"  ${packName} {cmdName} -{bool_flags[0]}  # Disable {bool_flags[0]} flag",
                lable.INFO,
            )


def cmdSwitcbord(argParse: ArgParse):
    global commands
    theCmd = "notSet"
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
                    if arg[0] in "-+?" and not arg.startswith("--") and len(arg) > 1:
                        flagName = arg[1:]

                        # Check if it's a global swtc flag first
                        if flagName in switchFlags.keys():
                            cmdOptSwitchbord(arg, switchFlags)

                        # Check if it's a command-specific flag
                        if cmdName in commands and "switchFlags" in commands[cmdName]:
                            cmdswitchFlags = commands[cmdName]["switchFlags"]
                            if flagName in cmdswitchFlags and cmdswitchFlags[flagName].get("type") == "bool":
                                # This is a command-specific boolean flag
                                setValue = arg[0] == "+"
                                toggleCmdSwtcFlag(cmdName, flagName, setValue)
                                flag_toggle_occurred = True

                # Handle old logic for backward compatibility only if flag toggle didn't occur above
                if not flag_toggle_occurred:
                    swtcFlagChk = sys.argv[2]
                    # Only handle single hyphen options here, let double hyphen pass through
                    if len(sys.argv) == 3 and swtcFlagChk[0] in "-+?" and not swtcFlagChk.startswith("--"):
                        flagName = swtcFlagChk[1:]

                        # Check if it's a global swtc flag first
                        if flagName in switchFlags.keys():
                            cmdOptSwitchbord(swtcFlagChk, switchFlags)
                            exit()

                        # Check if it's a command-specific flag
                        cmdName = sys.argv[1]
                        if cmdName in commands and "switchFlags" in commands[cmdName]:
                            cmdswitchFlags = commands[cmdName]["switchFlags"]
                            if flagName in cmdswitchFlags and cmdswitchFlags[flagName].get("type") == "bool":
                                # This is a command-specific boolean flag
                                setValue = swtcFlagChk[0] == "+"
                                toggleCmdSwtcFlag(cmdName, flagName, setValue)
                                flag_toggle_occurred = True
                                # Don't exit here - let the command execute with the new flag setting

                        # Not a recognized flag
                        if not flag_toggle_occurred:
                            if swtcFlagChk not in ["-h", "--help"]:
                                printIt(f"{swtcFlagChk} not defined", lable.WARN)
                            else:
                                argParse.parser.print_help()
                            exit()

            args: Namespace = argParse.args
            theCmd = args.commands[0]
            if theCmd in commands.keys():
                # Save command-specific swtc flags before executing command
                # Skip if a flag toggle already occurred to avoid overwriting the toggle
                if hasattr(argParse, "cmd_options") and argParse.cmd_options and not flag_toggle_occurred:
                    cmdswitchFlags = commands[theCmd].get("switchFlags", {})
                    if cmdswitchFlags:
                        saveCmdswitchFlags(theCmd, argParse.cmd_options, cmdswitchFlags)

                exec(f"from ..commands.{theCmd} import {theCmd}")
                exec(f"{theCmd}(argParse)")
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
        tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f"{theCmd}\\n{tb_str}", lable.ERROR)
        exit()
"""))

