#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

argParse_template = Template(dedent("""import os, sys, argparse, shlex
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
                added_indent = "x" * indent_chg
                print("added_indent", added_indent)
                invocations.append(added_indent + get_invocation(subaction))
            # print('inv', invocations)

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length, action_length)

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


class ArgParse:

    def __init__(self):
        # Parse command-specific options (double hyphen) before main parsing
        self.cmd_options = {}
        self.filtered_args = self._extract_cmd_options(sys.argv[1:])
        if not sys.stdin.isatty():
            self.parser = argparse.ArgumentParser(add_help=False)
            self.parser.add_argument("commands", nargs=1)
            self.parser.add_argument("arguments", nargs="*")
            self.args = self.parser.parse_args(self.filtered_args)
        else:
            _, tCols = os.popen("stty size", "r").read().split()
            tCols = int(tCols)
            indentPad = 8
            formatter_class = lambda prog: PiHelpFormatter(prog, max_help_position=8, width=tCols)
            commandsHelp = ""
            argumentsHelp = ""
            theCmds = Commands()
            commands = theCmds.commands
            swtcFlag = theCmds.switchFlags["switchFlags"]
            for cmdName in commands:
                # Skip metadata entries that are not actual commands
                if cmdName in ["description", "_globalSwtceFlags"] or not isinstance(commands[cmdName], dict):
                    continue

                needCmdDescription = True
                needArgDescription = True
                command_info = commands[cmdName]
                argumentsHelp += cStr(cmdName, color.YELLOW) + ": \\n"

                # Handle new structure vs old structure
                if "arguments" in command_info:
                    # New structure - arguments are under "arguments" key
                    arguments = command_info["arguments"]
                    # Get description from description field
                    if "description" in command_info:
                        cmdHelp = cStr(cmdName, color.YELLOW) + ": " + f"{command_info['description']}"
                        if len(cmdHelp) > tCols:
                            indentPad = len(cmdName) + 2
                            cmdHelp = formatHelpWidth(cmdHelp, tCols, indentPad)
                        else:
                            cmdHelp += "\\n"
                        commandsHelp += cmdHelp
                        needCmdDescription = False

                    # Process arguments
                    for argName, argDesc in arguments.items():
                        argHelp = cStr(f"  <{argName}> ", color.CYAN) + f"{argDesc}"
                        if len(argHelp) > tCols:
                            indentPad = len(argName) + 5
                            argHelp = " " + formatHelpWidth(argHelp, tCols, indentPad)
                        else:
                            argHelp += "\\n"
                        argumentsHelp += argHelp
                        needArgDescription = False
                else:
                    # Old structure - iterate through all keys and filter out metadata
                    for argName in command_info:
                        if argName == "description":
                            cmdHelp = cStr(cmdName, color.YELLOW) + ": " + f"{command_info[argName]}"
                            if len(cmdHelp) > tCols:
                                indentPad = len(cmdName) + 2
                                cmdHelp = formatHelpWidth(cmdHelp, tCols, indentPad)
                            else:
                                cmdHelp += "\\n"
                            commandsHelp += cmdHelp
                            needCmdDescription = False
                        elif argName not in ["switchFlags", "option_switches", "option_strings"]:
                            # Only process actual arguments, not metadata
                            argHelp = cStr(f"  <{argName}> ", color.CYAN) + f"{command_info[argName]}"
                            if len(argHelp) > tCols:
                                indentPad = len(argName) + 5
                                argHelp = " " + formatHelpWidth(argHelp, tCols, indentPad)
                            else:
                                argHelp += "\\n"
                            argumentsHelp += argHelp
                            needArgDescription = False
                if needArgDescription:
                    argumentsHelp = argumentsHelp[:-1]
                    argumentsHelp += "no arguments\\n"
                if needCmdDescription:
                    commandsHelp += cStr(cmdName, color.WHITE) + "\\n"
            #   commandsHelp = commandsHelp[:-1]

            self.parser = argparse.ArgumentParser(
                description="Command Line Tool for creating and managing commands.",
                epilog="Have Fun!",
                formatter_class=formatter_class,
            )

            self.parser.add_argument(
                "commands",
                type=str,
                nargs=1,
                metavar=f'{cStr(cStr("Commands", color.YELLOW), color.UNDERLINE)}:',
                help=commandsHelp,
            )

            self.parser.add_argument(
                "arguments",
                type=str_or_int,
                nargs="*",
                metavar=f'{cStr(cStr("Arguments", color.CYAN), color.UNDERLINE)}:',
                # metavar="arguments:",
                help=argumentsHelp,
            )

            for optFlag in swtcFlag:
                flagHelp = swtcFlag[optFlag]
                self.parser.add_argument(f"-{optFlag}", action="store_true", help=flagHelp)
            self.args = self.parser.parse_args(self.filtered_args)

    def _extract_cmd_options(self, args):
        \"\"\"Extract command-specific options(--option and -option) from arguments\"\"\"
        # Get global swtc flags to differentiate from command-specific flags
        theCmds = Commands()
        global_swtc_flags = theCmds.switchFlags.get("switchFlags", {})

        filtered_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                # Handle help flags - only preserve for general help (when no command specified)
                if arg == "--help":
                    # If this is the first argument, it's general help (${packName} --help)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (${packName} command --help), don't pass to argparse
                        i += 1
                # Handle command-specific options with double hyphen
                elif "=" in arg:
                    # Handle --option=value format
                    option_name, option_value = arg[2:].split("=", 1)  # Remove -- and split on first =
                    self.cmd_options[option_name] = option_value
                    i += 1
                else:
                    option_name = arg[2:]  # Remove --
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
                        # Option with value
                        self.cmd_options[option_name] = args[i + 1]
                        i += 2  # Skip both option and value
                    else:
                        # Double hyphen option without value - still treat as string type
                        # Mark it specially so we know it's a string option during command creation
                        self.cmd_options[option_name] = "__STRING_OPTION__"
                        i += 1
            elif (arg.startswith("-") or arg.startswith("+")) and len(arg) > 1:
                # Handle single-hyphen and plus-sign options that might be command-specific
                # Pi system uses unconventional persistence storage: -flag=OFF, +flag=ON
                # Check if this is a known global flag first
                is_plus_flag = arg.startswith("+")
                option_name = arg[1:]  # Remove - or +

                # Handle help flags - only preserve for general help (when no command specified)
                if option_name in ["h"]:
                    # If this is the first argument, it's general help (${packName} -h)
                    if i == 0:
                        filtered_args.append(arg)
                        i += 1
                    else:
                        # This is command-specific help (${packName} command -h), don't pass to argparse
                        i += 1
                elif option_name in global_swtc_flags:
                    # This is a global flag, let argparse handle it
                    filtered_args.append(arg)
                    i += 1
                else:
                    # This might be a command-specific flag, treat as such
                    # Pi system: -flag=False (OFF), +flag=True (ON)
                    self.cmd_options[option_name] = True if is_plus_flag else False
                    i += 1
            else:
                filtered_args.append(arg)
                i += 1
        return filtered_args


def formatHelpWidth(theText, tCols, indentPad=1) -> str:
    # this uses the screen with to estabhish tCols

    # tCols = int(tCols) - 20
    # print(tCols)
    # tCols = 60
    spPaddingStr = " " * indentPad
    rtnStr = ""
    outLine = ""
    tokens = shlex.split(theText)
    # print(tokens)
    # exit()
    for token in tokens:  # loop though tokens
        chkStr = outLine + token + " "
        if len(chkStr) <= tCols:  # check line length after concatinating each word
            outLine = chkStr  # less the the colums of copy over to outline
        else:
            if len(token) > tCols:
                # when the mtc word is longer then the terminal character width (tCols),
                # DEBUG how it should be handeled here.
                # Temporarily comment out debug code
                # print(f"here with long mtc.group():\\n{token}")
                # exit()
                chkStr = token
                while len(chkStr) > tCols:  # a single word may be larger the tCols
                    outLine += chkStr[:tCols]
                    chkStr = f"\\n{chkStr[tCols:]}"
                outLine += chkStr
            else:
                rtnStr += outLine
                outLine = f"\\n{spPaddingStr}{token} "
    rtnStr += f"{outLine}\\n"
    # rtnStr = rtnStr[:-1]
    return rtnStr
"""))

