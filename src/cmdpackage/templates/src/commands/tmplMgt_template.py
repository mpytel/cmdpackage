#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

tmplMgt_template = Template(dedent("""# Generated using classCall template
import os
import sys
import json
import shutil
import copy
import re
import subprocess
import inspect
from string import Template
from textwrap import dedent
from typing import Dict, Any, List, Optional, Union, Tuple

from ..defs.logIt import printIt, lable, cStr, color
from ..defs.utilities import calculate_md5, split_args
from .commands import Commands
from ..classes.optSwitches import getCmdswitchFlags

commandJsonDict = {
    "tmplMgt": {
        "description": "cmdPackage template managmet for transfering new or modified  command files with supporting files back to an editable install of comPackage.th supporting file",
        "switchFlags": {
            "black": {
                "description": "Use +black to enable and -black to disable, tracked python file formating before template generation, and the new template after generation.",
                "type": "bool",
            },
            "force": {
                "description": "Force template generation even if files are not modified.",
                "type": "bool",
            },
        },
        "status": "Show status of all tracked files",
        "make": "Make a template from a file that will be tracked",
        "sync": "Syncronize all tracked files that have changes",
        "trans": "Transfer new templates back to cmdPackage",
        "list": "List current set of templates",
    }
}


class TemplateSyncer:
    \"\"\"Handles synchronization of template-generated files by creating new template files\"\"\"

    def __init__(self, argParse):

        # Use current working directory as project root
        self.project_root = os.getcwd()
        self.sync_data_file = os.path.join(self.project_root, "genTempSyncData.json")
        self.new_templates_dir = os.path.join(self.project_root, "newTemplates")
        self.sync_data = {}
        cmd_flags = getCmdswitchFlags("tmplMgt")
        self.run_black = cmd_flags.get("black", True)
        self.force = cmd_flags.get("force", False)

        # Load the sync data file into self.sync_data
        self._load_sync_data()
        self.origialTemplatePath = self._getOrigialPathToTemplates()

    def _load_sync_data(self):
        \"\"\"Load the synchronization data from JSON file in current working directory\"\"\"
        if not os.path.exists(self.sync_data_file):
            printIt(
                f"genTempSyncData.json not found in current directory: {self.project_root}",
                lable.ERROR,
            )
            printIt(
                "Please run this command from a project directory containing genTempSyncData.json",
                lable.INFO,
            )
            return

        try:
            with open(self.sync_data_file, "r", encoding="utf-8") as f:
                self.sync_data = json.load(f)

            # Clean up entries for files that no longer exist
            initial_count = len([k for k in self.sync_data.keys() if k != "fields"])
            self._cleanup_missing_files()
            final_count = len([k for k in self.sync_data.keys() if k != "fields"])

            if initial_count > final_count:
                printIt(
                    f"Cleaned up {initial_count - final_count} entries for missing files",
                    lable.INFO,
                )
                # Save the cleaned data immediately
                self._save_sync_data()

            printIt(
                f"Loaded sync data from: {os.path.relpath(self.sync_data_file, self.project_root)}",
                lable.INFO,
            )
            printIt(f"Tracking {final_count} files", lable.INFO)
        except Exception as e:
            printIt(f"Error loading sync data: {e}", lable.ERROR)
            self.sync_data = {}

    def _save_sync_data(self):
        \"\"\"Save the synchronization data back to JSON file\"\"\"
        try:
            with open(self.sync_data_file, "w", encoding="utf-8") as f:
                json.dump(self.sync_data, f, indent=4, ensure_ascii=False)
            printIt(
                f"Sync data in {cStr(os.path.basename(self.sync_data_file),color.YELLOW)} updated",
                lable.SAVED,
            )
        except Exception as e:
            printIt(f"Error saving sync data: {e}", lable.ERROR)

    def _getOrigialPathToTemplates(self) -> str:
        \"\"\"Get the path to parent of original templates\"\"\"
        for file_info in self.sync_data.values():
            if isinstance(file_info, dict):
                temp_file_name: str = file_info.get("tempFileName", "")
                if "/templates/" in temp_file_name:
                    temp_file_name_part = temp_file_name.split("/templates/")
                    return os.path.join(temp_file_name_part[0], "templates")
        return ""

    def _cleanup_missing_files(self):
        \"\"\"Remove entries for files that no longer exist on the filesystem\"\"\"
        missing_files = []

        # Check each tracked file (skip 'fields' entry)
        for file_path in list(self.sync_data.keys()):
            if file_path == "fields":
                continue

            # Check if file exists
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        # Remove entries for missing files
        for file_path in missing_files:
            del self.sync_data[file_path]
            printIt(
                f"Removed missing file from tracking: {os.path.relpath(file_path, self.project_root)}",
                lable.WARN,
            )

    def _get_template_subdirectory(
        self, file_path: str, temp_file_name: str = ""
    ) -> str:
        \"\"\"Determine the correct subdirectory for a template based on tempFileName from genTempSyncData.json\"\"\"

        # First, try to use the provided temp_file_name parameter
        if temp_file_name and temp_file_name != "newMakeTemplate":
            subdir = self._extract_subdirectory_from_temp_filename(temp_file_name)
            if subdir is not None:
                return subdir

        # If temp_file_name not provided or didn't work, look it up in sync_data
        abs_file_path = os.path.abspath(file_path)
        if abs_file_path in self.sync_data:
            file_info = self.sync_data[abs_file_path]
            stored_temp_file_name = file_info.get("tempFileName", "")
            if stored_temp_file_name and stored_temp_file_name != "newMakeTemplate":
                subdir = self._extract_subdirectory_from_temp_filename(
                    stored_temp_file_name
                )
                if subdir is not None:
                    return subdir

        # Last resort: use hardcoded fallback patterns
        return self._get_fallback_subdirectory(file_path)

    def _extract_subdirectory_from_temp_filename(
        self, temp_file_name: str
    ) -> Optional[str]:
        \"\"\"Extract subdirectory path from tempFileName field\"\"\"
        try:
            # Expected format: /path/to/cmdpackage/templates/subdir/filename.py
            # We want to extract the 'subdir' part
            if "/templates/" not in temp_file_name:
                return ""  # Root level if no templates in path

            # Get everything after the first /templates/ occurrence
            template_part = temp_file_name.split("/templates/", 1)[1]

            # Extract the directory part (everything except the filename)
            subdir = os.path.dirname(template_part)

            # Return the subdirectory (could be empty string for root level)
            return subdir

        except Exception as e:
            printIt(
                f"Error extracting subdirectory from tempFileName '{temp_file_name}': {e}",
                lable.WARN,
            )
            return None

    def _get_fallback_subdirectory(self, file_path: str) -> str:
        \"\"\"Fallback method using hardcoded file path patterns (legacy behavior)\"\"\"
        # printIt(
        #     f"Using fallback method to determine template subdirectory for {file_path}",
        #     lable.WARN,
        # )
        abs_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(abs_path, self.project_root)

        # Map file paths to template subdirectories
        if rel_path.startswith(".github/"):
            return ".github"
        elif rel_path.startswith("src/${packName}/commands/templates/"):
            return "src/commands/templates"
        elif rel_path.startswith("src/${packName}/commands/"):
            return "src/commands"
        elif rel_path.startswith("src/${packName}/classes/"):
            return "src/classes"
        elif rel_path.startswith("src/${packName}/defs/"):
            return "src/defs"
        elif rel_path.startswith("src/${packName}/"):
            return "src"
        elif rel_path.startswith("tests/"):
            return "tests"
        elif rel_path in ["pyproject.toml", ".gitignore"] or rel_path.startswith(
            "README"
        ):
            return ""  # Root level
        else:
            return ""  # Default to root level

    def _escape_string_for_template(self, text: str) -> str:
        \"\"\"Escape special characters in strings for Python template generation\"\"\"
        # For multi-line strings in triple quotes, we need to escape backslashes and triple quotes
        escaped = text.replace("\\\\", "\\\\\\\\")  # Escape backslashes first
        escaped = escaped.replace('\"\"\"', '\\\\"\\\\"\\\\"')  # Escape triple quotes to \\"\\"\\"
        return escaped

    def _escape_string_for_json(self, text: str) -> str:
        \"\"\"Escape special characters for JSON template generation\"\"\"
        escaped = text.replace("\\\\", "\\\\\\\\")  # Escape backslashes first
        escaped = escaped.replace('"', '\\\\"')  # Escape double quotes
        return escaped

    def _convert_literals_to_placeholders(self, content: str) -> str:
        \"\"\"Convert literal field values in content to template placeholders\"\"\"
        if "fields" not in self.sync_data:
            return content

        fields = self.sync_data["fields"]
        modified_content = content

        # Create mapping of field names to placeholder names, ordered by specificity
        # (more specific patterns first to avoid partial replacements)
        field_mappings = [
            ("authorsEmail", "authorsEmail"),
            ("maintainersEmail", "maintainersEmail"),
            ("name", "packName"),
            ("version", "version"),
            ("description", "description"),
            ("readme", "readme"),
            ("license", "license"),
            ("authors", "authors"),
            ("maintainers", "maintainers"),
            ("classifiers", "classifiers"),
        ]

        # Replace literal values with placeholders
        for field_key, placeholder_name in field_mappings:
            if field_key in fields and fields[field_key]:
                field_value = str(fields[field_key])
                if field_value and field_value.strip():  # Only replace non-empty values
                    placeholder = "$${" + placeholder_name + "}"
                    # Special handling for 'name' field (packName) which appears in compound words
                    if field_key == "name":
                        # Handle compound patterns like "${packName}rc", "syncTemplates", etc.
                        compound_patterns = [
                            (f"{field_value}rc", f"$${{{placeholder_name}}}rc"),
                            (
                                f"{field_value}Templates",
                                f"$${{{placeholder_name}}}Templates",
                            ),
                            (f".{field_value}rc", f".$${{{placeholder_name}}}rc"),
                        ]
                        for compound_pattern, compound_replacement in compound_patterns:
                            modified_content = modified_content.replace(
                                compound_pattern, compound_replacement
                            )
                    # General replacement (exact mtces with and without word boundaries)
                    pattern = r"\\b" + re.escape(field_value) + r"\\b"
                    modified_content = re.sub(pattern, placeholder, modified_content)
                    # pattern = re.escape(field_value)
                    # modified_content = re.sub(pattern, placeholder, modified_content)

        return modified_content

    def _load_template_content(
        self, template_file: str, template_name: str
    ) -> Optional[str]:
        \"\"\"Load template content from template file\"\"\"
        # Use the new templates directory copy instead of the original path
        template_file_name = os.path.basename(template_file)
        local_template_path = os.path.join(self.new_templates_dir, template_file_name)

        if not os.path.exists(local_template_path):
            printIt(f"Template file not found: {local_template_path}", lable.ERROR)
            return None

        try:
            with open(local_template_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the template content to find the specific template
            template_content = self._extract_template_from_file(content, template_name)
            return template_content

        except Exception as e:
            printIt(
                f"Error loading template {template_name} from {local_template_path}: {e}",
                lable.ERROR,
            )
            return None

    def _extract_template_from_file(
        self, file_content: str, template_name: str
    ) -> Optional[str]:
        \"\"\"Extract specific template from a template file\"\"\"
        # Look for different template patterns

        # Pattern 1: dedent(\"\"\"...\"\"\") assignments
        dedent_pattern = rf'^{re.escape(template_name)}\\s*=\\s*dedent\\(\"\"\"(.*?)\"\"\"\\)'
        mtc = re.search(dedent_pattern, file_content, re.DOTALL | re.MULTILINE)
        if mtc:
            return mtc.group(1)

        # Pattern 2: Template(dedent(\"\"\"...\"\"\")) assignments
        template_pattern = (
            rf'^{re.escape(template_name)}\\s*=\\s*Template\\(dedent\\(\"\"\"(.*?)\"\"\"\\)\\)'
        )
        mtc = re.search(template_pattern, file_content, re.DOTALL | re.MULTILINE)
        if mtc:
            return mtc.group(1)

        # Pattern 3: JSON dictionary assignments
        json_pattern = rf"^{re.escape(template_name)}\\s*=\\s*(\\{{.*?\\}})"
        mtc = re.search(json_pattern, file_content, re.DOTALL | re.MULTILINE)
        if mtc:
            try:
                # Try to parse as JSON and return formatted version
                # Using eval for Python dict syntax
                json_data = eval(mtc.group(1))
                return json.dumps(json_data, indent=2, ensure_ascii=False)
            except:
                return mtc.group(1)

        printIt(f"Template '{template_name}' not found in file", lable.WARN)
        return None

    def _substitute_template_fields(
        self, template_content: str, fields: Dict[str, Any]
    ) -> str:
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
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Look for commandJsonDict = { ... } with proper brace mtcing
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
                # Extract the dictionary content
                dict_lines = lines[start_line : end_line + 1]
                dict_content = "\\n".join(dict_lines)

                # Remove the variable assignment part to get just the dictionary
                dict_content = dict_content.split("=", 1)[1].strip()

                try:
                    # Use eval to parse Python dict syntax
                    json_data = eval(dict_content)
                    return json.dumps(json_data, indent=2, ensure_ascii=False)
                except Exception as e:
                    printIt(
                        f"Error parsing commandJsonDict from {file_path}: {e}",
                        lable.WARN,
                    )
                    return None

            return None
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.WARN)
            return None

    def _build_complete_commands_json_dict(self) -> str:
        \"\"\"Build complete commandsJsonDict from all command files in the sync data\"\"\"
        commands_dict = {
            "switchFlags": {},
            "description": "Dictionary of commands, their discription and swtces, and their argument discriptions.",
            "_globalSwtceFlags": {},
        }

        # Collect command JSONs from all command files
        commands_dir = os.path.join(self.project_root, "src", "${packName}", "commands")

        for file_path, file_info in self.sync_data.items():
            if file_path == "fields":  # Skip the fields section
                continue

            if not isinstance(file_info, dict):
                continue

            # Check if this is a command file
            file_dir = os.path.dirname(os.path.abspath(file_path))
            if file_dir.startswith(commands_dir) and file_path.endswith(".py"):
                # Extract command JSON from this file
                command_json_dict = self._extract_command_json_dict(file_path)
                if command_json_dict:
                    try:
                        cmd_data = json.loads(command_json_dict)
                        # Merge command data into the main dict
                        commands_dict.update(cmd_data)
                    except Exception as e:
                        printIt(
                            f"Error parsing command JSON from {file_path}: {e}",
                            lable.WARN,
                        )

        return json.dumps(commands_dict, indent=2, ensure_ascii=False)

    def _sync_file(self, file_path: str, file_info: Dict[str, Any]) -> bool:
        \"\"\"Generate new template for a modified file\"\"\"
        if not os.path.exists(file_path):
            printIt(
                f"File not found: {os.path.relpath(file_path, self.project_root)}",
                lable.WARN,
            )
            return False

        # Calculate current MD5
        current_md5 = calculate_md5(file_path)
        stored_md5 = file_info.get("fileMD5", "")

        if current_md5 == stored_md5:
            return True

        printIt(
            f"File modified: {os.path.relpath(file_path, self.project_root)}",
            lable.WARN,
        )

        # Get template info
        template_name = file_info.get("template", "")
        template_file = file_info.get("tempFileName", "")

        if not template_name or not template_file:
            printIt(f"Missing template info for {file_path}", lable.ERROR)
            return False

        # Read current file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        # Handle different file types
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".json":
            success = self._generate_json_template(
                file_path, current_content, template_name, template_file
            )
        elif file_ext == ".md":
            success = self._generate_markdown_template(
                file_path, current_content, template_name, template_file
            )
        elif file_ext == ".py":
            success = self._generate_python_template(
                file_path, current_content, template_name, template_file
            )
        else:
            success = self._generate_generic_template(
                file_path, current_content, template_name, template_file
            )

        if success:
            # Update stored MD5 to reflect that we've synced this version
            self.sync_data[file_path]["fileMD5"] = current_md5

        return success

    def _generate_json_template(
        self,
        file_path: str,
        current_content: str,
        template_name: str,
        template_file: str,
    ) -> bool:
        \"\"\"Generate new JSON template from modified file\"\"\"
        printIt(f"Generating JSON template: {template_name}", lable.INFO)

        try:
            # Special handling for commands.json - rebuild from tracked commands only
            if template_name == "commands_commands.json" or file_path.endswith(
                "commands.json"
            ):
                printIt(
                    "Rebuilding commands.json from tracked commands only (excluding untracked)",
                    lable.INFO,
                )
                # Use rebuilt commands dictionary that only includes tracked commands
                rebuilt_commands_json = self._build_complete_commands_json_dict()
                current_content = rebuilt_commands_json
                current_json = json.loads(rebuilt_commands_json)
            else:
                # Parse current JSON content for other JSON files
                current_json = json.loads(current_content)

            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(self.new_templates_dir, template_file_name)

            # Generate Python code for the JSON template
            json_str = json.dumps(current_json, indent=2, ensure_ascii=False)

            # Convert JSON string to Python dict format for embedding in Python file
            template_code = f"{template_name} = {current_content}\\n"

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code
            )

            printIt(
                f"JSON template generated: {template_name} -> {os.path.basename(new_template_path)}",
                lable.PASS,
            )
            return True

        except Exception as e:
            printIt(f"Error generating JSON template for {file_path}: {e}", lable.ERROR)
            return False

    def _generate_markdown_template(
        self,
        file_path: str,
        current_content: str,
        template_name: str,
        template_file: str,
    ) -> bool:
        \"\"\"Generate new Markdown template from modified file\"\"\"
        printIt(f"Generating Markdown template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(self.new_templates_dir, template_file_name)

            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(current_content)

            # Generate Python code with dedent string
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            printIt(f"new_template_path: {new_template_path}", lable.DEBUG)
            printIt(f"template_name: {template_name}", lable.DEBUG)
            printIt(f"template_code: {template_code}", lable.DEBUG)
            self._write_to_template_file(
                new_template_path, template_name, template_code
            )

            printIt(
                f"Markdown template generated: {template_name} -> {os.path.basename(new_template_path)}",
                lable.PASS,
            )
            return True

        except Exception as e:
            printIt(
                f"Error generating Markdown template for {file_path}: {e}", lable.ERROR
            )
            return False

    def _generate_python_template(
        self,
        file_path: str,
        current_content: str,
        template_name: str,
        template_file: str,
    ) -> bool:
        \"\"\"Generate new Python template from modified file\"\"\"
        printIt(f"Generating Python template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(self.new_templates_dir, template_file_name)

            # Extract commandJsonDict from the source file and prepare for substitution
            command_json_dict = self._extract_command_json_dict(file_path)

            # Apply field substitutions including commandJsonDict
            fields = self.sync_data.get("fields", {})
            if command_json_dict:
                fields = fields.copy()  # Don't modify the original
                fields["commandJsonDict"] = command_json_dict

            # Apply field substitutions to content before creating template
            content_with_substitutions = self._substitute_template_fields(
                current_content, fields
            )

            # Determine template format based on template name patterns
            if "Template" in template_name and template_name.endswith("Template"):
                # This is a Template() object - use Template(dedent(\"\"\"...\"\"\"))
                escaped_content = self._escape_string_for_template(
                    content_with_substitutions
                )
                template_code = (
                    f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
                )
            else:
                # This is a simple dedent string
                escaped_content = self._escape_string_for_template(
                    content_with_substitutions
                )
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code
            )

            printIt(
                f"Python template generated: {template_name} -> {os.path.basename(new_template_path)}",
                lable.PASS,
            )
            return True

        except Exception as e:
            printIt(
                f"Error generating Python template for {file_path}: {e}", lable.ERROR
            )
            return False

    def _generate_generic_template(
        self,
        file_path: str,
        current_content: str,
        template_name: str,
        template_file: str,
    ) -> bool:
        \"\"\"Generate new generic template from modified file\"\"\"
        printIt(f"Generating generic template: {template_name}", lable.INFO)

        try:
            # Create new template file
            template_file_name = os.path.basename(template_file)
            new_template_path = os.path.join(self.new_templates_dir, template_file_name)

            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(current_content)

            # Generate Python code with dedent string
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

            # Write or append to template file
            self._write_to_template_file(
                new_template_path, template_name, template_code
            )

            printIt(
                f"Generic template generated: {template_name} -> {os.path.basename(new_template_path)}",
                lable.PASS,
            )
            return True

        except Exception as e:
            printIt(
                f"Error generating generic template for {file_path}: {e}", lable.ERROR
            )
            return False

    def _merge_json_structures(
        self, template: Dict[str, Any], current: Dict[str, Any]
    ) -> Dict[str, Any]:
        \"\"\"Merge JSON structures, preserving user modifications where possible\"\"\"
        merged = copy.deepcopy(template)

        # Recursively merge structures
        def merge_recursive(tmpl_obj, curr_obj, path=""):
            if isinstance(tmpl_obj, dict) and isinstance(curr_obj, dict):
                for key in curr_obj:
                    if key in tmpl_obj:
                        if isinstance(tmpl_obj[key], (dict, list)):
                            tmpl_obj[key] = merge_recursive(
                                tmpl_obj[key], curr_obj[key], f"{path}.{key}"
                            )
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
            with open(template_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip Python syntax compilation check for .py template files
            # Template files contain template variables like ${packName} which aren't valid Python
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
                        f"Template corruption detected in {template_file_path}: pattern {pattern}",
                        lable.WARN,
                    )
                    return False

            return True

        except Exception as e:
            printIt(
                f"Error validating template file {template_file_path}: {e}", lable.WARN
            )
            return False

    def _write_to_template_file(
        self, template_file_path: str, template_name: str, template_code: str
    ):
        \"\"\"Write or update template code in a template file, maintaining original structure and order\"\"\"
        # Get the original template file from the new templates directory
        template_file_name = os.path.basename(template_file_path)
        original_template_path = os.path.join(
            self.new_templates_dir, template_file_name
        )

        # Load original template file to maintain structure
        print(original_template_path)
        if os.path.exists(original_template_path):
            with open(original_template_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        else:
            printIt(
                f"Original template file not found: {original_template_path}",
                lable.WARN,
            )
            original_content = ""

        # Load existing new template file content if it exists
        if os.path.exists(template_file_path):
            with open(template_file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        else:
            existing_content = original_content  # Start with original structure

        # Find and replace the specific template
        import re

        # First, try to find existing template in the content and replace it
        template_pattern = (
            rf"^({re.escape(template_name)}\\s*=.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*\\s*=|\\Z)"
        )
        mtc = re.search(template_pattern, existing_content, re.MULTILINE | re.DOTALL)

        if mtc:
            # Replace existing template
            new_content = re.sub(
                template_pattern,
                template_code.rstrip(),
                existing_content,
                flags=re.MULTILINE | re.DOTALL,
            )
        else:
            # Template doesn't exist in new file, try to find it in original and replace
            original_mtc = re.search(
                template_pattern, original_content, re.MULTILINE | re.DOTALL
            )
            if original_mtc:
                # Add the template in the same position as original
                new_content = re.sub(
                    template_pattern,
                    template_code.rstrip(),
                    original_content,
                    flags=re.MULTILINE | re.DOTALL,
                )

                # Now merge any other updates from existing_content
                if existing_content != original_content:
                    # This is complex - for now, just replace the content
                    new_content = existing_content
                    new_content = re.sub(
                        template_pattern,
                        template_code.rstrip(),
                        new_content,
                        flags=re.MULTILINE | re.DOTALL,
                    )
            else:
                # Template not found anywhere, append at end
                if existing_content and not existing_content.endswith("\\n"):
                    existing_content += "\\n"
                new_content = existing_content + "\\n" + template_code

        # Ensure necessary imports are present
        imports_needed = []
        if (
            "dedent(" in new_content
            and "from textwrap import dedent" not in new_content
        ):
            imports_needed.append("from textwrap import dedent")
        if (
            "Template(" in new_content
            and "from string import Template" not in new_content
        ):
            imports_needed.append("from string import Template")

        if imports_needed:
            import_lines = "\\n".join(imports_needed) + "\\n"
            if new_content.startswith("#!"):
                # Find end of shebang and encoding lines
                lines = new_content.split("\\n")
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith("#") and (
                        "coding" in line or "encoding" in line or line.startswith("#!")
                    ):
                        insert_pos = i + 1
                    else:
                        break
                lines.insert(insert_pos, import_lines)
                new_content = "\\n".join(lines)
            else:
                new_content = import_lines + "\\n" + new_content

        # Ensure the directory exists
        os.makedirs(os.path.dirname(template_file_path), exist_ok=True)

        # Write the file
        with open(template_file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def sync_all_files(self, file_patterns: Optional[List[str]] = None) -> bool:
        \"\"\"Synchronize all tracked files or files mtcing patterns\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return False

        fields = self.sync_data.get("fields", {})
        if not fields:
            printIt("No field data found in sync data", lable.WARN)

        # Group files by their template files to process them together
        template_file_groups = {}
        files_to_sync = []

        for file_path, file_info in self.sync_data.items():
            if file_path == "fields":  # Skip the fields section
                continue

            if not isinstance(file_info, dict):
                continue

            # If patterns specified, check if file mtces
            if file_patterns:
                mtces = False
                for pattern in file_patterns:
                    if pattern in file_path or pattern in os.path.basename(file_path):
                        mtces = True
                        break
                if not mtces:
                    continue

            if self.force:
                files_to_sync.append(file_path)
            else:
                # Check if file is modified
                current_md5 = calculate_md5(file_path)
                stored_md5 = file_info.get("fileMD5", "")
                if current_md5 != stored_md5:
                    files_to_sync.append(file_path)
                else:
                    # check if template exists in new templates dir
                    templateExists = self._check_newTemplate_exists(file_path)
                    if not templateExists:
                        files_to_sync.append(file_path)

            # Group by template file
            template_file = file_info.get("tempFileName", "")
            if template_file:
                template_file_name = os.path.basename(template_file)
                if template_file_name not in template_file_groups:
                    template_file_groups[template_file_name] = []
                if file_path in files_to_sync:
                    template_file_groups[template_file_name].append(
                        (file_path, file_info)
                    )

        if not files_to_sync:
            if not self.force:
                printIt("No files modified", lable.INFO)
                return True
            else:
                printIt("Forcing sync - processing all files", lable.INFO)
        else:
            printIt(f"Generating templates for {len(files_to_sync)} files.", lable.INFO)

        success_count = 0

        # Process each template file group
        for template_file_name, file_group in template_file_groups.items():
            if self._sync_template_file_group(template_file_name, file_group):
                success_count += 1

        printIt(
            f"Generated templates for {success_count}/{len(files_to_sync)} files",
            lable.INFO,
        )

        # Save updated sync data
        if success_count > 0:
            self._save_sync_data()

        return True

    def _sync_template_file_group(
        self, template_file_name: str, file_group: List[Tuple[str, Dict[str, Any]]]
    ) -> bool:
        \"\"\"Sync a group of files that belong to the same template file\"\"\"
        success = False
        # Check if this is using the special newMakeTemplate marker
        # This marker indicates files that are authorized for make action
        if template_file_name == "newMakeTemplate":
            # Create standalone template files for each modified file in this group
            printIt(
                f"Creating standalone templates for newMakeTemplate group", lable.DEBUG
            )
            return self._create_standalone_templates_for_group(file_group)

        # stats for black formatting
        black_success = 0
        total_files = 0
        all_python_files = self._get_all_python_files()

        # Replace each modified template
        for file_path, file_info in file_group:
            if not os.path.exists(file_path):
                continue
            # Run black formatter if enabled and file is Python`
            if self.run_black and file_path in all_python_files:
                total_files += 1
                black_success += self._run_black_on_file(file_path)

            success = self._make_template_from_file(file_path)

            # Update the MD5 in sync data if file is modified
            current_md5 = calculate_md5(file_path)
            stored_md5 = file_info.get("fileMD5", "")
            if success and current_md5 != stored_md5:
                self.sync_data[file_path]["fileMD5"] = current_md5

        # Report black formatting stats
        if black_success:
            printIt(f"Black formatting {black_success}/{total_files} files", lable.INFO)

        return success

    def _create_standalone_templates_for_group(
        self, file_group: List[Tuple[str, Dict[str, Any]]]
    ) -> bool:
        \"\"\"Create standalone template files for files in newMakeTemplate group\"\"\"
        success_count = 0
        total_processed = 0

        for file_path, file_info in file_group:
            if not os.path.exists(file_path):
                total_processed += (
                    1  # Count as processed (file missing is handled gracefully)
                )
                success_count += 1  # This is not an error condition
                continue

            template_name = file_info.get("template", "")
            if not template_name:
                total_processed += (
                    1  # Count as processed (no template name to work with)
                )
                success_count += 1  # This is not an error condition
                continue

            total_processed += 1  # Count this file as being processed

            # Check if file comes from commands parent directory
            # If so, it should go into the combined cmdTemplate.py file
            file_dir = os.path.dirname(os.path.abspath(file_path))
            commands_dir = os.path.join(self.project_root, "src", "${packName}", "commands")
            is_from_commands_dir = file_dir.startswith(commands_dir)

            # Check if the template file already exists
            template_exists = self._check_newTemplate_exists(file_path)

            # Check if file is modified
            current_md5 = calculate_md5(file_path)
            stored_md5 = file_info.get("fileMD5", "")
            is_modified = current_md5 != stored_md5

            # Skip if template exists and file is unchanged
            if template_exists and not is_modified:
                if not self.force:
                    success_count += 1  # No work needed - this is success
                    continue

            if self._make_template_from_file(file_path):
                success_count += 1
                # Update the MD5 in sync data
                self.sync_data[file_path]["fileMD5"] = current_md5

        return success_count == total_processed

    def _check_newTemplate_exists(self, file_path: str) -> bool:
        \"\"\"Check if the template file exists for this source file\"\"\"

        testTempPath = self._get_fallback_subdirectory(file_path)
        # Check if standalone template file exists
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".json":
            template_filename = filename
        else:
            template_filename = f"{name_without_ext}.py"

        template_file_path = os.path.join(
            self.new_templates_dir, testTempPath, template_filename
        )
        return os.path.exists(template_file_path)

    def list_tracked_files(self):
        \"\"\"List all files tracked in the sync data\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return

        printIt("\\nTracked files:", lable.INFO)
        printIt("-" * 80, lable.INFO)

        for file_path, file_info in self.sync_data.items():
            if file_path == "fields":
                continue

            if not isinstance(file_info, dict):
                continue

            # Check if file exists and if it's modified
            exists = os.path.exists(file_path)
            if exists:
                current_md5 = calculate_md5(file_path)
                stored_md5 = file_info.get("fileMD5", "")
                status = "OK" if current_md5 == stored_md5 else "MODIFIED"
                status_color = color.GREEN if status == "OK" else color.YELLOW
            else:
                status = "MISSING"
                status_color = color.RED

            template_name = file_info.get("template", "Unknown")
            rel_path = os.path.relpath(file_path, self.project_root)

            printIt(
                f"{cStr(status, status_color):10} {rel_path:50} ({template_name})",
                lable.INFO,
            )

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

        printIt(
            "-" * 29, cStr(" Tracked File Status ", color.GREEN), "-" * 30, lable.INFO
        )

        for file_path, file_info in self.sync_data.items():
            if file_path == "fields":
                continue

            if not isinstance(file_info, dict):
                continue

            total_files += 1

            # Check if file exists and if it's modified
            exists = os.path.exists(file_path)
            if exists:
                current_md5 = calculate_md5(file_path)
                stored_md5 = file_info.get("fileMD5", "")
                if current_md5 == stored_md5:
                    ok_files += 1
                else:
                    modified_files += 1
                    template_name = file_info.get("template", "unknown")
                    modified_file_list.append((file_path, template_name))
            else:
                missing_files += 1
                template_name = file_info.get("template", "unknown")
                missing_file_list.append((file_path, template_name))

        printIt(f"Total tracked files: {total_files}", lable.INFO)
        printIt(f"{cStr('Files in sync:', color.GREEN)} {ok_files}", lable.INFO)
        if modified_files > 0:
            printIt(
                f"{cStr('Modified files:', color.YELLOW)} {modified_files}", lable.INFO
            )
        if missing_files > 0:
            printIt(f"{cStr('Missing files:', color.RED)} {missing_files}", lable.INFO)

        # List modified files
        if modified_file_list:
            printIt(
                "-" * 32, cStr(" Modified Files ", color.YELLOW), "-" * 32, lable.INFO
            )
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
            printIt(
                "-" * 31,
                cStr(" Untracked Files ", color.CYAN),
                "-" * 32,
                lable.INFO,
            )
            for file_path in untracked_files:
                # Show relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, self.project_root)
                except ValueError:
                    rel_path = file_path
                printIt(f"  {cStr('UNTRACKED', color.CYAN)} {rel_path}", lable.INFO)
            printIt(
                f"\\n  To track these files, use: {cStr('${packName} tmplMgt make <file>', color.GREEN)}",
                lable.INFO,
            )

    def _discover_untracked_files(self) -> List[str]:
        \"\"\"Discover files that exist but aren't tracked in genTempSyncData.json\"\"\"
        untracked = []

        # Get list of tracked files
        tracked_files = set()
        for file_path in self.sync_data.keys():
            if file_path != "fields" and isinstance(self.sync_data[file_path], dict):
                # Normalize to absolute path
                if os.path.isabs(file_path):
                    tracked_files.add(file_path)
                else:
                    tracked_files.add(os.path.join(self.project_root, file_path))

        # Directories to scan for potential template files
        scan_dirs = [
            os.path.join(self.project_root, "tests"),
            os.path.join(self.project_root, "src"),
        ]

        # File patterns to look for
        patterns = [
            "test_*.py",  # Test files
            "*.py",  # Python files
        ]

        # Files/directories to exclude
        exclude_patterns = [
            "__pycache__",
            "__init__.py",
            ".pyc",
            "env/",
            "venv/",
            ".git/",
            "build/",
            "dist/",
            ".egg-info",
        ]

        for scan_dir in scan_dirs:
            if not os.path.exists(scan_dir):
                continue

            for root, dirs, files in os.walk(scan_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d for d in dirs if not any(excl in d for excl in exclude_patterns)
                ]

                for file in files:
                    # Skip excluded files
                    if any(excl in file for excl in exclude_patterns):
                        continue

                    # Check if file mtces any pattern
                    file_path = os.path.join(root, file)

                    # Only include Python files for now
                    if not file.endswith(".py"):
                        continue

                    # Skip if already tracked
                    if file_path in tracked_files:
                        continue

                    # Add to untracked list
                    untracked.append(file_path)

        return sorted(untracked)

    def _get_all_python_files(self) -> List[str]:
        \"\"\"Get all Python files (tracked and untracked) in the project\"\"\"
        python_files = []

        # Get tracked Python files
        for file_path in self.sync_data.keys():
            if file_path != "fields" and isinstance(self.sync_data[file_path], dict):
                if file_path.endswith(".py") and os.path.exists(file_path):
                    python_files.append(file_path)

        # Get untracked Python files
        untracked_files = self._discover_untracked_files()
        for file_path in untracked_files:
            if file_path.endswith(".py"):
                python_files.append(file_path)

        return sorted(list(set(python_files)))  # Remove duplicates and sort

    def _check_black_available(self) -> bool:
        \"\"\"Check if black is available in the system\"\"\"
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (
            subprocess.SubprocessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def _run_black_on_file(self, file_path: str) -> int:
        \"\"\"Run black formatter on the specified file

        Returns:
            1 if successful, 0 otherwise
        \"\"\"
        successful = 0
        if not os.path.exists(file_path):
            return successful

        if not self._check_black_available():
            printIt(
                "Black formatter not found. Please install black: pip install black",
                lable.WARN,
            )
            return successful

        try:
            # Run black on individual file for better error reporting
            result = subprocess.run(
                ["black", "--line-length=200", file_path], capture_output=True, text=True, timeout=30
            )
            rel_path = os.path.relpath(file_path, self.project_root)

            if result.returncode == 0:
                if result.stdout.strip():  # Black outputs when it reformats
                    printIt(f"Formatted: {rel_path}", lable.INFO)
                    successful = 1
            else:
                printIt(
                    f"Black failed on {rel_path}: {result.stderr.strip()}",
                    lable.WARN,
                )

        except subprocess.TimeoutExpired:
            rel_path = os.path.relpath(file_path, self.project_root)
            printIt(f"Black timeout on {rel_path}", lable.WARN)
        except Exception as e:
            rel_path = os.path.relpath(file_path, self.project_root)
            printIt(f"Error running black on {rel_path}: {e}", lable.WARN)

        return successful

    def _make_template_from_file(self, file_path: str) -> bool:
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

        # printIt(f"Creating template from file: {file_path}", lable.INFO)

        # Create  template filename
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        template_name = f"{name_without_ext}_template"
        template_filename = f"{filename}"

        # Read the file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            printIt(f"Error reading file {file_path}: {e}", lable.ERROR)
            return False

        # Determine file type and generate appropriate template code
        file_ext = os.path.splitext(file_path)[1].lower()

        # For .md files, convert literal values to template placeholders
        if file_ext == ".md":
            file_content = self._convert_literals_to_placeholders(file_content)
            if file_path == "${readme}":
                printIt(f"file_content:\\n{file_content}", lable.DEBUG)
        # Create template file name - for non-Python files that generate Python templates, use .py extension
        if file_ext == ".json":
            # get filename without .json extension h
            template_filename = os.path.basename(filename)  # keep .json extension
            template_filename = template_filename + "_template.json"
        else:
            # Other files get .py extension
            template_filename = f"{name_without_ext}_template.py"
            file_content = self._convert_literals_to_placeholders(file_content)

        if file_ext == ".json":
            try:
                # Validate JSON
                json.loads(file_content)
                # For JSON files, we'll use the raw content directly in template file
                template_code = file_content
            except json.JSONDecodeError as e:
                printIt(f"Invalid JSON in file {file_path}: {e}", lable.ERROR)
                return False
        elif file_ext in [".py", ".md", ".txt"] or template_name.lower().endswith(
            "template"
        ):
            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(file_content)
            # .md files should always use Template(dedent()) format
            if file_ext == ".md" or (
                "template" in template_name.lower()
                and template_name.lower().endswith("template")
            ):
                template_code = (
                    f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
                )
            else:
                template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'
        else:
            # Generic template for other file types
            escaped_content = self._escape_string_for_template(file_content)
            template_code = f'{template_name} = dedent(\"\"\"{escaped_content}\"\"\")\\n'

        # Determine the correct subdirectory for this template
        # First, check if we have tempFileName info from existing tracking
        temp_file_name = ""
        abs_file_path = os.path.abspath(file_path)
        if abs_file_path in self.sync_data:
            temp_file_name = self.sync_data[abs_file_path].get("tempFileName", "")

        template_subdir = self._get_template_subdirectory(file_path, temp_file_name)

        # Create the template file path with subdirectory
        if template_subdir:
            template_dir = os.path.join(self.new_templates_dir, template_subdir)
            new_template_path = os.path.join(template_dir, template_filename)
        else:
            new_template_path = os.path.join(self.new_templates_dir, template_filename)

        # Ensure the newTemplates directory and subdirectory exist
        if template_subdir:
            template_dir = os.path.join(self.new_templates_dir, template_subdir)
            os.makedirs(template_dir, exist_ok=True)
        else:
            os.makedirs(self.new_templates_dir, exist_ok=True)

        # Create template file content based on file type
        if file_ext == ".json":
            # For JSON files, just write the template code without Python headers
            template_file_content = template_code
        else:
            # For other files, create a full Python template file structure
            imports_needed = []
            if "dedent(" in template_code:
                imports_needed.append("from textwrap import dedent")
            if "Template(" in template_code:
                imports_needed.append("from string import Template")

            import_lines = "\\n".join(imports_needed) if imports_needed else ""

            template_file_content = f\"\"\"#!/usr/bin/python
# -*- coding: utf-8 -*-
{import_lines}

{template_code}
\"\"\"

        try:
            with open(new_template_path, "w", encoding="utf-8") as f:
                f.write(template_file_content)
            printIt(
                f"Template file created: {cStr(os.path.relpath(new_template_path, self.project_root), color.YELLOW)}",
                lable.SAVED,
            )

            return True
        except Exception as e:
            printIt(f"Error writing template file: {e}", lable.ERROR)
            return False

    def add_file_to_sync_data(self, file_path: str):
        \"\"\"Add a new file to the sync data tracking\"\"\"
        if not os.path.exists(file_path):
            printIt(f"File not found: {file_path}", lable.ERROR)
            return

        # Make file_path relative to project root if it's absolute
        if os.path.isabs(file_path):
            try:
                file_path = os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If file is on different drive, keep absolute path
                pass

        # Create template filename
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        template_name = f"{name_without_ext}_template"

        # Determine template subdirectory
        template_subdir = self._get_fallback_subdirectory(file_path)

        # Create template file name
        if template_subdir:
            temp_file_name = os.path.join(template_subdir, filename)
        else:
            temp_file_name = filename

        temp_file_name = os.path.join(self.origialTemplatePath, temp_file_name)

        # Calculate MD5
        file_md5 = calculate_md5(file_path)

        # Add to sync data
        self.sync_data[file_path] = {
            "fileMD5": file_md5,
            "template": template_name,
            "tempFileName": temp_file_name,
        }

        self._save_sync_data()

    def _get_all_files_in_directory(self, directory: str) -> List[str]:
        \"\"\"Get a list of all files in the specified directory and its subdirectories\"\"\"
        file_list = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_list.append(file_path)
        return file_list

    def transfer_templates(self):
        \"\"\"Transfer templates from newTemplates to origialTemplatePath directory\"\"\"
        newtemplates_files = []
        if os.path.exists(self.origialTemplatePath):
            resopone = input(
                f"Are you sure you want to clobber {self.origialTemplatePath}? (y/N): "
            )
            if resopone.lower() != "y":
                printIt("Transfer cancelled by user", lable.WARN)
                return
            elif os.path.exists(self.new_templates_dir):
                # remove origialTemplatePath directory
                shutil.rmtree(self.origialTemplatePath)
        else:
            # does origialTemplatePath parent directory exist
            if not os.path.exists(os.path.dirname(self.origialTemplatePath)):
                printIt(
                    f"Original template path parent directory does not exist: {os.path.dirname(self.origialTemplatePath)}",
                    lable.ERROR,
                )
                return

        newtemplates_files = self._get_all_files_in_directory(self.new_templates_dir)

        if not newtemplates_files:
            printIt("No templates found to transfer", lable.WARN)
            return

        printIt(
            f"Transferring templates from {self.new_templates_dir} to {self.origialTemplatePath}",
            lable.INFO,
        )

        # get list of all files in self.new_templates_dir
        if not os.path.exists(self.new_templates_dir):
            printIt(
                f"New templates directory does not exist: {self.new_templates_dir}",
                lable.ERROR,
            )
            return

        # Copy all files from newTemplates to origialTemplatePath
        for source_file_name in newtemplates_files:
            # construnct target file name
            rel_path = os.path.relpath(source_file_name, self.new_templates_dir)
            target_file_name = os.path.join(self.origialTemplatePath, rel_path)
            try:
                target_dir = os.path.dirname(target_file_name)
                os.makedirs(target_dir, exist_ok=True)
                # printIt(
                #     f"Transfer:\\n{new_file_name}\\n{target_file_name}",
                #     f"\\nTransferred: {os.path.exists(new_file_name)}, {os.path.exists(target_file_name)}",
                #     lable.DEBUG,
                # )
                shutil.copy2(source_file_name, target_file_name)
                printIt(
                    cStr(os.path.basename(target_file_name), color.YELLOW), lable.SAVED
                )
            except Exception as e:
                printIt(
                    f"Error transferring template to {target_file_name}: {e}",
                    lable.ERROR,
                )

    def listNew_templates(self):
        \"\"\"List all templates in the newTemplates directory\"\"\"
        if not os.path.exists(self.new_templates_dir):
            printIt(
                f"New templates directory not found: {self.new_templates_dir}",
                lable.ERROR,
            )
            return

        printIt("\\nTemplates in newTemplates directory:", lable.INFO)
        printIt("-" * 80, lable.INFO)

        for root, dirs, files in os.walk(self.new_templates_dir):
            for file in files:
                template_path = os.path.join(root, file)
                rel_path = os.path.relpath(template_path, self.new_templates_dir)
                printIt(f"{rel_path}", lable.INFO)


class tmplMgtCommand:
    def __init__(self, argParse):
        self.argParse = argParse
        self.cmdObj = Commands()
        self.commands = self.cmdObj.commands
        self.args = argParse.args
        self.theCmd = self.args.commands[0]
        self.theArgNames = list(self.commands[self.theCmd].keys())
        self.theArgs: list[str] = self.args.arguments

        self.module = sys.modules[__name__]

        # printIt(f"Command flags from .${packName}rc: {cmd_flags}", lable.DEBUG)

    def execute(self):
        \"\"\"Main execution method for tmplMgt command\"\"\"

        if len(self.theArgs) == 0:
            printIt("No arguments provided", lable.WARN)
            return

        theArgs, optArgs = split_args(self.theArgs, [])

        argIndex = 0
        while argIndex < len(theArgs):
            anArg = theArgs[argIndex]
            method_name = str(anArg)
            if hasattr(self.module, method_name):
                # Dynamically calls use handle_ prefix to map to methods.
                getattr(self.module, method_name)(self.argParse)
            argIndex += 1

    def get_external_helpers(self):
        \"\"\"Gets and returns the names of all module-level functions.\"\"\"

        # 1. Get all members (attributes) of the current module
        all_members = inspect.getmembers(self.module)

        # 2. Filter the members
        function_names = [
            name
            for name, obj in all_members
            if inspect.isfunction(obj)  # Check if it's a function object
            and obj.__module__
            == __name__  # Ensure it's defined in THIS file, not imported
            # Exclude internal/special functions like __init__
            and not name.startswith("_")
            # Exclude methods of the tmplMgt function
            and not name == "tmplMgt"
            # Optionally exclude the method doing the lookup
            and obj != self.get_external_helpers
        ]

        return function_names


def tmplMgt(argParse):
    \"\"\"Entry point for tmplMgt command\"\"\"
    command_instance = tmplMgtCommand(argParse)
    command_instance.execute()


def status(argParse):
    \"\"\"Show status of all tracked files\"\"\"
    syncer = TemplateSyncer(argParse)
    syncer.show_status()


def make(argParse):
    syncer = TemplateSyncer(argParse)

    args = argParse.args
    theArgs = args.arguments
    theArgs, optArgs = split_args(theArgs, ["make"])

    for i, arg in enumerate(theArgs):
        if i + 1 < len(theArgs):
            make_file = theArgs[i + 1]
            # Skip the next argument since we consumed it
            theArgs = theArgs[: i + 1] + theArgs[i + 2 :]
            break
    if theArgs:
        for arg in theArgs:
            sucess = syncer._make_template_from_file(arg)
            if sucess:
                syncer.add_file_to_sync_data(arg)
    else:
        printIt("No file specified for 'make' action", lable.ERROR)


def sync(argParse):
    syncer = TemplateSyncer(argParse)

    args = argParse.args
    theArgs = args.arguments
    theArgs, optArgs = split_args(theArgs, ["sync"])

    file_patterns = []
    for arg in theArgs:
        printIt(f"arg: {arg}", lable.DEBUG)
        file_patterns.append(arg)

    if file_patterns:
        printIt(
            f"Generating templates for files mtcing patterns: {', '.join(file_patterns)}",
            lable.INFO,
        )

    syncer.sync_all_files(file_patterns if file_patterns else None)


def listNew(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.listNew_templates()


def trans(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.transfer_templates()
"""))

