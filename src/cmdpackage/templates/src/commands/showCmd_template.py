#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

showCmd_template = Template(dedent("""# Generated using argCmdDef template
import os
import json
from ..defs.logIt import printIt, lable, cStr, color
from ..defs.utilities import format_wrapped_text
from .commands import Commands

commandJsonDict = {
    "showCmd": {
        "description": "Show meta data about a command.",
        "option_switches": {},
        "option_strings": {},
        "arguments": {
            "classCall": "The template used to first create the command.thed template used for this command."
        },
    }
}


def load_sync_data():
    \"\"\"Load metadata from genTempSyncData.json\"\"\"
    try:
        # Get project root directory
        current_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        sync_data_file = os.path.join(project_root, "genTempSyncData.json")

        if os.path.exists(sync_data_file):
            with open(sync_data_file, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        printIt(f"Warning: Could not load sync data: {e}", lable.WARN)
        return {}


def get_command_file_path(cmd_name):
    \"\"\"Get the file path for a command\"\"\"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, f"{cmd_name}.py")


def get_template_info(cmd_name, sync_data):
    \"\"\"Extract template information for a command from sync data\"\"\"
    cmd_file_path = get_command_file_path(cmd_name)
    abs_cmd_path = os.path.abspath(cmd_file_path)

    if abs_cmd_path in sync_data:
        file_info = sync_data[abs_cmd_path]
        return {
            "template": file_info.get("template", "Unknown"),
            "template_file": file_info.get("tempFileName", "Unknown"),
            "file_md5": file_info.get("fileMD5", "Unknown"),
            "exists": os.path.exists(cmd_file_path),
        }
    else:
        return {
            "template": "Not tracked in sync data",
            "template_file": "Unknown",
            "file_md5": "Unknown",
            "exists": os.path.exists(cmd_file_path),
        }


def show_command_metadata(cmd_name):
    \"\"\"Show comprehensive metadata about a command\"\"\"
    cmdObj = Commands()
    commands = cmdObj.commands
    sync_data = load_sync_data()

    header_text = f" Command Metadata: {cmd_name} "
    printIt("-" * 10, cStr(header_text, color.BLUE), "-" * (80 - 10 - len(header_text)), lable.INFO)

    if cmd_name not in commands:
        printIt(f"Command '{cmd_name}' not found in commands registry", lable.ERROR)
        return

    # Basic command info from commands.json
    cmd_info = commands[cmd_name]
    description_text = format_wrapped_text(
        f"{cStr('Description:', color.GREEN)}", cmd_info.get("description", "No description")
    )
    printIt(description_text, lable.INFO)

    # Show option switches
    option_switches = cmd_info.get("option_switches", {})
    if option_switches:
        printIt(f"{cStr('Option Switches:', color.GREEN)}", lable.INFO)
        for switch, switch_desc in option_switches.items():
            switch_text = format_wrapped_text(f"  • +{switch}/-{switch}:", switch_desc)
            printIt(switch_text, lable.INFO)

    # Show option strings
    option_strings = cmd_info.get("option_strings", {})
    if option_strings:
        printIt(f"{cStr('Option Strings:', color.GREEN)}", lable.INFO)
        for option, option_desc in option_strings.items():
            option_text = format_wrapped_text(f"  • --{option}:", option_desc)
            printIt(option_text, lable.INFO)

    # Show arguments
    arguments = cmd_info.get("arguments", {})
    if arguments:
        printIt(f"{cStr('Arguments:', color.GREEN)}", lable.INFO)
        for arg, arg_desc in arguments.items():
            arg_text = format_wrapped_text(f"  • {arg}:", arg_desc)
            printIt(arg_text, lable.INFO)

    # Show legacy switch flags (if they exist)
    switch_flags = cmd_info.get("switchFlags", {})
    if switch_flags:
        printIt(f"{cStr('Legacy Switch Flags:', color.GREEN)}", lable.INFO)
        for flag, flag_info in switch_flags.items():
            flag_type = flag_info.get("type", "unknown")
            flag_desc = flag_info.get("description", "No description")
            printIt(f"  • -{flag} ({flag_type}): {flag_desc}", lable.INFO)

    # Template and file information from sync data
    template_info = get_template_info(cmd_name, sync_data)

    # Check if file is untracked (not in sync data)
    cmd_file = get_command_file_path(cmd_name)
    abs_cmd_path = os.path.abspath(cmd_file)
    is_untracked = abs_cmd_path not in sync_data

    # Check if file is modified (tracked but MD5 doesn't match)
    is_modified = False
    if not is_untracked and template_info["exists"] and abs_cmd_path in sync_data:
        try:
            import hashlib

            with open(abs_cmd_path, "rb") as f:
                current_md5 = hashlib.md5(f.read()).hexdigest()
            stored_md5 = sync_data[abs_cmd_path].get("fileMD5", "")
            is_modified = current_md5 != stored_md5
        except Exception:
            pass

    # Show file status in Template Status section
    if is_untracked and template_info["exists"] or is_modified:
        printIt(f"{cStr('Template Status:', color.GREEN)}", lable.INFO)
        if is_untracked and template_info["exists"]:
            printIt(f"  • {cStr('UNTRACKED', color.CYAN)} {os.path.relpath(cmd_file)}", lable.INFO)
        elif is_modified:
            printIt(f"  • {cStr('MODIFIED', color.YELLOW)} {os.path.relpath(cmd_file)}", lable.INFO)

    printIt(f"{cStr('File Information:', color.GREEN)}", lable.INFO)
    printIt(f"  • Template: {template_info['template']}", lable.INFO)
    printIt(f"  • Template File: {os.path.basename(template_info['template_file'])}", lable.INFO)
    printIt(
        (
            f"  • File MD5: {template_info['file_md5'][:12]}..."
            if len(template_info["file_md5"]) > 12
            else f"  • File MD5: {template_info['file_md5']}"
        ),
        lable.INFO,
    )
    printIt(f"  • File Exists: {'Yes' if template_info['exists'] else 'No'}", lable.INFO)

    # Show file path
    printIt(f"  • File Path: {os.path.relpath(cmd_file)}", lable.INFO)

    # Special handling for tmplMgt command - show template status
    if cmd_name == "tmplMgt":
        show_tmplmgt_status_info()


def show_tmplmgt_status_info():
    \"\"\"Show template management status information\"\"\"
    try:
        # Get project root directory
        current_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        sync_data_file = os.path.join(project_root, "genTempSyncData.json")

        if not os.path.exists(sync_data_file):
            printIt(f"{cStr('Template Status:', color.GREEN)} No genTempSyncData.json found", lable.INFO)
            return

        with open(sync_data_file, "r") as f:
            sync_data = json.load(f)

        # Count file status
        total_files = 0
        ok_files = 0
        modified_files = 0
        missing_files = 0
        modified_list = []

        for file_path, file_info in sync_data.items():
            if file_path == "fields" or not isinstance(file_info, dict):
                continue

            total_files += 1

            if os.path.exists(file_path):
                try:
                    import hashlib

                    with open(file_path, "rb") as f:
                        current_md5 = hashlib.md5(f.read()).hexdigest()
                    stored_md5 = file_info.get("fileMD5", "")

                    if current_md5 == stored_md5:
                        ok_files += 1
                    else:
                        modified_files += 1
                        rel_path = os.path.relpath(file_path, project_root)
                        modified_list.append(rel_path)
                except Exception:
                    modified_files += 1
            else:
                missing_files += 1

        printIt(f"{cStr('Template Status:', color.GREEN)}", lable.INFO)
        printIt(f"  • Total tracked files: {total_files}", lable.INFO)
        printIt(f"  • Files in sync: {ok_files}", lable.INFO)
        if modified_files > 0:
            printIt(f"  • Modified files: {modified_files}", lable.INFO)
            if len(modified_list) <= 5:  # Show up to 5 modified files
                for mod_file in modified_list:
                    printIt(f"    - {mod_file}", lable.INFO)
            elif len(modified_list) > 5:
                for mod_file in modified_list[:3]:
                    printIt(f"    - {mod_file}", lable.INFO)
                printIt(f"    ... and {len(modified_list) - 3} more files", lable.INFO)
        if missing_files > 0:
            printIt(f"  • Missing files: {missing_files}", lable.INFO)

        # Show sync data file info
        printIt(f"  • Sync data: {os.path.basename(sync_data_file)}", lable.INFO)

    except Exception as e:
        printIt(f"{cStr('Template Status:', color.GREEN)} Error reading status ({str(e)[:50]}...)", lable.INFO)


def showCmd(argParse):
    \"\"\"Main showCmd function\"\"\"
    args = argParse.args
    theArgs = args.arguments

    if len(theArgs) == 0:
        printIt("No command specified. Usage: ${packName} showCmd <command_name>", lable.ERROR)
        return

    cmd_name = theArgs[0]
    show_command_metadata(cmd_name)


def classCall(argParse):
    \"\"\"Legacy function for backward compatibility\"\"\"
    args = argParse.args
    printIt("showCmd: Use '${packName} showCmd <command_name>' for detailed command metadata", lable.INFO)
    printIt(str(args), lable.INFO)
"""))

