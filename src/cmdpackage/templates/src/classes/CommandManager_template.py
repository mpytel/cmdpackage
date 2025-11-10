#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

CommandManager_template = Template(dedent("""\"\"\"
CommandManager - Centralized management for commands.json and related operations

This class centralizes all the repetitive command.json operations that were previously
duplicated across multiple command files (newCmd.py, modCmd.py, rmCmd.py, etc.).

Features:
- Centralized file path management
- Consistent JSON read/write operations with error handling
- MD5 sync data management
- Command structure access (arguments, option_switches, option_strings)
- Config file management (.cmdrc, legacy .${packName}rc)
- Command existence and data retrieval
\"\"\"

import os
import json
import hashlib
import ast
from pathlib import Path
from typing import Dict, Optional, Any
from ..defs.logIt import printIt, lable, cStr, color


class CommandManager:
    \"\"\"Centralized manager for commands.json and related operations\"\"\"

    def __init__(self):
        \"\"\"Initialize CommandManager with file paths\"\"\"
        # Get the commands directory (where this would be called from)
        self.commands_dir = Path(__file__).parent.parent / "commands"
        self.commands_json_path = self.commands_dir / "commands.json"
        self.cmdrc_path = self.commands_dir / ".cmdrc"

        # Legacy .${packName}rc path (in project root)
        self.project_root = self.commands_dir.parent.parent.parent
        self.${packName}rc_path = self.project_root / ".${packName}rc"

        # Sync data path
        self.sync_data_path = self.project_root / "genTempSyncData.json"

    def _load_commands_json(self) -> Dict[str, Any]:
        \"\"\"Load and return commands.json data with error handling\"\"\"
        try:
            with open(self.commands_json_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            printIt(f"Error loading commands.json: {e}", lable.ERROR)
            return {}
        except Exception as e:
            printIt(f"Unexpected error loading commands.json: {e}", lable.ERROR)
            return {}

    def _save_commands_json(self, data: Dict[str, Any]) -> bool:
        \"\"\"Save data to commands.json with error handling\"\"\"
        try:
            with open(self.commands_json_path, "w") as f:
                json.dump(data, f, indent=2)

            # Update MD5 hash after successful save
            self.update_sync_data_md5(str(self.commands_json_path))
            return True
        except Exception as e:
            printIt(f"Error saving commands.json: {e}", lable.ERROR)
            return False

    def command_exists(self, cmd_name: str) -> bool:
        \"\"\"Check if command exists in commands.json\"\"\"
        commands_data = self._load_commands_json()
        return cmd_name in commands_data

    def get_command_data(self, cmd_name: str) -> Dict[str, Any]:
        \"\"\"Get command data from commands.json\"\"\"
        commands_data = self._load_commands_json()
        return commands_data.get(cmd_name, {})

    def get_all_commands(self) -> Dict[str, Any]:
        \"\"\"Get all commands data from commands.json\"\"\"
        return self._load_commands_json()

    def update_command(self, cmd_name: str, cmd_data: Dict[str, Any]) -> bool:
        \"\"\"Update command data in commands.json and sync to Python file\"\"\"
        commands_data = self._load_commands_json()
        commands_data[cmd_name] = cmd_data

        # Save to commands.json
        if self._save_commands_json(commands_data):
            # Also update the Python file's commandJsonDict
            self.update_python_file_command_json_dict(cmd_name)
            return True
        return False

    def remove_command(self, cmd_name: str) -> bool:
        \"\"\"Remove entire command from commands.json\"\"\"
        commands_data = self._load_commands_json()
        if cmd_name in commands_data:
            del commands_data[cmd_name]
            return self._save_commands_json(commands_data)
        return False

    def get_arguments(self, cmd_name: str) -> Dict[str, str]:
        \"\"\"Get arguments section for a specific command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        return cmd_data.get("arguments", {})

    def get_option_switches(self, cmd_name: str) -> Dict[str, str]:
        \"\"\"Get option_switches (boolean flags) for a specific command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        return cmd_data.get("option_switches", {})

    def get_option_strings(self, cmd_name: str) -> Dict[str, str]:
        \"\"\"Get option_strings for a specific command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        return cmd_data.get("option_strings", {})

    def get_legacy_switch_flags(self, cmd_name: str) -> Dict[str, Any]:
        \"\"\"Get legacy switchFlags for backwards compatibility\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        return cmd_data.get("switchFlags", {})

    def add_argument(self, cmd_name: str, arg_name: str, arg_description: str) -> bool:
        \"\"\"Add an argument to a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data:
            return False

        if "arguments" not in cmd_data:
            cmd_data["arguments"] = {}

        cmd_data["arguments"][arg_name] = arg_description
        return self.update_command(cmd_name, cmd_data)

    def remove_argument(self, cmd_name: str, arg_name: str) -> bool:
        \"\"\"Remove an argument from a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data or "arguments" not in cmd_data:
            return False

        arguments = cmd_data["arguments"]
        if arg_name in arguments:
            del arguments[arg_name]
            return self.update_command(cmd_name, cmd_data)
        return False

    def add_option_switch(self, cmd_name: str, flag_name: str, flag_description: str) -> bool:
        \"\"\"Add a boolean flag (option_switch) to a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data:
            return False

        if "option_switches" not in cmd_data:
            cmd_data["option_switches"] = {}

        cmd_data["option_switches"][flag_name] = flag_description
        return self.update_command(cmd_name, cmd_data)

    def remove_option_switch(self, cmd_name: str, flag_name: str) -> bool:
        \"\"\"Remove a boolean flag (option_switch) from a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data or "option_switches" not in cmd_data:
            return False

        option_switches = cmd_data["option_switches"]
        if flag_name in option_switches:
            del option_switches[flag_name]
            return self.update_command(cmd_name, cmd_data)
        return False

    def add_option_string(self, cmd_name: str, option_name: str, option_description: str) -> bool:
        \"\"\"Add a string option (option_string) to a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data:
            return False

        if "option_strings" not in cmd_data:
            cmd_data["option_strings"] = {}

        cmd_data["option_strings"][option_name] = option_description
        return self.update_command(cmd_name, cmd_data)

    def remove_option_string(self, cmd_name: str, option_name: str) -> bool:
        \"\"\"Remove a string option (option_string) from a command\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data or "option_strings" not in cmd_data:
            return False

        option_strings = cmd_data["option_strings"]
        if option_name in option_strings:
            del option_strings[option_name]
            return self.update_command(cmd_name, cmd_data)
        return False

    def flag_exists(self, cmd_name: str, flag_name: str) -> bool:
        \"\"\"Check if a flag exists in either option_switches, option_strings, or legacy switchFlags\"\"\"
        cmd_data = self.get_command_data(cmd_name)
        if not cmd_data:
            return False

        # Check new structure
        option_switches = cmd_data.get("option_switches", {})
        option_strings = cmd_data.get("option_strings", {})

        # Check legacy structure
        switch_flags = cmd_data.get("switchFlags", {})

        return flag_name in option_switches or flag_name in option_strings or flag_name in switch_flags

    def get_cmdrc_data(self) -> Dict[str, Any]:
        \"\"\"Read .cmdrc file data\"\"\"
        try:
            if not self.cmdrc_path.exists():
                return {"option_switches": {}, "option_strings": {}, "commands": {}}

            with open(self.cmdrc_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            printIt(f"Error loading .cmdrc: {e}", lable.WARN)
            return {"option_switches": {}, "option_strings": {}, "commands": {}}

    def save_cmdrc_data(self, data: Dict[str, Any]) -> bool:
        \"\"\"Save data to .cmdrc file\"\"\"
        try:
            with open(self.cmdrc_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            printIt(f"Error saving .cmdrc: {e}", lable.WARN)
            return False

    def add_cmdrc_flag(self, cmd_name: str, flag_name: str, is_switch: bool, default_value: Any = None) -> bool:
        \"\"\"Add a flag to .cmdrc file\"\"\"
        cmdrc_data = self.get_cmdrc_data()

        if "commands" not in cmdrc_data:
            cmdrc_data["commands"] = {}

        if cmd_name not in cmdrc_data["commands"]:
            cmdrc_data["commands"][cmd_name] = {"option_switches": {}, "option_strings": {}}

        cmd_options = cmdrc_data["commands"][cmd_name]

        if is_switch:
            if "option_switches" not in cmd_options:
                cmd_options["option_switches"] = {}
            cmd_options["option_switches"][flag_name] = default_value if default_value is not None else False
        else:
            if "option_strings" not in cmd_options:
                cmd_options["option_strings"] = {}
            cmd_options["option_strings"][flag_name] = default_value if default_value is not None else ""

        return self.save_cmdrc_data(cmdrc_data)

    def remove_cmdrc_flag(self, cmd_name: str, flag_name: str) -> bool:
        \"\"\"Remove a flag from .cmdrc file\"\"\"
        cmdrc_data = self.get_cmdrc_data()

        if "commands" not in cmdrc_data or cmd_name not in cmdrc_data["commands"]:
            return False

        cmd_options = cmdrc_data["commands"][cmd_name]
        removed = False

        # Remove from option_switches
        if "option_switches" in cmd_options and flag_name in cmd_options["option_switches"]:
            del cmd_options["option_switches"][flag_name]
            removed = True

        # Remove from option_strings
        if "option_strings" in cmd_options and flag_name in cmd_options["option_strings"]:
            del cmd_options["option_strings"][flag_name]
            removed = True

        # If command has no more flags, remove the command entry
        if not cmd_options.get("option_switches") and not cmd_options.get("option_strings"):
            del cmdrc_data["commands"][cmd_name]

        return self.save_cmdrc_data(cmdrc_data) if removed else False

    def get_legacy_${packName}rc_data(self) -> Dict[str, Any]:
        \"\"\"Read legacy .${packName}rc file data for backwards compatibility\"\"\"
        try:
            if not self.${packName}rc_path.exists():
                return {"commandFlags": {}}

            with open(self.${packName}rc_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            printIt(f"Warning: Could not read .${packName}rc file: {e}", lable.WARN)
            return {"commandFlags": {}}

    def save_legacy_${packName}rc_data(self, data: Dict[str, Any]) -> bool:
        \"\"\"Save data to legacy .${packName}rc file\"\"\"
        try:
            with open(self.${packName}rc_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            printIt(f"Warning: Could not update .${packName}rc file: {e}", lable.WARN)
            return False

    def remove_legacy_${packName}rc_flag(self, cmd_name: str, flag_name: str) -> bool:
        \"\"\"Remove a flag from legacy .${packName}rc file\"\"\"
        ${packName}rc_data = self.get_legacy_${packName}rc_data()

        if (
            "commandFlags" in ${packName}rc_data
            and cmd_name in ${packName}rc_data["commandFlags"]
            and flag_name in ${packName}rc_data["commandFlags"][cmd_name]
        ):

            del ${packName}rc_data["commandFlags"][cmd_name][flag_name]

            # If command has no more flags, remove the command entry
            if not ${packName}rc_data["commandFlags"][cmd_name]:
                del ${packName}rc_data["commandFlags"][cmd_name]

            return self.save_legacy_${packName}rc_data(${packName}rc_data)

        return False

    def update_sync_data_md5(self, file_path: str) -> None:
        \"\"\"Update the MD5 hash for a file in genTempSyncData.json\"\"\"
        try:
            if not self.sync_data_path.exists():
                # If genTempSyncData.json doesn't exist, no need to update
                return

            # Calculate new MD5 hash
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Load sync data
            with open(self.sync_data_path, "r") as f:
                sync_data = json.load(f)

            # Update MD5 for the file if it's tracked
            abs_file_path = os.path.abspath(file_path)
            if abs_file_path in sync_data:
                sync_data[abs_file_path]["fileMD5"] = file_hash

                # Save updated sync data
                with open(self.sync_data_path, "w") as f:
                    json.dump(sync_data, f, indent=4)

                file_name = os.path.basename(file_path)
                printIt(f"Updated MD5 hash for {file_name} in sync data", lable.INFO)

        except Exception as e:
            printIt(f"Warning: Could not update sync data MD5: {e}", lable.WARN)

    def remove_flag_from_all_locations(self, cmd_name: str, flag_name: str) -> bool:
        \"\"\"Remove a flag from commands.json, .cmdrc, and legacy .${packName}rc files\"\"\"
        success = True

        # Remove from commands.json (both new and old structures)
        cmd_data = self.get_command_data(cmd_name)
        if cmd_data:
            flag_removed = False

            # Remove from new structure
            if "option_switches" in cmd_data and flag_name in cmd_data["option_switches"]:
                del cmd_data["option_switches"][flag_name]
                flag_removed = True

            if "option_strings" in cmd_data and flag_name in cmd_data["option_strings"]:
                del cmd_data["option_strings"][flag_name]
                flag_removed = True

            # Remove from legacy structure
            if "switchFlags" in cmd_data and flag_name in cmd_data["switchFlags"]:
                del cmd_data["switchFlags"][flag_name]
                if not cmd_data["switchFlags"]:
                    cmd_data["switchFlags"] = {}
                flag_removed = True

            if flag_removed:
                success &= self.update_command(cmd_name, cmd_data)

        # Remove from .cmdrc
        success &= self.remove_cmdrc_flag(cmd_name, flag_name)

        # Remove from legacy .${packName}rc
        success &= self.remove_legacy_${packName}rc_flag(cmd_name, flag_name)

        return success

    def update_python_file_command_json_dict(self, cmd_name: str) -> bool:
        \"\"\"Update the commandJsonDict in the Python file to match commands.json\"\"\"
        try:
            # Get the current command data from commands.json
            cmd_data = self.get_command_data(cmd_name)
            if not cmd_data:
                printIt(f"Command '{cmd_name}' not found in commands.json", lable.WARN)
                return False

            # Build the path to the Python file
            python_file_path = self.commands_dir / f"{cmd_name}.py"

            if not python_file_path.exists():
                printIt(f"Python file {python_file_path} not found", lable.WARN)
                return False

            # Read the current file content
            with open(python_file_path, "r") as f:
                file_content = f.read()

            # Create the new commandJsonDict string
            new_command_json_dict = {cmd_name: cmd_data}
            json_str = json.dumps(new_command_json_dict, indent=2)

            # Look for the commandJsonDict pattern with proper nesting
            lines = file_content.split("\\n")
            start_line = -1
            end_line = -1
            brace_count = 0
            in_dict = False

            for i, line in enumerate(lines):
                if "commandJsonDict" in line and "=" in line and "{" in line:
                    start_line = i
                    in_dict = True
                    brace_count = line.count("{") - line.count("}")
                elif in_dict:
                    brace_count += line.count("{") - line.count("}")
                    if brace_count == 0:
                        end_line = i
                        break

            if start_line != -1 and end_line != -1:
                # Replace the commandJsonDict section
                before_lines = lines[:start_line]
                after_lines = lines[end_line + 1 :]

                new_lines = before_lines + [f"commandJsonDict = {json_str}"] + after_lines

                # Write the updated content back to the file
                with open(python_file_path, "w") as f:
                    f.write("\\n".join(new_lines))

                printIt(f"Updated commandJsonDict in {python_file_path.name}", lable.INFO)
                return True
            else:
                printIt(f"Could not find commandJsonDict pattern in {python_file_path.name}", lable.WARN)
                return False

        except Exception as e:
            printIt(f"Error updating Python file commandJsonDict: {e}", lable.ERROR)
            return False

    def sync_all_python_files(self) -> bool:
        \"\"\"Sync all Python files' commandJsonDict with commands.json\"\"\"
        commands_data = self._load_commands_json()
        success_count = 0
        total_count = len(commands_data)

        for cmd_name in commands_data:
            if self.update_python_file_command_json_dict(cmd_name):
                success_count += 1

        printIt(f"Synced {success_count}/{total_count} Python files", lable.INFO)
        return success_count == total_count

    def build_tracked_commands_json(self) -> Dict[str, Any]:
        \"\"\"
        Build commands.json equivalent by extracting commandJsonDict from ALL Python files in commands directory

        This method serves as the foundation for making Python files the source of truth.
        It scans ALL Python files in src/${packName}/commands/, extracts their commandJsonDict definitions,
        and builds a complete commands.json structure from them. This treats both tracked and
        untracked command files uniformly.

        Returns:
            Dict[str, Any]: Dictionary equivalent to commands.json built from Python files
        \"\"\"
        commands_dict = {}
        processed_files = 0
        successful_extractions = 0

        # Get the commands directory path
        commands_dir = os.path.dirname(os.path.dirname(__file__)) + "/commands"

        if not os.path.exists(commands_dir):
            printIt(f"Commands directory not found: {commands_dir}", lable.ERROR)
            return {}

        # Scan ALL Python files in the commands directory
        for file_name in os.listdir(commands_dir):
            if not file_name.endswith(".py"):
                continue

            # Skip special files that don't contain commandJsonDict
            if file_name in ["commands.py", "__init__.py", "cmdOptSwitchboard.py", "cmdSwitchboard.py"]:
                continue

            file_path = os.path.join(commands_dir, file_name)
            processed_files += 1

            try:
                # Read the Python file
                with open(file_path, "r") as f:
                    file_content = f.read()

                # Extract commandJsonDict using the same logic as our update method
                lines = file_content.split("\\n")
                start_line = -1
                end_line = -1
                brace_count = 0
                in_dict = False

                for i, line in enumerate(lines):
                    if "commandJsonDict" in line and "=" in line and "{" in line:
                        start_line = i
                        in_dict = True
                        brace_count = line.count("{") - line.count("}")
                    elif in_dict:
                        brace_count += line.count("{") - line.count("}")
                        if brace_count == 0:
                            end_line = i
                            break

                if start_line != -1 and end_line != -1:
                    # Extract the commandJsonDict section
                    dict_lines = lines[start_line : end_line + 1]
                    dict_content = "\\n".join(dict_lines)

                    # Extract just the dictionary part after the equals sign
                    equals_index = dict_content.find("=")
                    if equals_index != -1:
                        python_dict_part = dict_content[equals_index + 1 :].strip()

                        # Use ast.literal_eval to safely parse the Python dictionary
                        command_data = ast.literal_eval(python_dict_part)

                        # Merge into commands_dict
                        if isinstance(command_data, dict):
                            commands_dict.update(command_data)
                            successful_extractions += 1

                            # Get command name for logging
                            cmd_names = list(command_data.keys())
                            if cmd_names:
                                printIt(
                                    f"Extracted commandJsonDict from {file_name}: {', '.join(cmd_names)}",
                                    lable.ABORTPRT,
                                )
                        else:
                            printIt(f"Invalid commandJsonDict format in {file_path}", lable.WARN)
                else:
                    # No commandJsonDict found - this is OK, just skip silently
                    pass

            except (ValueError, SyntaxError) as e:
                printIt(f"Python syntax error in {file_path}: {e}", lable.ERROR)
            except Exception as e:
                printIt(f"Error processing {file_path}: {e}", lable.ERROR)

        printIt(f"Built commands dict from {successful_extractions}/{processed_files} Python command files", lable.INFO)
        printIt(f"Total commands found: {len(commands_dict)}", lable.INFO)

        return commands_dict

    def generate_commands_template_json(self) -> bool:
        \"\"\"
        Generate newTemplates/src/commands/commands_template.json from tracked Python files

        This method creates the template version of commands.json by building it from
        the commandJsonDict values in all tracked Python files, then saves it to the
        newTemplates directory structure.

        Returns:
            bool: True if successful, False otherwise
        \"\"\"
        try:
            # Build commands dict from tracked files
            commands_dict = self.build_tracked_commands_json()

            if not commands_dict:
                printIt("No commands found in tracked files", lable.WARN)
                return False

            # Ensure newTemplates directory structure exists
            template_dir = self.project_root / "newTemplates" / "src" / "commands"
            template_dir.mkdir(parents=True, exist_ok=True)

            # Write the commands_template.json file
            template_file_path = template_dir / "commands_template.json"
            with open(template_file_path, "w") as f:
                json.dump(commands_dict, f, indent=2)

            printIt(
                "Generated commands.json template:",
                cStr(os.path.relpath(template_file_path, self.project_root), color.YELLOW),
                lable.SAVED,
            )
            return True

        except Exception as e:
            printIt(f"Error generating commands_template.json: {e}", lable.ERROR)
            return False

    def update_command_json(
        self, cmd_obj, the_args: dict, cmd_name: str = None, mode: str = "create"
    ) -> Dict[str, Any]:
        \"\"\"
        Unified method to update command JSON for both create and modify operations

        Args:
            cmd_obj: Commands object containing command data
            the_args: Dictionary of arguments from command line
            cmd_name: Command name (required for modify mode)
            mode: "create" for new commands, "modify" for existing commands

        Returns:
            dict: Updated command data (for create mode) or empty dict (for modify mode)
        \"\"\"
        import copy

        # Work with a copy of the commands
        commands = copy.deepcopy(cmd_obj.commands)

        if mode == "create":
            # Create mode: Initialize new command structure
            # Get command name from theArgs
            arg_names = list(the_args.keys())
            if not arg_names:
                printIt("No command name found in arguments", lable.ERROR)
                return {}

            cmd_name = arg_names[0]
            cmd_description = the_args[cmd_name]

            new_command_cmd_json = {}
            new_command_cmd_json["description"] = cmd_description

            # Initialize new structure sections
            new_command_cmd_json["option_switches"] = {}
            new_command_cmd_json["option_strings"] = {}
            new_command_cmd_json["arguments"] = {}

            # Handle option flags if they exist - use new structure
            option_details = the_args.get("_option_details", {})

            # Process option details into new structure
            for option_name, option_info in option_details.items():
                if option_info.get("type") == "bool":
                    new_command_cmd_json["option_switches"][option_name] = option_info.get("description", "")
                elif option_info.get("type") == "str":
                    new_command_cmd_json["option_strings"][option_name] = option_info.get("description", "")

            # Process arguments (skip command name and _option_details)
            arg_index = 1
            while arg_index < len(the_args):
                arg_name = arg_names[arg_index]
                if arg_name != "_option_details":
                    new_command_cmd_json["arguments"][arg_name] = the_args[arg_name]
                arg_index += 1

            # Add to commands dictionary
            commands[cmd_name] = new_command_cmd_json

            # Update cmd_obj.commands (this triggers _writeCmdJsonFile via setter)
            cmd_obj.commands = commands

            printIt(f"Successfully updated command '{cmd_name}' in commands.json", lable.INFO)

            # Also update the Python file's commandJsonDict
            self.update_python_file_command_json_dict(cmd_name)

            # Return command data for create mode
            return new_command_cmd_json

        elif mode == "modify":
            # Modify mode: Get existing command data and update it
            if not cmd_name or cmd_name not in commands:
                printIt(f"Command '{cmd_name}' not found for modification", lable.ERROR)
                return {}

            arg_names = list(the_args.keys())

            # Handle command description update if present
            if cmd_name in arg_names:
                commands[cmd_name]["description"] = the_args[cmd_name]
                arg_index = 1  # Start processing other arguments from index 1
            else:
                arg_index = 0  # Start from beginning if no description update

            # Ensure all required sections exist
            if "arguments" not in commands[cmd_name]:
                commands[cmd_name]["arguments"] = {}
            if "option_switches" not in commands[cmd_name]:
                commands[cmd_name]["option_switches"] = {}
            if "option_strings" not in commands[cmd_name]:
                commands[cmd_name]["option_strings"] = {}

            # Handle option flags if they exist
            option_details = the_args.get("_option_details", {})
            if option_details:
                # Process option details into appropriate sections
                for option_name, option_info in option_details.items():
                    if option_info.get("type") == "bool":
                        commands[cmd_name]["option_switches"][option_name] = option_info.get("description", "")
                    elif option_info.get("type") == "str":
                        commands[cmd_name]["option_strings"][option_name] = option_info.get("description", "")

            # Add regular arguments (skip _option_details)
            while arg_index < len(the_args):
                arg_name = arg_names[arg_index]
                # Skip the special _option_details entry
                if arg_name != "_option_details":
                    commands[cmd_name]["arguments"][arg_name] = the_args[arg_name]
                arg_index += 1

            # Update cmd_obj.commands (this triggers _writeCmdJsonFile via setter)
            cmd_obj.commands = commands

            printIt(f"Successfully updated command '{cmd_name}' in commands.json", lable.INFO)

            # Also update the Python file's commandJsonDict
            self.update_python_file_command_json_dict(cmd_name)

            # Return empty dict for modify mode
            return {}

        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'create' or 'modify'")

    def verify_commands_json_integrity(self) -> bool:
        \"\"\"
        Verify that ALL Python command files have their commandJsonDict in sync with commands.json

        This function checks for issues by comparing commandJsonDict from ALL Python files
        in src/${packName}/commands/ with what's actually in commands.json. This treats both tracked
        and untracked command files uniformly.

        Returns:
            bool: True if all commands are properly synced, False if issues found
        \"\"\"
        issues_found = []
        commands_json = self._load_commands_json()

        # Get the commands directory path
        commands_dir = os.path.dirname(os.path.dirname(__file__)) + "/commands"

        if not os.path.exists(commands_dir):
            printIt(f"Commands directory not found: {commands_dir}", lable.ERROR)
            return False

        # Check ALL Python files in commands directory
        for file_name in os.listdir(commands_dir):
            if not file_name.endswith(".py"):
                continue

            # Skip special files that don't contain commandJsonDict
            if file_name in ["commands.py", "__init__.py", "cmdOptSwitchboard.py", "cmdSwitchboard.py"]:
                continue

            file_path = os.path.join(commands_dir, file_name)

            try:
                # Extract commandJsonDict from Python file
                with open(file_path, "r") as f:
                    file_content = f.read()

                # Look for commandJsonDict
                lines = file_content.split("\\n")
                start_line = -1
                end_line = -1
                brace_count = 0
                in_dict = False

                for i, line in enumerate(lines):
                    if "commandJsonDict" in line and "=" in line and "{" in line:
                        start_line = i
                        in_dict = True
                        brace_count = line.count("{") - line.count("}")
                    elif in_dict:
                        brace_count += line.count("{") - line.count("}")
                        if brace_count == 0:
                            end_line = i
                            break

                if start_line == -1 or end_line == -1:
                    # No commandJsonDict found - this might be OK for some files
                    continue

                # Extract and parse the commandJsonDict
                dict_lines = lines[start_line : end_line + 1]
                dict_content = "\\n".join(dict_lines)
                equals_index = dict_content.find("=")
                if equals_index != -1:
                    python_dict_part = dict_content[equals_index + 1 :].strip()
                    try:
                        command_data = ast.literal_eval(python_dict_part)

                        # Check each command in the Python file
                        for cmd_name, cmd_info in command_data.items():
                            if cmd_name not in commands_json:
                                issues_found.append(f"Command '{cmd_name}' from {file_name} missing in commands.json")
                            else:
                                # Check if the command data matches
                                json_cmd = commands_json[cmd_name]

                                # Check description
                                if cmd_info.get("description") != json_cmd.get("description"):
                                    issues_found.append(
                                        f"Command '{cmd_name}' description mismatch between {file_name} and commands.json"
                                    )

                                # Check if major sections exist
                                for section in ["option_switches", "option_strings", "arguments"]:
                                    if section in cmd_info and section not in json_cmd:
                                        issues_found.append(
                                            f"Command '{cmd_name}' missing {section} section in commands.json"
                                        )

                    except Exception as e:
                        issues_found.append(f"Error parsing commandJsonDict in {file_name}: {e}")

            except Exception as e:
                issues_found.append(f"Error processing {file_name}: {e}")

        # Report findings
        if issues_found:
            printIt("🚨 Commands.json integrity issues found:", lable.ERROR)
            for issue in issues_found:
                printIt(f"  • {issue}", lable.WARN)
            return False
        else:
            # printIt("✅ Commands.json integrity verified - all command files properly synced", lable.INFO)
            return True

    def repair_commands_json_from_python_files(self) -> bool:
        \"\"\"
        Repair commands.json by rebuilding it from commandJsonDict in ALL Python command files
        while preserving any existing commands that don't have corresponding Python files

        This function fixes issues like the rmCmd bug by regenerating commands.json
        from the authoritative Python file commandJsonDict definitions, but it preserves
        any existing commands that don't have corresponding Python files.

        Returns:
            bool: True if repair was successful
        \"\"\"
        printIt("🔧 Repairing commands.json from Python commandJsonDict sources...", lable.INFO)

        # Load current commands.json to preserve existing data
        current_commands = self._load_commands_json()

        # Start with current structure to preserve any commands without Python files
        repaired_commands = current_commands.copy()

        # Ensure basic structure exists
        if "switchFlags" not in repaired_commands:
            repaired_commands["switchFlags"] = {}

        # Build from ALL Python command files (both tracked and untracked)
        python_commands = self.build_tracked_commands_json()

        if python_commands:
            # Get list of commands from Python files
            python_command_names = set(python_commands.keys())
            existing_command_names = set(cmd for cmd in current_commands.keys() if cmd != "switchFlags")

            # Identify commands that exist in JSON but not in Python files
            json_only_commands = existing_command_names - python_command_names

            if json_only_commands:
                printIt(
                    f"Preserving {len(json_only_commands)} commands without Python files: {', '.join(sorted(json_only_commands))}",
                    lable.INFO,
                )

            # Update/add Python-sourced commands (this will overwrite any existing versions)
            repaired_commands.update(python_commands)

            # Log what was updated
            printIt(f"Updated {len(python_commands)} commands from Python files", lable.INFO)

            # Write the repaired commands.json
            try:
                with open(self.commands_json_path, "w") as f:
                    json.dump(repaired_commands, f, indent=2, ensure_ascii=False)

                total_commands = len([k for k in repaired_commands.keys() if k != "switchFlags"])
                printIt(f"✅ Successfully repaired commands.json ({total_commands} total commands)", lable.INFO)

                # Update MD5 in sync data
                self.update_sync_data_md5(str(self.commands_json_path))

                return True

            except Exception as e:
                printIt(f"Error writing repaired commands.json: {e}", lable.ERROR)
                return False
        else:
            printIt("No command data found in Python files to repair with", lable.ERROR)
            return False


# Global instance for easy access
command_manager = CommandManager()
"""))

