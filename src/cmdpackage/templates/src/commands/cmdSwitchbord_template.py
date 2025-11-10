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
from ..classes.optSwitches import saveCmdSwitchOptions, toggleCmdSwitchOption

cmdObj = Commands()
commands = cmdObj.commands
# Handle both old and new global switch structure
if hasattr(cmdObj, "switchFlags") and "switchFlags" in cmdObj.switchFlags:
    switchFlags = cmdObj.switchFlags["switchFlags"]
else:
    # Try new structure or fallback to empty
    switchFlags = cmdObj.switchFlags.get("option_switches", {})


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
    # Handle new structure with "arguments" or old structure with direct key-value pairs
    if "arguments" in cmdInfo:
        # New structure - get arguments from the "arguments" section
        for key, value in cmdInfo["arguments"].items():
            if isinstance(value, str):
                args.append(f"<{key}>")
    else:
        # Old structure - get arguments from direct key-value pairs
        for key, value in cmdInfo.items():
            if key not in ["description", "switchFlags", "option_switches", "option_strings"] and isinstance(
                value, str
            ):
                args.append(f"<{key}>")

    if args:
        usage_parts.extend(args)

    # Add option flags - handle both old and new structure
    flag_parts = []

    # Check new structure first
    option_switches = cmdInfo.get("option_switches", {})
    option_strings = cmdInfo.get("option_strings", {})

    # Add boolean switches
    for flagName in option_switches.keys():
        flag_parts.append(f"[+{flagName}|-{flagName}]")

    # Add string options
    for flagName in option_strings.keys():
        flag_parts.append(f"[--{flagName} <value>]")

    # Fallback to old structure if no new structure found
    if not option_switches and not option_strings:
        switchFlags = cmdInfo.get("switchFlags", {})
        if switchFlags:
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
        # Handle new structure with "arguments" or old structure
        if "arguments" in cmdInfo:
            # New structure - get arguments from the "arguments" section
            for key, value in cmdInfo["arguments"].items():
                if isinstance(value, str):
                    printIt(f"  {cStr(f'<{key}>', color.WHITE)}  {value}", lable.INFO)
        else:
            # Old structure - get arguments from direct key-value pairs
            for key, value in cmdInfo.items():
                if key not in ["description", "switchFlags", "option_switches", "option_strings"] and isinstance(
                    value, str
                ):
                    printIt(f"  {cStr(f'<{key}>', color.WHITE)}  {value}", lable.INFO)
        print()  # Extra line

    # Print option flags section - handle both old and new structure
    has_options = bool(
        option_switches
        or option_strings
        or (not option_switches and not option_strings and cmdInfo.get("switchFlags", {}))
    )

    if has_options:
        printIt(f"{cStr('Option Flags:', color.CYAN)}", lable.INFO)

        # Handle new structure first
        # Boolean switches
        for flagName, flagDesc in option_switches.items():
            printIt(
                f"  {cStr(f'+{flagName}', color.GREEN)}   Enable: {flagDesc}",
                lable.INFO,
            )
            printIt(
                f"  {cStr(f'-{flagName}', color.RED)}   Disable: {flagDesc}",
                lable.INFO,
            )

        # String options
        for flagName, flagDesc in option_strings.items():
            printIt(
                f"  {cStr(f'--{flagName}', color.YELLOW)} <value>  {flagDesc}",
                lable.INFO,
            )

        # Fallback to old structure if no new structure found
        if not option_switches and not option_strings:
            switchFlags = cmdInfo.get("switchFlags", {})
            if switchFlags:
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
    if has_options:
        printIt(f"{cStr('Examples:', color.CYAN)}", lable.INFO)
        example_parts = [f"${packName} {cmdName}"]
        if args:
            example_parts.append("arg1")

        # Show flag examples - handle both old and new structure
        bool_flags = list(option_switches.keys()) if option_switches else []
        str_flags = list(option_strings.keys()) if option_strings else []

        # Fallback to old structure
        if not bool_flags and not str_flags:
            switchFlags = cmdInfo.get("switchFlags", {})
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


def cmdSwitchbord(argParse: ArgParse):
    global commands
    theCmd = "notSet"
    flag_toggle_occurred = False  # Track if a flag toggle happened
    try:
        if len(sys.argv) > 1:
            # Handle direct help flags like '${packName} -h'
            if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
                printIt("Global Help:", lable.INFO)
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
                        if cmdName in commands:
                            cmd_info = commands[cmdName]

                            # Check new structure first
                            option_switches = cmd_info.get("option_switches", {})
                            if flagName in option_switches:
                                # This is a command-specific boolean flag in new structure
                                setValue = arg[0] == "+"
                                toggleCmdSwitchOption(cmdName, flagName, setValue)
                                flag_toggle_occurred = True
                            # Fallback to old structure
                            elif "switchFlags" in cmd_info:
                                cmdswitchFlags = cmd_info["switchFlags"]
                                if flagName in cmdswitchFlags and cmdswitchFlags[flagName].get("type") == "bool":
                                    # This is a command-specific boolean flag in old structure
                                    setValue = arg[0] == "+"
                                    toggleCmdSwitchOption(cmdName, flagName, setValue)
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
                        if cmdName in commands:
                            cmd_info = commands[cmdName]

                            # Check new structure first
                            option_switches = cmd_info.get("option_switches", {})
                            if flagName in option_switches:
                                # This is a command-specific boolean flag in new structure
                                setValue = swtcFlagChk[0] == "+"
                                toggleCmdSwitchOption(cmdName, flagName, setValue)
                                flag_toggle_occurred = True
                                # Don't exit here - let the command execute with the new flag setting
                            # Fallback to old structure
                            elif "switchFlags" in cmd_info:
                                cmdswitchFlags = cmd_info["switchFlags"]
                                if flagName in cmdswitchFlags and cmdswitchFlags[flagName].get("type") == "bool":
                                    # This is a command-specific boolean flag in old structure
                                    setValue = swtcFlagChk[0] == "+"
                                    toggleCmdSwitchOption(cmdName, flagName, setValue)
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
                    printIt(f"no argument(s) entered for {theCmd}", lable.INFO)
        else:
            argParse.parser.print_help()
    except Exception as e:
        tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f"{theCmd}\\n{tb_str}", lable.ERROR)
        exit()
"""))

