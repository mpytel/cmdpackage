#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

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
                    placeholder = '$${' + placeholder_name + '}'
                    # Special handling for 'name' field (packName) which appears in compound words
                    if field_key == 'name':
                        # Handle compound patterns like "${packName}rc", "syncTemplates", etc.
                        compound_patterns = [
                            (f'{field_value}rc', f'$${{{placeholder_name}}}rc'),
                            (f'{field_value}Templates', f'$${{{placeholder_name}}}Templates'),
                            (f'.{field_value}rc', f'.$${{{placeholder_name}}}rc'),
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