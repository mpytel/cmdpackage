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
from ..classes.optSwitches import getCmdSwitchOptions
from ..classes.CommandManager import command_manager

commandJsonDict = {
    "tmplMgt": {
        "description": "cmdPackage template management for transferring new or modified  command files with supporting files back to an editable install of comPackage.th supporting file",
        "option_switches": {
            "black": "Use +black to enable and -black to disable, tracked python file formatting before template generation, and the new template after generation.",
            "force": "Force template generation even if files are not modified.",
        },
        "option_strings": {},
        "arguments": {
            "status": "Show status of all tracked files",
            "scanFiles": "Show detailed file discovery report including exclusions",
            "listFiles": "List files by category: tracked, untracked, noTracked, or new",
            "sync": "Synchronize all tracked files that have changes",
            "trans": "Transfer new templates back to cmdPackage",
            "track": "Track file for template sync",
            "untrack": "Remove a template from being tracked",
            "notrack": "Add files to doNotTrack list to exclude from tracking consideration",
        },
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
        self.args = argParse.args  # Store args for use in track/untrack methods
        cmd_flags = getCmdSwitchOptions("tmplMgt")
        self.run_black = cmd_flags.get("black", True)
        self.force = cmd_flags.get("force", False)

        # Check if newTemplates directory is missing
        self.temp_force_due_to_missing_dir = False
        if not os.path.exists(self.new_templates_dir):
            self.temp_force_due_to_missing_dir = True
            printIt("newTemplates directory missing - enabling force mode for this run", lable.INFO)

        # Load the sync data file into self.sync_data
        self._load_sync_data()
        self.origialTemplatePath = self._getOrigialPathToTemplates()

    def is_force_mode(self) -> bool:
        \"\"\"Check if force mode is active (either from cmdrc or temporary due to missing directory)\"\"\"
        return self.force or self.temp_force_due_to_missing_dir

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
                f"Update sync data in {cStr(os.path.basename(self.sync_data_file),color.YELLOW)}",
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
            if file_path in ["fields", "doNotTrack"]:
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

    def _get_template_subdirectory(self, file_path: str, temp_file_name: str = "") -> str:
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
                subdir = self._extract_subdirectory_from_temp_filename(stored_temp_file_name)
                if subdir is not None:
                    return subdir

        # Last resort: use hardcoded fallback patterns
        return self._get_fallback_subdirectory(file_path)

    def _extract_subdirectory_from_temp_filename(self, temp_file_name: str) -> Optional[str]:
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
        elif rel_path in ["pyproject.toml", ".gitignore"] or rel_path.startswith("README"):
            return ""  # Root level
        else:
            return ""  # Default to root level

    def _escape_string_for_template(self, text: str) -> str:
        \"\"\"Escape special characters in strings for Python template generation\"\"\"
        # For multi-line strings in triple quotes, we need to escape backslashes and triple quotes
        escaped = text.replace("\\\\", "\\\\\\\\")  # Escape backslashes first
        escaped = escaped.replace('\"\"\"', '\\\\"\\\\"\\\\"')  # Escape triple quotes to \\"\\"\\"
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
                            modified_content = modified_content.replace(compound_pattern, compound_replacement)
                    # General replacement (exact mtces with and without word boundaries)
                    pattern = r"\\b" + re.escape(field_value) + r"\\b"
                    modified_content = re.sub(pattern, placeholder, modified_content)
                    # pattern = re.escape(field_value)
                    # modified_content = re.sub(pattern, placeholder, modified_content)

        # After replacing literals with placeholders, escape remaining $$ characters
        modified_content = self._escape_literal_dollars(modified_content)

        return modified_content

    def _escape_literal_dollars(self, content: str) -> str:
        \"\"\"Escape literal $$ characters that are not part of valid template placeholders\"\"\"
        if "fields" not in self.sync_data:
            return content

        # Get list of valid placeholder names from field_mappings
        valid_placeholders = [
            "authorsEmail",
            "maintainersEmail",
            "packName",
            "version",
            "description",
            "readme",
            "license",
            "authors",
            "maintainers",
            "classifiers",
        ]

        # Create pattern to match valid placeholders: $${validName}
        valid_placeholder_pattern = r"\\$$\\{(" + "|".join(re.escape(name) for name in valid_placeholders) + r")\\}"

        # Find all $$ characters and their positions
        result = []
        i = 0
        while i < len(content):
            if content[i] == "$$":
                # Check if this $$ is part of a valid placeholder
                remaining_content = content[i:]
                match = re.match(valid_placeholder_pattern, remaining_content)
                if match:
                    # This is a valid placeholder, keep it as is
                    result.append(match.group(0))
                    i += len(match.group(0))
                else:
                    # This is a literal $$, escape it as $$$$
                    result.append("$$$$")
                    i += 1
            else:
                result.append(content[i])
                i += 1

        return "".join(result)

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

    def _write_to_template_file(self, template_file_path: str, template_name: str, template_code: str):
        \"\"\"Write or update template code in a template file, maintaining original structure and order\"\"\"
        # Get the original template file from the new templates directory
        template_file_name = os.path.basename(template_file_path)
        original_template_path = os.path.join(self.new_templates_dir, template_file_name)

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
        template_pattern = rf"^({re.escape(template_name)}\\s*=.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*\\s*=|\\Z)"
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
            original_mtc = re.search(template_pattern, original_content, re.MULTILINE | re.DOTALL)
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
        if "dedent(" in new_content and "from textwrap import dedent" not in new_content:
            imports_needed.append("from textwrap import dedent")
        if "Template(" in new_content and "from string import Template" not in new_content:
            imports_needed.append("from string import Template")

        if imports_needed:
            import_lines = "\\n".join(imports_needed) + "\\n"
            if new_content.startswith("#!"):
                # Find end of shebang and encoding lines
                lines = new_content.split("\\n")
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith("#") and ("coding" in line or "encoding" in line or line.startswith("#!")):
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
        \"\"\"Synchronize all tracked files or files matching patterns\"\"\"
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

            # If patterns specified, check if file matches
            if file_patterns:
                matches = False
                for pattern in file_patterns:
                    if pattern in file_path or pattern in os.path.basename(file_path):
                        matches = True
                        break
                if not matches:
                    continue

            # Determine if file should be synced
            should_sync = False
            if self.is_force_mode():
                # Force mode: sync ALL tracked files (either explicit +force or missing directory)
                should_sync = True
            else:
                # Normal mode: only sync modified files
                current_md5 = calculate_md5(file_path)
                stored_md5 = file_info.get("fileMD5", "")
                if current_md5 != stored_md5:
                    should_sync = True

            if should_sync:
                files_to_sync.append(file_path)

                # Group by template file
                template_file = file_info.get("tempFileName", "")
                if template_file:
                    template_file_name = os.path.basename(template_file)
                    if template_file_name not in template_file_groups:
                        template_file_groups[template_file_name] = []
                    template_file_groups[template_file_name].append((file_path, file_info))

        if not files_to_sync:
            printIt("No files to sync", lable.INFO)
            return True
        else:
            if self.temp_force_due_to_missing_dir:
                printIt(
                    f"Missing directory mode: Generating templates for {len(files_to_sync)} tracked files.", lable.INFO
                )
            elif self.force:
                printIt(f"Force mode: Generating templates for {len(files_to_sync)} tracked files.", lable.INFO)
            # else:
            #     printIt(f"Generating templates for {len(files_to_sync)} modified files.", lable.INFO)

        success_count = 0

        # Process each template file group
        for template_file_name, file_group in template_file_groups.items():
            if self._sync_template_file_group(template_file_name, file_group):
                success_count += 1

        # printIt(
        #     f"Generated templates for {success_count}/{len(files_to_sync)} files",
        #     lable.INFO,
        # )

        # Special handling for commands.json: Always generate commands_template.json from tracked Python files
        commands_json_generated = False
        try:
            # printIt("Generating commands_template.json from tracked Python files...", lable.INFO)
            if command_manager.generate_commands_template_json():
                commands_json_generated = True
                # printIt("Generated commands_template.json from commandJsonDict in tracked Python files", lable.INFO)

        except Exception as e:
            printIt(f"Error generating commands_template.json: {e}", lable.ERROR)

        # Save updated sync data
        if success_count > 0 or commands_json_generated:
            self._save_sync_data()

        return True

    def _sync_template_file_group(self, template_file_name: str, file_group: List[Tuple[str, Dict[str, Any]]]) -> bool:
        \"\"\"Sync a group of files that belong to the same template file\"\"\"
        success = False
        # Check if this is using the special newMakeTemplate marker
        # This marker indicates files that are authorized for make action
        if template_file_name == "newMakeTemplate":
            # Create standalone template files for each modified file in this group
            printIt(f"Creating standalone templates for newMakeTemplate group", lable.DEBUG)
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

    def _create_standalone_templates_for_group(self, file_group: List[Tuple[str, Dict[str, Any]]]) -> bool:
        \"\"\"Create standalone template files for files in newMakeTemplate group\"\"\"
        success_count = 0
        total_processed = 0

        for file_path, file_info in file_group:
            if not os.path.exists(file_path):
                total_processed += 1  # Count as processed (file missing is handled gracefully)
                success_count += 1  # This is not an error condition
                continue

            template_name = file_info.get("template", "")
            if not template_name:
                total_processed += 1  # Count as processed (no template name to work with)
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

        template_file_path = os.path.join(self.new_templates_dir, testTempPath, template_filename)
        return os.path.exists(template_file_path)

    def show_status(self, file_patterns: Optional[List[str]] = None):
        \"\"\"Show status of all tracked files or files matching patterns\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return

        total_files = 0
        ok_files = 0
        modified_files = 0
        missing_files = 0
        modified_file_list = []
        missing_file_list = []

        # Filter files based on patterns if provided
        files_to_check = []
        for file_path, file_info in self.sync_data.items():
            if file_path == "fields":
                continue

            if not isinstance(file_info, dict):
                continue

            # Skip commands.json - it's generated from Python files, not tracked for status
            if file_path.endswith("/commands.json") or file_path.endswith("\\\\commands.json"):
                continue

            # If patterns specified, check if file matches
            if file_patterns:
                matches = self._matches_any_pattern(file_path, file_info, file_patterns)
                if not matches:
                    continue

            files_to_check.append((file_path, file_info))

        if not files_to_check:
            if file_patterns:
                printIt(f"No tracked files match patterns: {', '.join(file_patterns)}", lable.WARN)
            else:
                printIt("No tracked files found", lable.WARN)
            return

        if file_patterns:
            printIt(f"Status for files matching patterns: {', '.join(file_patterns)}", lable.INFO)

        printIt("-" * 29, cStr(" Tracked File Status ", color.GREEN), "-" * 30, lable.INFO)

        for file_path, file_info in files_to_check:
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
            printIt(f"{cStr('Modified files:', color.YELLOW)} {modified_files}", lable.INFO)
        if missing_files > 0:
            printIt(f"{cStr('Missing files:', color.RED)} {missing_files}", lable.INFO)

        # List modified files
        if modified_file_list:
            printIt("-" * 32, cStr(" Modified Files ", color.YELLOW), "-" * 32, lable.INFO)
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

        # List untracked files only if no patterns specified (to avoid confusion)
        if not file_patterns:
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
                    f"\\n  To track these files, use: {cStr('${packName} tmplMgt track <file>', color.GREEN)}",
                    lable.INFO,
                )

    def _matches_any_pattern(self, file_path: str, file_info: dict, patterns: List[str]) -> bool:
        \"\"\"Check if a file matches any of the given patterns\"\"\"
        # Get various ways to refer to this file
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        template_name = file_info.get("template", "")

        # Try to get relative path
        try:
            rel_path = os.path.relpath(file_path, self.project_root)
        except ValueError:
            rel_path = file_path

        for pattern in patterns:
            # Direct matches
            if (
                pattern in file_path
                or pattern in filename
                or pattern in rel_path
                or pattern in name_without_ext
                or pattern in template_name
            ):
                return True

            # Handle template name patterns (remove _template suffix)
            if pattern.endswith("_template"):
                base_pattern = pattern[:-9]  # Remove "_template"
                if base_pattern in filename or base_pattern in name_without_ext or base_pattern in rel_path:
                    return True

            # Handle adding _template to pattern
            pattern_with_template = pattern + "_template"
            if pattern_with_template in template_name:
                return True

            # Handle .py extension variants
            if not pattern.endswith(".py"):
                pattern_py = pattern + ".py"
                if pattern_py in filename or pattern_py in rel_path:
                    return True

        return False

    def _discover_untracked_files(self, verbose: bool = False) -> List[str]:
        \"\"\"Discover files that exist but aren't tracked in genTempSyncData.json\"\"\"
        untracked = []
        excluded_files = []
        already_tracked_files = []

        # Get list of tracked files
        tracked_files = set()
        for file_path in self.sync_data.keys():
            if file_path != "fields" and file_path != "doNotTrack" and isinstance(self.sync_data[file_path], dict):
                # Normalize to absolute path
                if os.path.isabs(file_path):
                    tracked_files.add(file_path)
                else:
                    tracked_files.add(os.path.join(self.project_root, file_path))

        # Get doNotTrack list from sync data
        do_not_track = self.sync_data.get("doNotTrack", [])
        do_not_track_abs = set()
        for file_pattern in do_not_track:
            # Convert to absolute path if not already
            if os.path.isabs(file_pattern):
                do_not_track_abs.add(file_pattern)
            else:
                do_not_track_abs.add(os.path.join(self.project_root, file_pattern))

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
                dirs[:] = [d for d in dirs if not any(excl in d for excl in exclude_patterns)]

                for file in files:
                    file_path = os.path.join(root, file)

                    # Check if file is in doNotTrack list
                    if file_path in do_not_track_abs:
                        if verbose:
                            excluded_files.append((file_path, "listed in doNotTrack"))
                        continue

                    # Check exclusions and track reasons
                    if file.startswith(("${packName}", ".${packName}")):
                        if verbose:
                            excluded_files.append((file_path, "starts with '${packName}' or '.${packName}'"))
                        continue

                    # Skip excluded files
                    if any(excl in file for excl in exclude_patterns):
                        if verbose:
                            excluded_files.append(
                                (
                                    file_path,
                                    f"matches exclusion pattern: {[excl for excl in exclude_patterns if excl in file]}",
                                )
                            )
                        continue

                    # Only include Python files for now
                    if not file.endswith(".py"):
                        if verbose:
                            excluded_files.append((file_path, "not a .py file"))
                        continue

                    # Skip if already tracked
                    if file_path in tracked_files:
                        if verbose:
                            already_tracked_files.append(file_path)
                        continue

                    # Add to untracked list
                    untracked.append(file_path)

        if verbose:
            printIt(f"\\n{cStr('File Discovery Report:', color.CYAN)}", lable.INFO)
            printIt(f"  Scanned directories: {scan_dirs}", lable.INFO)
            printIt(f"  Found {len(untracked)} untracked files", lable.INFO)
            printIt(f"  Found {len(already_tracked_files)} already tracked files", lable.INFO)
            printIt(f"  Excluded {len(excluded_files)} files", lable.INFO)

            if excluded_files:
                printIt(f"\\n{cStr('Excluded Files:', color.YELLOW)}", lable.INFO)
                for file_path, reason in excluded_files[:10]:  # Show first 10
                    rel_path = os.path.relpath(file_path, self.project_root)
                    printIt(f"  {rel_path} - {reason}", lable.INFO)
                if len(excluded_files) > 10:
                    printIt(f"  ... and {len(excluded_files) - 10} more", lable.INFO)

        return sorted(untracked)

    def _find_files_by_keyword(self, keyword: str) -> List[str]:
        \"\"\"Find all untracked files associated with a keyword (e.g., 'qt' finds test_qt.py, README_qt_instructions.md, etc.)\"\"\"
        associated_files = []

        # Get list of untracked files
        untracked_files = self._discover_untracked_files()

        # Also scan for other file types in the project root and common directories
        scan_dirs = [
            self.project_root,  # Root directory for README, config files
            os.path.join(self.project_root, "tests"),
            os.path.join(self.project_root, "src"),
            os.path.join(self.project_root, "docs"),
        ]

        # Additional file extensions to look for
        extensions = [".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"]

        # Files/directories to exclude
        exclude_patterns = [
            "__pycache__",
            ".pyc",
            "env/",
            "venv/",
            ".git/",
            "build/",
            "dist/",
            ".egg-info",
            "node_modules/",
        ]

        all_candidate_files = set(untracked_files)  # Start with untracked Python files

        # Scan for additional file types
        for scan_dir in scan_dirs:
            if not os.path.exists(scan_dir):
                continue

            for root, dirs, files in os.walk(scan_dir):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(excl in d for excl in exclude_patterns)]

                for file in files:
                    if file.startswith("."):  # Skip hidden files
                        continue

                    # Skip excluded files
                    if any(excl in file for excl in exclude_patterns):
                        continue

                    # Check if file has an extension we care about
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in extensions:
                        file_path = os.path.join(root, file)

                        # Skip if already tracked
                        rel_path = os.path.relpath(file_path, self.project_root)
                        if rel_path in self.sync_data:
                            continue

                        all_candidate_files.add(file_path)

        # Filter files that contain the keyword
        keyword_lower = keyword.lower()
        for file_path in all_candidate_files:
            filename = os.path.basename(file_path)
            filename_lower = filename.lower()

            # Check if keyword appears in filename
            if keyword_lower in filename_lower:
                # Additional checks for common patterns
                patterns_match = [
                    f"test_{keyword_lower}",  # test_qt.py
                    f"{keyword_lower}_test",  # qt_test.py
                    f"test{keyword_lower}",  # testqt.py
                    f"{keyword_lower}test",  # qttest.py
                    f"readme_{keyword_lower}",  # README_qt_instructions.md
                    f"{keyword_lower}_readme",  # qt_README.md
                    f"{keyword_lower}_",  # qt_something.py
                    f"_{keyword_lower}",  # something_qt.py
                    keyword_lower,  # qt.py
                ]

                # If any pattern matches, add to associated files
                if any(pattern in filename_lower for pattern in patterns_match):
                    associated_files.append(file_path)

        return sorted(associated_files)

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
                ["black", "--line-length=120", file_path], capture_output=True, text=True, timeout=30
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
            # template_filename = os.path.basename(filename)  # keep .json extension
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
        elif file_ext in [".py", ".md", ".txt"] or template_name.lower().endswith("template"):
            # Escape content for Python string embedding
            escaped_content = self._escape_string_for_template(file_content)
            # .md files should always use Template(dedent()) format
            if file_ext == ".md" or (
                "template" in template_name.lower() and template_name.lower().endswith("template")
            ):
                template_code = f'{template_name} = Template(dedent(\"\"\"{escaped_content}\"\"\"))\\n'
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
            new_template_path = new_template_path.replace(".json_template.json", "_template.json")
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

        # Determine the correct template filename with extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".json":
            template_filename = f"{name_without_ext}_template.json"
        else:
            template_filename = f"{name_without_ext}_template.py"

        # Determine template subdirectory
        template_subdir = self._get_fallback_subdirectory(file_path)

        # Create template file name
        if template_subdir:
            temp_file_name = os.path.join(template_subdir, template_filename)
        else:
            temp_file_name = template_filename
        #
        temp_file_name_chk = os.path.join(
            self.origialTemplatePath, os.path.relpath(file_path, self.project_root), temp_file_name
        )

        temp_file_name = os.path.join(self.origialTemplatePath, temp_file_name)
        printIt(f"temp_file_name_chk: {temp_file_name_chk}", lable.DEBUG)
        printIt(f"temp_file_name: {temp_file_name}", lable.DEBUG)

        # Calculate MD5
        file_md5 = calculate_md5(file_path)

        # Add to sync data
        self.sync_data[file_path] = {
            "fileMD5": file_md5,
            "template": template_name,
            "tempFileName": temp_file_name,
        }

        self._save_sync_data()

    def track_template(self):
        \"\"\"Track a file for template synchronization\"\"\"
        args = self.args if hasattr(self, "args") else None
        if not args:
            printIt("No arguments provided for track action", lable.ERROR)
            return

        theArgs = args.arguments
        theArgs, optArgs = split_args(theArgs, ["track"])

        if not theArgs:
            printIt("No file specified for 'track' action", lable.ERROR)
            return

        for arg in theArgs:
            # Check if arg is a file path that exists
            if os.path.exists(arg):
                # Handle as existing file path
                rel_path = os.path.relpath(arg, self.project_root) if os.path.isabs(arg) else arg
                if rel_path in self.sync_data:
                    printIt(f"File already tracked: {rel_path}", lable.WARN)
                    continue

                # Remove from doNotTrack list if it exists there
                if "doNotTrack" in self.sync_data and rel_path in self.sync_data["doNotTrack"]:
                    self.sync_data["doNotTrack"].remove(rel_path)
                    printIt(f"Removed from doNotTrack list: {rel_path}", lable.INFO)

                # Create template and add to tracking
                success = self._make_template_from_file(arg)
                if success:
                    self.add_file_to_sync_data(arg)
                    printIt(f"Successfully started tracking: {rel_path}", lable.INFO)
                else:
                    printIt(f"Failed to create template for: {rel_path}", lable.ERROR)
            else:
                # Handle as keyword - find associated files
                associated_files = self._find_files_by_keyword(arg)

                if not associated_files:
                    printIt(
                        f"No files found associated with keyword '{arg}' and file '{arg}' does not exist", lable.WARN
                    )
                    continue

                printIt(f"Found {len(associated_files)} files associated with '{arg}':", lable.INFO)

                # Show files that would be tracked and ask for confirmation
                for file_path in associated_files:
                    rel_path = os.path.relpath(file_path, self.project_root)
                    printIt(f"  {cStr(rel_path, color.CYAN)}", lable.INFO)

                # Ask for confirmation to track and make templates
                try:
                    response = (
                        input(f"\\nTrack all {len(associated_files)} files and create templates? (y/N): ")
                        .strip()
                        .lower()
                    )
                    if not response or response[0] != "y":
                        printIt(f"Cancelled tracking files for '{arg}'", lable.WARN)
                        continue
                except (KeyboardInterrupt, EOFError):
                    printIt(f"\\nCancelled tracking files for '{arg}'", lable.WARN)
                    continue

                # Track all associated files
                success_count = 0
                for file_path in associated_files:
                    rel_path = os.path.relpath(file_path, self.project_root)

                    # Check if already tracked
                    if rel_path in self.sync_data:
                        printIt(f"File already tracked: {rel_path}", lable.WARN)
                        continue

                    # Create template and add to tracking
                    success = self._make_template_from_file(file_path)
                    if success:
                        self.add_file_to_sync_data(file_path)
                        printIt(f"Successfully started tracking: {rel_path}", lable.INFO)
                        success_count += 1
                    else:
                        printIt(f"Failed to create template for: {rel_path}", lable.ERROR)

                if success_count > 0:
                    printIt(
                        f"Successfully tracked {success_count}/{len(associated_files)} files for '{arg}'", lable.INFO
                    )

    def untrack_template(self):
        \"\"\"Remove a file from template synchronization tracking\"\"\"
        args = self.args if hasattr(self, "args") else None
        if not args:
            printIt("No arguments provided for untrack action", lable.ERROR)
            return

        theArgs = args.arguments
        theArgs, optArgs = split_args(theArgs, ["untrack"])

        if not theArgs:
            printIt("No file specified for 'untrack' action", lable.ERROR)
            return

        for arg in theArgs:
            # Convert to relative path for consistency
            rel_path = os.path.relpath(arg, self.project_root) if os.path.isabs(arg) else arg

            # Check if file is currently tracked
            if rel_path not in self.sync_data:
                # Check if it's in the doNotTrack list
                if "doNotTrack" in self.sync_data and rel_path in self.sync_data["doNotTrack"]:
                    self.sync_data["doNotTrack"].remove(rel_path)
                    self._save_sync_data()
                    printIt(f"Removed from doNotTrack list: {rel_path}", lable.INFO)
                    continue

                # Try to find by template name or partial match
                found_key = None
                for key in self.sync_data.keys():
                    if key in ["fields", "doNotTrack"]:
                        continue
                    # Check if basename matches
                    if os.path.basename(key) == os.path.basename(rel_path):
                        found_key = key
                        break
                    # Check if it's a template name match
                    if key.endswith(arg) or arg.endswith(os.path.basename(key)):
                        found_key = key
                        break

                if not found_key:
                    printIt(f"File not currently tracked or in doNotTrack list: {rel_path}", lable.WARN)
                    continue
                rel_path = found_key

            # Remove from tracking
            file_info = self.sync_data[rel_path]
            del self.sync_data[rel_path]

            # Also try to remove the template file if it exists
            if "tempFileName" in file_info:
                template_path = os.path.join(self.new_templates_dir, os.path.basename(file_info["tempFileName"]))
                if os.path.exists(template_path):
                    try:
                        os.remove(template_path)
                        printIt(f"Removed template file: {os.path.basename(template_path)}", lable.INFO)
                    except Exception as e:
                        printIt(f"Could not remove template file {template_path}: {e}", lable.WARN)

            self._save_sync_data()
            printIt(f"Successfully stopped tracking: {rel_path}", lable.INFO)

    def notrack_file(self):
        \"\"\"Add files to the doNotTrack list to exclude them from tracking consideration\"\"\"
        args = self.args if hasattr(self, "args") else None
        if not args:
            printIt("No arguments provided for notrack action", lable.ERROR)
            return

        theArgs = args.arguments
        theArgs, optArgs = split_args(theArgs, ["notrack"])

        if not theArgs:
            printIt("No file specified for 'notrack' action", lable.ERROR)
            return

        # Ensure doNotTrack list exists in sync_data
        if "doNotTrack" not in self.sync_data:
            self.sync_data["doNotTrack"] = []

        for arg in theArgs:
            # Convert to relative path for consistency
            rel_path = os.path.relpath(arg, self.project_root) if os.path.isabs(arg) else arg

            # Check if already in doNotTrack list
            if rel_path in self.sync_data["doNotTrack"]:
                printIt(f"File already in doNotTrack list: {rel_path}", lable.WARN)
                continue

            # Check if currently tracked - if so, warn user
            if rel_path in self.sync_data:
                printIt(
                    f"Warning: File '{rel_path}' is currently being tracked. Use 'untrack' first if you want to stop tracking it.",
                    lable.WARN,
                )
                continue

            # Add to doNotTrack list
            self.sync_data["doNotTrack"].append(rel_path)
            printIt(f"Added to doNotTrack list: {rel_path}", lable.INFO)

        # Save the updated sync data
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
        if not os.path.exists(self.origialTemplatePath):
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
            f"{len(newtemplates_files)} templates ready for transfer\\n    from: {self.new_templates_dir}\\n      to: {self.origialTemplatePath}",
            lable.INFO,
        )

        inputStr = input("\\nProceed with transfer? (y/n/List): ")
        if len(inputStr) == 0:
            inputStr = "l"
        if inputStr.lower()[0] == "n":
            printIt("Transfer cancelled by user", lable.WARN)
            return
        elif len(inputStr) == 0 or inputStr.lower()[0] == "l":
            printIt("\\nTemplates to be transferred:", lable.INFO)
            # Show all templates first
            for source_file_name in newtemplates_files:
                file_name = os.path.basename(source_file_name)
                printIt(f"  {cStr(file_name, color.YELLOW)}", lable.INFO)

            # Then ask for confirmation once
            inputStr = input("\\nProceed with transfer? (Y/n): ")
            if len(inputStr) == 0:
                inputStr = "y"
            if inputStr.lower()[0] != "y":
                printIt("Transfer cancelled by user", lable.WARN)
                return

        # Copy all files from newTemplates to origialTemplatePath
        for source_file_name in newtemplates_files:
            # construnct target file name
            rel_path = os.path.relpath(source_file_name, self.new_templates_dir)
            target_file_name = os.path.join(self.origialTemplatePath, rel_path)
            try:
                target_dir = os.path.dirname(target_file_name)
                if not os.path.exists(target_dir):
                    printIt(f"No target directory found: {target_dir}", lable.WARN)
                    printIt(f"Skipping template transfer for {source_file_name} ", lable.INFO)
                else:
                    shutil.copy2(source_file_name, target_file_name)
                    printIt(cStr(os.path.basename(target_file_name), color.YELLOW), lable.SAVED)
            except Exception as e:
                printIt(
                    f"Error transferring template to {target_file_name}: {e}",
                    lable.ERROR,
                )

    def list_tracked_files(self, directory_filter: Optional[str] = None):
        \"\"\"List all tracked files in a formatted style\"\"\"
        if not self.sync_data:
            printIt("No sync data available", lable.ERROR)
            return

        tracked_files = []
        for file_path, file_info in self.sync_data.items():
            if file_path in ["fields", "doNotTrack"] or not isinstance(file_info, dict):
                continue

            # Convert absolute paths to relative
            if file_path.startswith("/"):
                rel_path = os.path.relpath(file_path, self.project_root)
            else:
                rel_path = file_path

            # Apply directory filter if specified
            if directory_filter:
                # Normalize paths for comparison
                rel_dir = os.path.dirname(rel_path)

                # Check if the file's directory matches the filter
                filter_match = False

                # Root level files when filter is ".", "", or "root"
                if directory_filter in [".", "", "root"]:
                    if rel_dir == "":
                        filter_match = True
                # Exact directory match
                elif rel_dir == directory_filter:
                    filter_match = True
                # Starts with filter (for subdirectories) - more precise check
                elif directory_filter != "." and (
                    rel_dir.startswith(directory_filter + "/") or rel_dir.startswith(directory_filter + "\\\\")
                ):
                    filter_match = True
                # Check if just the directory basename matches (e.g., "templates" matches "src/commands/templates")
                elif directory_filter != "." and os.path.basename(rel_dir) == directory_filter:
                    filter_match = True

                if not filter_match:
                    continue

            # Get file stats if file exists
            abs_path = file_path if os.path.isabs(file_path) else os.path.join(self.project_root, file_path)
            if os.path.exists(abs_path):
                try:
                    import datetime

                    mod_time = os.path.getmtime(abs_path)
                    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                    tracked_files.append((rel_path, mod_time_str))
                except Exception:
                    tracked_files.append((rel_path, "unknown date"))
            else:
                tracked_files.append((rel_path, "MISSING"))

        tracked_files.sort()

        # Header with 80 col color formatting
        if directory_filter:
            theLable = cStr(f"Tracked Files in {directory_filter}", color.GREEN)
        else:
            theLable = cStr("Tracked Files", color.GREEN)
        printIt(f"{'-' * 10} {theLable} {'-' * (80-9-len(theLable))}", lable.INFO)

        if not tracked_files and directory_filter:
            printIt(f"  No tracked files found matching filter: {directory_filter}", lable.WARN)
            return

        for file_path, mod_time_str in tracked_files:
            printIt(f"  {cStr(file_path, color.GREEN):60} {mod_time_str}", lable.INFO)

        filter_text = f" (filtered by {directory_filter})" if directory_filter else ""
        print(f"     Total tracked files{filter_text}: {len(tracked_files)}")

    def list_untracked_files(self, directory_filter: Optional[str] = None):
        \"\"\"List files that could be tracked but aren't in formatted style\"\"\"
        untracked_files = self._discover_untracked_files(verbose=False)

        if not untracked_files:
            printIt("No untracked files found", lable.INFO)
            return

        # Prepare file data with modification times
        file_data = []
        for file_path in untracked_files:
            rel_path = os.path.relpath(file_path, self.project_root)

            # Apply directory filter if specified
            if directory_filter:
                # Normalize paths for comparison
                rel_dir = os.path.dirname(rel_path)

                # Check if the file's directory matches the filter
                filter_match = False

                # Root level files when filter is ".", "", or "root"
                if directory_filter in [".", "", "root"]:
                    if rel_dir == "":
                        filter_match = True
                # Exact directory match
                elif rel_dir == directory_filter:
                    filter_match = True
                # Starts with filter (for subdirectories) - more precise check
                elif directory_filter != "." and (
                    rel_dir.startswith(directory_filter + "/") or rel_dir.startswith(directory_filter + "\\\\")
                ):
                    filter_match = True
                # Check if just the directory basename matches (e.g., "templates" matches "src/commands/templates")
                elif directory_filter != "." and os.path.basename(rel_dir) == directory_filter:
                    filter_match = True

                if not filter_match:
                    continue

            try:
                import datetime

                mod_time = os.path.getmtime(file_path)
                mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                file_data.append((rel_path, mod_time_str))
            except Exception:
                file_data.append((rel_path, "unknown date"))

        file_data.sort()

        # Header with 80 col color formatting

        if directory_filter:
            theLable = cStr(f"Untracked Files in {directory_filter}", color.CYAN)
        else:
            theLable = cStr("Untracked Files", color.CYAN)
        printIt(f"{'-' * 10} {theLable} {'-' * (80-9-len(theLable))}", lable.INFO)

        if not file_data and directory_filter:
            printIt(f"  No untracked files found matching filter: {directory_filter}", lable.WARN)
            return

        for file_path, mod_time_str in file_data:
            printIt(f"  {cStr(file_path, color.CYAN):60} {mod_time_str}", lable.INFO)

        filter_text = f" (filtered by {directory_filter})" if directory_filter else ""
        print(f"     Total untracked files{filter_text}: {len(file_data)}")

    def list_not_tracked_files(self, directory_filter: Optional[str] = None):
        \"\"\"List files in the doNotTrack list in formatted style\"\"\"
        do_not_track = self.sync_data.get("doNotTrack", [])

        if not do_not_track:
            printIt("No files in doNotTrack list", lable.INFO)
            return

        # Prepare file data with modification times if files exist
        file_data = []
        for file_pattern in do_not_track:
            # Convert pattern to relative path for filtering
            if file_pattern.startswith("/"):
                rel_pattern = os.path.relpath(file_pattern, self.project_root)
            else:
                rel_pattern = file_pattern

            # Apply directory filter if specified
            if directory_filter:
                # Normalize paths for comparison
                rel_dir = os.path.dirname(rel_pattern)

                # Check if the file's directory matches the filter
                filter_match = False

                # Root level files when filter is ".", "", or "root"
                if directory_filter in [".", "", "root"]:
                    if rel_dir == "":
                        filter_match = True
                # Exact directory match
                elif rel_dir == directory_filter:
                    filter_match = True
                # Starts with filter (for subdirectories) - more precise check
                elif directory_filter != "." and (
                    rel_dir.startswith(directory_filter + "/") or rel_dir.startswith(directory_filter + "\\\\")
                ):
                    filter_match = True
                # Check if just the directory basename matches (e.g., "templates" matches "src/commands/templates")
                elif directory_filter != "." and os.path.basename(rel_dir) == directory_filter:
                    filter_match = True

                if not filter_match:
                    continue

            # Try to get file stats if it's a real file
            abs_path = file_pattern if os.path.isabs(file_pattern) else os.path.join(self.project_root, file_pattern)
            if os.path.exists(abs_path):
                try:
                    import datetime

                    mod_time = os.path.getmtime(abs_path)
                    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                    file_data.append((rel_pattern, mod_time_str))
                except Exception:
                    file_data.append((rel_pattern, "unknown date"))
            else:
                file_data.append((rel_pattern, "pattern/missing"))

        file_data.sort()

        # Header with 80 col color formatting
        if directory_filter:
            theLable = cStr(f"Do Not Track Files in {directory_filter}", color.YELLOW)
        else:
            theLable = cStr("Do Not Track Files", color.YELLOW)
        printIt(f"{'-' * 10} {theLable} {'-' * (80-9-len(theLable))}", lable.INFO)

        if not file_data and directory_filter:
            printIt(f"  No doNotTrack files found matching filter: {directory_filter}", lable.WARN)
            return

        for file_pattern, mod_time_str in file_data:
            printIt(f"  {cStr(file_pattern, color.YELLOW):60} {mod_time_str}", lable.INFO)

        filter_text = f" (filtered by {directory_filter})" if directory_filter else ""
        print(f"     Total doNotTrack entries{filter_text}: {len(file_data)}")

    def list_new_files(self, directory_filter: Optional[str] = None):
        \"\"\"List all templates in the newTemplates directory, optionally filtered by directory path\"\"\"
        if not os.path.exists(self.new_templates_dir):
            printIt(
                f"New templates directory not found: {self.new_templates_dir}",
                lable.ERROR,
            )
            return

        # Determine what we're listing
        if directory_filter:
            theLable = cStr(f"Templates in newTemplates/{directory_filter}", color.GREEN)
        else:
            theLable = cStr("Templates in newTemplates directory", color.GREEN)

        printIt(f"{'-' * 10} {theLable} {'-' * (80-9-len(theLable))}", lable.INFO)

        template_count = 0
        for root, dirs, files in os.walk(self.new_templates_dir):
            for file in files:
                template_path = os.path.join(root, file)
                rel_path = os.path.relpath(template_path, self.new_templates_dir)

                # Apply directory filter if specified
                if directory_filter:
                    # Normalize paths for comparison
                    rel_dir = os.path.dirname(rel_path)

                    # Check if the file's directory matches the filter
                    filter_match = False

                    # Root level files when filter is ".", "", or "root"
                    if directory_filter in [".", "", "root"]:
                        if rel_dir == "":
                            filter_match = True
                    # Exact directory match
                    elif rel_dir == directory_filter:
                        filter_match = True
                    # Starts with filter (for subdirectories) - more precise check
                    elif directory_filter != "." and (
                        rel_dir.startswith(directory_filter + "/") or rel_dir.startswith(directory_filter + "\\\\")
                    ):
                        filter_match = True
                    # Check if just the directory basename matches (e.g., "templates" matches "src/commands/templates")
                    elif directory_filter != "." and os.path.basename(rel_dir) == directory_filter:
                        filter_match = True

                    if not filter_match:
                        continue

                # Show file size and modification time
                try:
                    stat_info = os.stat(template_path)
                    file_size = stat_info.st_size
                    mod_time = os.path.getmtime(template_path)
                    import datetime

                    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")

                    # Remove redundant directory portion from display when filtering
                    display_path = rel_path
                    if directory_filter and directory_filter not in [".", "", "root"]:
                        # If the path starts with the filter, remove that portion
                        if rel_path.startswith(directory_filter + "/") or rel_path.startswith(directory_filter + "\\\\"):
                            display_path = rel_path[len(directory_filter) + 1 :]  # +1 to remove the slash
                        # If it's an exact directory match, show just the filename
                        elif os.path.dirname(rel_path) == directory_filter:
                            display_path = os.path.basename(rel_path)

                    printIt(f"  {cStr(display_path, color.GREEN):60} {mod_time_str}", lable.INFO)
                    template_count += 1
                except Exception as e:
                    printIt(f"  {cStr(rel_path, color.YELLOW):50} (error reading file info)", lable.INFO)
                    template_count += 1

        if template_count == 0:
            if directory_filter:
                printIt(f"  No templates found matching filter: {directory_filter}", lable.WARN)
            else:
                printIt("  No templates found", lable.WARN)
        else:
            filter_text = f" (filtered by {directory_filter})" if directory_filter else ""
            print(f"     Total templates{filter_text}: {template_count}")


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
                # Store original arguments length to detect if arguments were consumed
                original_args = theArgs[:]

                # Dynamically calls use handle_ prefix to map to methods.
                getattr(self.module, method_name)(self.argParse)

                # Handle special cases where functions consume multiple arguments
                if method_name == "listFiles":
                    # listFiles consumes up to 2 additional arguments (type and optional directory filter)
                    # Skip to after all consumed arguments
                    remaining_args = len(theArgs) - argIndex - 1  # How many args are left after current
                    if remaining_args >= 2:
                        # Both type and directory filter provided
                        argIndex += 3  # Skip listFiles, type, and directory_filter
                    elif remaining_args >= 1:
                        # Only type provided
                        argIndex += 2  # Skip listFiles and type
                    else:
                        # No additional args
                        argIndex += 1  # Skip just listFiles
                elif method_name in ["untrack", "track", "notrack"]:
                    # untrack, track, and notrack consume all remaining arguments as filenames
                    # Skip to end of arguments since they process all remaining args
                    argIndex = len(theArgs)
                else:
                    argIndex += 1
            else:
                # Invalid function name - provide helpful warning
                valid_functions = ["status", "scanFiles", "listFiles", "sync", "trans", "track", "untrack", "notrack"]
                printIt(f"Unknown tmplMgt function: '{method_name}'", lable.WARN)
                printIt(f"Valid tmplMgt functions are: {', '.join(valid_functions)}", lable.INFO)
                argIndex += 1

    def get_external_helpers(self):
        \"\"\"Gets and returns the names of all module-level functions.\"\"\"

        # 1. Get all members (attributes) of the current module
        all_members = inspect.getmembers(self.module)

        # 2. Filter the members
        function_names = [
            name
            for name, obj in all_members
            if inspect.isfunction(obj)
            and obj.__module__
            == __name__  # Check if it's a function object  # Ensure it's defined in THIS file, not imported
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
    \"\"\"Show status of all tracked files or files matching patterns\"\"\"
    syncer = TemplateSyncer(argParse)

    args = argParse.args
    theArgs = args.arguments
    theArgs, optArgs = split_args(theArgs, ["status"])

    file_patterns = []
    for arg in theArgs:
        file_patterns.append(arg)

    if file_patterns:
        printIt(
            f"Showing status for files matching patterns: {', '.join(file_patterns)}",
            lable.INFO,
        )

    syncer.show_status(file_patterns if file_patterns else None)


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


def listFiles(argParse):
    \"\"\"Unified list command for different file categories\"\"\"
    syncer = TemplateSyncer(argParse)

    args = argParse.args
    theArgs = args.arguments
    theArgs, optArgs = split_args(theArgs, ["listFiles"])

    if len(theArgs) == 0:
        # Default to showing help
        printIt("Usage: ${packName} tmplMgt listFiles <type>", lable.INFO)
        printIt("Available types:", lable.INFO)
        printIt(f"  {cStr('tracked', color.GREEN)}   - Show all tracked files", lable.INFO)
        printIt(f"  {cStr('untracked', color.CYAN)} - Show files that could be tracked but aren't", lable.INFO)
        printIt(f"  {cStr('noTracked', color.YELLOW)} - Show files in doNotTrack list", lable.INFO)
        printIt(f"  {cStr('new', color.GREEN)}       - Show generated template files", lable.INFO)
        return

    list_type = theArgs[0].lower()
    directory_filter = theArgs[1] if len(theArgs) > 1 else None

    if list_type in ["tracked", "tk", "trackedFiles", "tracked-files"]:
        syncer.list_tracked_files(directory_filter)
    elif list_type in ["untracked", "utk", "untrackedFiles", "untracked-files"]:
        syncer.list_untracked_files(directory_filter)
    elif list_type in ["notracked", "notk", "nottracked", "not-tracked"]:
        syncer.list_not_tracked_files(directory_filter)
    elif list_type in ["new", "newFiles", "new-files"]:
        syncer.list_new_files(directory_filter)
    else:
        printIt(f"Unknown list type: {list_type}", lable.WARN)
        printIt("Valid types: tracked, untracked, noTracked, new", lable.INFO)


def trans(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.transfer_templates()


def scanFiles(argParse):
    \"\"\"Show detailed file discovery report including exclusions\"\"\"
    syncer = TemplateSyncer(argParse)

    printIt(f"{cStr('File Discovery Scan Report', color.BLUE)}", lable.INFO)
    printIt("=" * 80, lable.INFO)

    # Run discovery in verbose mode
    untracked_files = syncer._discover_untracked_files(verbose=True)

    printIt(f"\\n{cStr('Summary:', color.GREEN)}", lable.INFO)
    printIt(f"  Untracked files found: {len(untracked_files)}", lable.INFO)

    if untracked_files:
        printIt(f"\\n{cStr('Untracked Files:', color.CYAN)}", lable.INFO)
        for file_path in untracked_files:
            rel_path = os.path.relpath(file_path, syncer.project_root)
            printIt(f"  {rel_path}", lable.INFO)


def track(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.track_template()


def untrack(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.untrack_template()


def notrack(argParse):
    syncer = TemplateSyncer(argParse)
    syncer.notrack_file()
"""))

