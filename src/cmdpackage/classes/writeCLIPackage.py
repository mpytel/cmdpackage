#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import json
import inspect
import traceback
from string import Template
from hashlib import md5
from cmdpackage.defs.logIt import printIt, lable
from cmdpackage.defs.utilities import chkDir, list_files_os_walk, load_template, sanitize_var_name
# Note: Template imports are now handled dynamically from the new template structure
# Old static imports have been replaced with dynamic template discovery

LABLE_DEBUG = lable.DEBUG
LABLE_DEBUG = lable.ABORTPRT

class WriteCLIPackage:
    """
    Advanced CLI package writer using templateSources for flexible template discovery.
    
    This class discovers templates with templateSources dictionaries and processes them
    based on their configuration, supporting various output types (py, md, json).
    """
    
    def __init__(self, fields: dict, gen_temp_sync_data_write: bool = False):
        """
        Initialize the WriteCLIPackage2 with project configuration.
        
        Args:
            fields (dict): Dictionary containing project configuration fields
            gen_temp_sync_data_write (bool): Flag to control temp sync data writing
        """
        self.fields = fields
        self.gen_temp_sync_data_write = gen_temp_sync_data_write
        self.program_name = fields.get("name", "")
        self.description = fields.get("description", "")
        self.version = fields.get("version", "1.0.0")
        self.temp_sync_files = {}
        self.temp_sync_files['fields'] = fields
        
        # Set up base source directory
        self.src_dir = os.path.join(os.path.abspath("."), 'src', self.program_name)
        
        # Create replacement strings dictionary from fields
        self.repl_strings = self._create_replacement_strings()
        
        # Discover all template modules
        self.template_modules = self._discover_template_sources()

    def write_cli_package(self) -> None:
        """
        Main method to write the complete CLI package structure using templateSources.
        """

        # Process each template source
        for source_name, source_info in self.template_modules.items():
            self._process_template_source(source_name, source_info)

        # Write temp sync data
        self._write_temp_sync_data()

        print("CLI package generation completed!")

    def _create_replacement_strings(self) -> dict:
        """
        Create replacement strings dictionary from fields for template substitution.
        
        Returns:
            dict: Dictionary with replacement strings for templates
        """
        repl_strings = {
            'packName': self.program_name,
            'description': self.description,
            'version': self.version,
            'name': self.program_name,
        }
        
        # Add all fields to replacement strings
        repl_strings.update(self.fields)
        
        return repl_strings

    def _discover_template_sources(self) -> dict:
        """
        Discover all template files from the templates directory structure.
        
        Returns:
            dict: Dictionary mapping template names to their configuration
        """
        discovered_sources = {}
        
        # Base templates directory - get cmdpackage directory
        package_dir = os.path.dirname(os.path.dirname(__file__))  # Go up 2 levels from classes/ to cmdpackage/
        templates_base = os.path.join(package_dir, "templates")
        
        if not os.path.exists(templates_base):
            print(f"Warning: Templates directory not found: {templates_base}")
            return discovered_sources

        # get list of all template files in templates_base and subdirectories
        template_files = list_files_os_walk(templates_base, extensions=('.py', '.json'))

        template_mappings: dict[str, str] = {}
        for template_filename in template_files:
            template_mappings.update(self.get_template_map_entry(template_filename))

        #print(f"Discovered {json.dumps(template_mappings,indent=2)} template mappings.")
        # "src/vc/defs/logIt.py": "templates/src/defs/logIt_template.py"
        # Process each template mapping
        for target_file, template_file_path in template_mappings.items():
            # Get the cmdpackage directory (templates are now in src/cmdpackage/templates/)
            package_dir = os.path.dirname(os.path.dirname(__file__))  # Go up 2 levels from classes/ to cmdpackage/
            full_template_path = os.path.join(package_dir, template_file_path)
            full_template_path = full_template_path

            module_name = os.path.splitext(template_file_path)
            module_name = sanitize_var_name(module_name[0].split(os.path.sep)[-1])
            
            if os.path.exists(full_template_path):
                # Load the template file as a module
                if os.path.splitext(template_file_path)[1] == '.py':
                    module = load_template(full_template_path)

                    try:
                        # Find the template object in the module
                        template_obj = None
                        if hasattr(module, module_name):
                            template_obj = getattr(module, module_name)

                        if LABLE_DEBUG == lable.DEBUG:
                            printIt(f"target_file: {target_file}, module_name: {module_name}", lable.DEBUG)
                            
                        if template_obj is not None:                           
                            discovered_sources[module_name] = {
                                'module': module,
                                'template_obj': template_obj,
                                'target_file': target_file,
                                'source_name': module_name
                            }
                        else:
                            print(f"  Warning: No template found in {module_name}")
                            # Debug: show what attributes are available
                            available_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
                            print(f"    Available attributes: {available_attrs}")
                            
                    except Exception as e:
                        print(f"  Error loading template {template_file_path}: {e}")
                else:
                    root, ext = os.path.splitext(target_file)
                    module_name = module_name + "." + ext
                    with open(full_template_path, "r") as rf:
                        template_str = rf.read()
                    discovered_sources[module_name] = {
                        'module': None,
                        'template_obj': template_str,
                        'target_file': target_file,
                        'source_name': full_template_path
                    }
            else:
                print(f"  Warning: Template file not found: {full_template_path}")
        
        printIt(f"Discovered {len(discovered_sources)} CLIPackage template sources",lable.INFO)

        return discovered_sources

    def get_template_map_entry(self, template_filename: str) -> dict[str, str]:
        """
        Creates a mapping dictionary from a final output path (with self.program_name)
        back to its source template file path.
        
        Args:
            template_filename (str): The absolute path to the source template file.
            self.program_name (str): The name of the target project to insert into the 
                                output path (e.g., '{packName}'). Defaults to '{packName}'.
            
        Returns:
            dict: A dictionary mapping the relative output path to the relative 
                template path. 
        """

        TEMPLATE_DIR = "templates"

        # 1. Get the path portion starting from 'templates/...'
        try:
            # Find the index of the 'templates' directory to get the relative path
            templates_index = template_filename.find(TEMPLATE_DIR)
        except ValueError:
            raise ValueError(
                f"'{TEMPLATE_DIR}' not found in the template path: {template_filename}")

        # The value for the mapping dictionary: 'templates/...'
        relative_template_path = template_filename[templates_index:]
        # Example result: 'templates/src/commands/newCmd_template.py'

        # 2. Derive the output key path

        # Start with the template path relative to the project root (after 'templates/')
        output_key_path = relative_template_path.replace(
            TEMPLATE_DIR + os.path.sep, '', 1)
        # Example result: 'src/commands/newCmd_template.py'

        # Remove the '_template' suffix from the filename part
        root, ext = os.path.splitext(output_key_path)
        fileNameParts = root.split(os.path.sep)
        fileName = fileNameParts[-1]
        fileName = sanitize_var_name(fileName)
        # "commands.json": "src/cmdpackage/templates/src/commands/commands_template.json"
        if fileName.startswith('README")'):
            ext = '.md'  # Special case for README files
        if fileName.endswith('_template'):
            revFileName = fileName[:-len('_template')]
            output_key_path = root[:-len(fileName)] + revFileName + ext
            # Example result: 'src/commands/newCmd.py'
        # 3. Inject the project name ('{packName}') into the path
        # We assume '{packName}' should be inserted after the first directory component (e.g., 'src/').

        path_parts = output_key_path.split(os.path.sep)

        # If the path has at least two components (a root folder and a filename/folder)
        if len(path_parts) > 1 and path_parts[0] in ('src', 'tests', '.github'):
            # Inject the project name after the first directory (e.g., 'src' or 'tests')
            # e.g., ['src', '{packName}', 'commands', 'newCmd.py']
            path_parts.insert(1, self.program_name)

        final_output_key = os.path.join(*path_parts)
        # Example result: 'src/{packName}/commands/newCmd.py'
        # (or just 'README_Command_modifications.py' if it was a root file)

        # 4. Construct and return the mapping dictionary
        return {
            final_output_key: relative_template_path
        }
    
    def _process_template_source(self, source_name: str, source_info: dict) -> None:
        """
        Process a single template source and write its output file.
        
        Args:
            source_name (str): Name of the template source
            source_info (dict): Dictionary containing module, template_obj, target_file, etc.
        """
        module = source_info['module']
        template_obj = source_info['template_obj']
        target_file = source_info['target_file']
        template_name = source_info['source_name']
        
        # Substitute variables in target file path
        target_file_path = Template(target_file).substitute(**self.repl_strings)
        
        # Resolve target file path (support relative paths)
        if target_file_path.startswith('./'):
            file_path = os.path.join(os.path.abspath("."), target_file_path[2:])
        elif target_file_path.startswith('../'):
            file_path = os.path.join(os.path.abspath(".."), target_file_path[3:])
        elif not os.path.isabs(target_file_path):
            file_path = os.path.join(os.path.abspath("."), target_file_path)
        else:
            file_path = target_file_path
        
        # Ensure directory exists
        dir_path = os.path.dirname(file_path)
        chkDir(dir_path)
        
        try:
            # Process template based on type
            if isinstance(template_obj, Template):
                # Template object - check if this is a template definition file
                template_def_names = ['argCmdDef', 'asyncDef', 'classCall', 'simple', 
                                    'commands_templates_argCmdDef', 'commands_templates_argDefTemplate',
                                    'commands_templates_asyncDef', 'commands_templates_classCall', 
                                    'commands_templates_simple']
                if '/templates/' in target_file_path and template_name in template_def_names:
                    # This is a template definition file - write the Template object as-is
                    file_content = self._create_template_definition_file_from_template(template_obj, template_name)
                elif self._is_command_template(template_name):
                    # Handle special command templates that need commandJsonDict
                    file_content = self._process_command_template(template_obj, template_name)
                else:
                    # Regular template substitution
                    file_content = template_obj.substitute(**self.repl_strings)
                    
            elif isinstance(template_obj, dict):
                # Dictionary - convert to JSON
                file_content = json.dumps(template_obj, indent=2)
                    
            elif isinstance(template_obj, str):
                # Check if this is a template definition file (in commands/templates/)
                template_names_to_check = ['argCmdDef_templates', 'argDefTemplate_templates', 'asyncDef_templates',
                                         'classCall_templates', 'simple_templates',
                                         'commands_templates_argCmdDef', 'commands_templates_argDefTemplate',
                                         'commands_templates_asyncDef', 'commands_templates_classCall', 
                                         'commands_templates_simple']
                if '/templates/' in target_file_path and template_name in template_names_to_check:
                    # Handle special template definition files
                    file_content = self._create_template_definition_file(template_obj, template_name)
                elif template_name == 'gitignore':
                    # Gitignore content should not be processed as template (contains $py.class etc)
                    file_content = template_obj
                elif self._is_command_template(template_name) and '$' in template_obj and '${' in template_obj:
                    # String command template that needs commandJsonDict
                    temp_obj = Template(template_obj)
                    file_content = self._process_command_template(temp_obj, template_name)
                elif '$' in template_obj and '${' in template_obj:
                    # String with template variables (must have ${} format to be processed)
                    temp_obj = Template(template_obj)
                    file_content = temp_obj.substitute(**self.repl_strings)
                else:
                    # Plain string
                    file_content = template_obj
                
            else:
                # Other types - convert to string
                file_content = str(template_obj)
            
            # Write file
            with open(file_path, "w") as wf:
                wf.write(file_content)
            
            # Track for temp sync
            if module is not None:
                self._temp_sync_file_json(template_name, module.__file__, file_path, file_content)
            else:
               self._temp_sync_file_json(template_name, template_name, file_path, file_content)

            printIt(target_file_path, lable.SAVED)
            
        except Exception as e:
            tb_str = ''.join(traceback.format_exception(
                None, e, e.__traceback__))
            print(f"Error processing {source_name}: {tb_str}")
    
    def _is_command_template(self, template_name: str) -> bool:
        """
        Check if a template is a command template that needs special commandJsonDict handling.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            bool: True if this is a command template
        """
        # These templates contain function definitions and need commandJsonDict
        # Check both the source name (e.g., 'commands_newCmd') and base template name
        command_templates = [
            'modCmd', 'newCmd', 'rmCmd', 'fileDiff', 'runTest',
            'commands_modCmd', 'commands_newCmd', 'commands_rmCmd', 
            'commands_fileDiff', 'commands_runTest',
            'modCmdTemplate', 'newCmdTemplate', 'rmCmdTemplate',
            'fileDiffTemplate', 'runTestTemplate',
            # Template files in commands/templates/ directory (only those that need commandJsonDict)
            'commands_templates_simple', 'commands_templates_classCall', 'commands_templates_asyncDef'
        ]
        return template_name in command_templates
    
    def _process_command_template(self, template_obj: Template, template_name: str) -> str:
        """
        Process command templates that need special commandJsonDict handling.
        
        Args:
            template_obj (Template): The template object
            template_name (str): Name of the template
            
        Returns:
            str: Processed template content
        """
        # Create commandJsonDict for this specific command
        command_json_dict_str = self._create_command_json_dict(template_name)
        
        # Add commandJsonDict to replacement strings
        extended_repl_strings = self.repl_strings.copy()
        extended_repl_strings['commandJsonDict'] = command_json_dict_str
        
        # Perform substitution
        return template_obj.substitute(**extended_repl_strings)
    
    def _create_command_json_dict(self, template_name: str) -> str:
        """
        Create a commandJsonDict string for a specific command template.
        
        Args:
            template_name (str): Name of the command template
            
        Returns:
            str: Formatted commandJsonDict string
        """
        # Create basic command definition since commandsJsonDict is no longer centralized
        # Each command template now manages its own JSON structure
        command_def = {
            "description": f"Command {template_name}",
            "switchFlags": {}
        }
        
        # Format as Python dictionary assignment
        command_json_dict_str = "commandJsonDict = {\n"
        command_json_dict_str += f'    "{template_name}": {json.dumps(command_def, indent=8)}\n'
        command_json_dict_str += "}"
        
        return command_json_dict_str
    
    def _create_template_definition_file(self, template_str: str, template_name: str) -> str:
        """
        Create a template definition file that exports Template objects.
        
        Args:
            template_str (str): The template string content
            template_name (str): Name of the template
            
        Returns:
            str: Python file content with Template definitions
        """
        file_content = "from string import Template\n"
        file_content += "from textwrap import dedent\n\n"
        
        # Handle different template types
        if 'argDefTemplate' in template_name:
            # Create argDefTemplate from the template string
            file_content += f'argDefTemplate = Template(dedent("""{template_str}"""))\n\n'
        elif 'argCmdDef' in template_name:
            # Create cmdDefTemplate
            file_content += f'cmdDefTemplate = Template(dedent("""{template_str}\n"""))\n\n'
            # argDefTemplate is now in its own file, so we reference it
            file_content += '# argDefTemplate is now available from separate template file'
        else:
            # Default case - create a template with a generic name based on template_name
            template_var_name = template_name.replace('commands_templates_', '').replace('Template', '') + 'Template'
            file_content += f'{template_var_name} = Template(dedent("""{template_str}"""))\n\n'
            
        return file_content
    
    def _create_template_definition_file_from_template(self, template_obj: Template, template_name: str) -> str:
        """
        Create a template definition file from an existing Template object.
        
        Args:
            template_obj (Template): The Template object to write
            template_name (str): Name of the template
            
        Returns:
            str: Python file content with Template definitions
        """
        # Extract the template string from the Template object
        template_str = template_obj.template
        
        file_content = "from string import Template\n"
        file_content += "from textwrap import dedent\n\n"
        
        # Handle different template types
        if 'argDefTemplate' in template_name:
            # This will be argDefTemplate.py containing argDefTemplate (from argCmdDefTemplate)
            file_content += f'argDefTemplate = Template(dedent("""{template_str}"""))\n\n'
        elif 'argCmdDef' in template_name:
            # This will be argCmdDef.py containing argCmdDefTemplate (from argDefTemplateStr)
            file_content += f'argCmdDefTemplate = Template(dedent("""{template_str}"""))\n\n'
        else:
            # Default case - create a template with a generic name based on template_name
            template_var_name = template_name.replace('commands_templates_', '').replace('Template', '') + 'Template'
            file_content += f'{template_var_name} = Template(dedent("""{template_str}"""))\n\n'
            
        return file_content
    
    def _write_temp_sync_data(self) -> None:
        """Write temporary sync data JSON file."""
        if self.gen_temp_sync_data_write:
            file_name = os.path.join(os.path.abspath("."), "genTempSyncData.json")
            print(f'Writing temp sync data to {file_name}')
            with open(file_name, "w") as wf:
                json.dump(self.temp_sync_files, wf, indent=4)
                
    def _temp_sync_file_json(self, template: str, temp_file_name: str, out_file_name: str, file_str: str) -> None:
        """
        Create a temp sync file JSON entry.
        
        Args:
            template (str): Template name
            temp_file_name (str): Template file name
            out_file_name (str): Output file name
            file_str (str): File content string
        """
        if self.gen_temp_sync_data_write:
            file_md5 = md5(file_str.encode('utf-8')).hexdigest()
            self.temp_sync_files[out_file_name] = {
                "fileMD5": file_md5,
                "template": template,
                "tempFileName": temp_file_name
            }


# Convenience function for backward compatibility
def writeCLIPackage(fields: dict, GenTempSyncDataWrite: bool = False) -> None:
    """
    Convenience function that creates and uses the WriteCLIPackage2 class.
    
    Args:
        fields (dict): Dictionary containing project configuration fields
        GenTempSyncDataWrite (bool): Flag to control temp sync data writing
    """
    cli_package_writer = WriteCLIPackage(fields, GenTempSyncDataWrite)
    cli_package_writer.write_cli_package()