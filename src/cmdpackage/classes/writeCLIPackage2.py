#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
import inspect
from string import Template
from cmdpackage.defs.utilities import chkDir
import cmdpackage.templates.cmdTemplate as pyTemplate
import cmdpackage.templates.copilotInstructions_md as mdTemplate


class WriteCLIPackage2:
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
        self.template_modules = self._discover_template_modules()
        
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
    
    def _discover_template_modules(self) -> list:
        """
        Discover all available template modules.
        
        Returns:
            list: List of template modules to process
        """
        modules = [pyTemplate, mdTemplate]
        return modules
    
    def _discover_template_sources(self) -> dict:
        """
        Discover all templateSources dictionaries from template modules.
        
        Returns:
            dict: Dictionary mapping template names to their configuration
        """
        discovered_sources = {}
        
        for module in self.template_modules:
            module_name = module.__name__.split('.')[-1]
            print(f"Scanning module: {module_name}")
            
            # Look for templateSources dictionary
            if hasattr(module, 'templateSources'):
                template_sources = getattr(module, 'templateSources')
                
                if isinstance(template_sources, dict):
                    # Process each template source
                    for source_name, target_file in template_sources.items():
                        # Check if there's a corresponding template object in the module
                        template_obj = None
                        
                        # Try different naming patterns
                        possible_names = [
                            source_name,  # exact match
                            f"{source_name}Template",  # with Template suffix
                            f"{source_name}File",  # with File suffix
                            f"{source_name}Str",   # with Str suffix
                            f"{source_name}TemplateStr"  # with TemplateStr suffix
                        ]
                        
                        for name in possible_names:
                            if hasattr(module, name):
                                template_obj = getattr(module, name)
                                break
                        
                        if template_obj is not None:
                            full_name = f"{module_name}_{source_name}"
                            discovered_sources[full_name] = {
                                'module': module,
                                'template_obj': template_obj,
                                'target_file': target_file,
                                'source_name': source_name
                            }
                            print(f"  Found template: {source_name} -> {target_file}")
                        else:
                            print(f"  Warning: No template found for source '{source_name}'")
        
        print(f"Discovered {len(discovered_sources)} template sources")
        return discovered_sources
    
    def write_cli_package(self) -> None:
        """
        Main method to write the complete CLI package structure using templateSources.
        """
        print("Starting CLI package generation with templateSources discovery...")
        print()
        
        # Discover all template sources
        template_sources = self._discover_template_sources()
        
        # Process each template source
        for source_name, source_info in template_sources.items():
            self._process_template_source(source_name, source_info)
        
        # Write temp sync data
        self._write_temp_sync_data()
        
        print("CLI package generation completed!")
    
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
                # Template object - perform substitution
                # Check if this is a command template that needs commandJsonDict
                if self._is_command_template(template_name):
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
                if '/templates/' in target_file_path and template_name in ['argCmdDef', 'asyncDef', 'classCall', 'simple']:
                    # Handle special template definition files
                    file_content = self._create_template_definition_file(template_obj, template_name)
                elif '$' in template_obj:
                    # String with template variables
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
            self._temp_sync_file_json(template_name, module.__file__, file_path, file_content)
            
            print(f"Generated: {target_file_path} (from {template_name})")
            
        except Exception as e:
            print(f"Error processing {source_name}: {str(e)}")
    
    def _is_command_template(self, template_name: str) -> bool:
        """
        Check if a template is a command template that needs special commandJsonDict handling.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            bool: True if this is a command template
        """
        # These templates contain function definitions and need commandJsonDict
        command_templates = ['modCmd', 'newCmd', 'rmCmd', 'fileDiff', 'runTest']
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
        # Get the command definition from pyTemplate.commandsJsonDict
        command_def = getattr(pyTemplate, 'commandsJsonDict', {}).get(template_name, {})
        
        if not command_def:
            # Fallback: create basic command definition
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
        file_content += f'cmdDefTemplate = Template(dedent("""{template_str}\n"""))\n\n'
        
        # Add argDefTemplate for argCmdDef
        if template_name == "argCmdDef":
            arg_def_template_str = getattr(pyTemplate, 'argDefTemplateStr', '')
            file_content += f'argDefTemplate = Template(dedent("""{arg_def_template_str}\n"""))'
            
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
def writeCLIPackage2(fields: dict, GenTempSyncDataWrite: bool = False) -> None:
    """
    Convenience function that creates and uses the WriteCLIPackage2 class.
    
    Args:
        fields (dict): Dictionary containing project configuration fields
        GenTempSyncDataWrite (bool): Flag to control temp sync data writing
    """
    cli_package_writer = WriteCLIPackage2(fields, GenTempSyncDataWrite)
    cli_package_writer.write_cli_package()