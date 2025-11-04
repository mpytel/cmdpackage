#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
import importlib
from string import Template
from cmdpackage.defs.utilities import chkDir, load_template, sanitize_var_name
from cmdpackage.defs.logIt import printIt, lable

class WriteTestScript:
    """
    A class for writing test script files for CLI packages.
    
    This class handles the creation of test scripts for various command functionalities
    including newCmd, modCmd, rmCmd, and argCmdDef roundtrip tests.
    """
    
    def __init__(self, fields: dict, gen_temp_sync_data_write: bool = False):
        """
        Initialize the WriteTestScript with project configuration.
        
        Args:
            fields (dict): Dictionary containing project configuration fields
            gen_temp_sync_data_write (bool): Flag to control temp sync data writing
        """
        self.fields = fields
        self.gen_temp_sync_data_write = gen_temp_sync_data_write
        self.program_name = fields.get("name", "")
        self.temp_sync_files = {}
        
        # Set up test directory
        self.test_dir = os.path.join(os.path.abspath("."), "tests")
        # Set up base source directory for sync data file
        self.src_dir = os.path.join(os.path.abspath("."), 'src', self.program_name)
    
    def write_test_script(self) -> None:
        """
        Main method to write all test scripts using dynamic discovery.
        """
        # Ensure test directory exists
        chkDir(self.test_dir)
        
        # Discover and write all test scripts
        self._discover_and_write_test_scripts()
        
        # Update temp sync data
        self._write_temp_sync_data()
    
    def _discover_and_write_test_scripts(self) -> None:
        """Discover and process all test templates that begin with 'test_'."""

        # Get the cmdpackage directory and use the new template location
        package_dir = os.path.dirname(os.path.dirname(__file__))  # Go up 2 levels from classes/ to cmdpackage/
        templates_dir = os.path.join(package_dir, "templates", "tests")
        if not os.path.exists(templates_dir):
            printIt(f"Template directory not found: {templates_dir}", lable.WARN)
            return
            
        # Include any templates containing '_test_' and the cleanup helper script
        template_files = [
            f for f in os.listdir(templates_dir)
            if (f.startswith("test_") and f.endswith(".py") or "_test_" in f) and f != "__init__.py"
        ]
        printIt(f"Discovered {len(template_files)} TestScript template sources", lable.INFO)
        
        for template_file in template_files:
            self._process_test_template(template_file)
    
    def _process_test_template(self, template_file: str) -> None:
        """Process a single test template file."""
        TEMPLATE_DIR = "templates"
        TESTS_DIR = "tests"
        try:
            # Remove .py extension to get module name
            module_name = template_file[:-3]
            
            # Load the template file directly from the new templates directory
            package_dir = os.path.dirname(os.path.dirname(__file__))  # Go up 2 levels from classes/ to cmdpackage/
            templates_dir = os.path.join(package_dir, TEMPLATE_DIR, TESTS_DIR)
            template_path = os.path.join(templates_dir, template_file)

            # Load the template file as a module
            module = None
            if os.path.splitext(template_path)[1] == '.py':
                module = load_template(template_path)

            if module is None:
                printIt(f"Could not load template module from {template_path}",lable.WARN)
                return  


            module_name = os.path.splitext(template_path)
            module_name = sanitize_var_name(module_name[0].split(os.path.sep)[-1])
            module_name = module_name.replace(f"_template_template", "_template").replace(f".py", "")

            # Look for template attribute - try common naming patterns
            template_attr_name = f"{module_name}_{TEMPLATE_DIR}"
            template_obj = getattr(module, module_name, None)
            
            if template_obj is None:
                printIt(f"No template attribute '{template_attr_name}' found in {module_name}", lable.WARN)
                available_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
                printIt(f"    Available attributes: {available_attrs}",lable.INFO)
                return
            
            # Generate output filename (remove test_ prefix and add .py)
            output_filename = f"{module_name}.py"
            file_path = os.path.join(self.test_dir, output_filename)
            
            # Handle both Template objects and strings
            if hasattr(template_obj, 'substitute'):
                # It's a Template object
                file_content = template_obj.substitute(packName=self.program_name)
            else:
                # It's a string, wrap it in Template
                template_wrapper = Template(str(template_obj))
                file_content = template_wrapper.substitute(packName=self.program_name)
            
            # Write the file
            with open(file_path, "w") as wf:
                wf.write(file_content)
            
            # Make executable for certain test types
            if "rmCmd" in module_name or "argCmdDef" in module_name:
                self._make_executable(file_path)
            
            # Track for sync data
            module_file_path = module.__file__ or f"cmdpackage.templates.{module_name}"
            self._temp_sync_file_json(template_attr_name, module_file_path, file_path, file_content)
            
            printIt(f"{output_filename}",lable.SAVED)
            
        except Exception as e:
            printIt(f"Processing test template {template_file}: {e}",lable.ERROR)


    def _make_executable(self, file_name: str) -> None:
        """Make a file executable by adding execute permissions."""
        st = os.stat(file_name)
        os.chmod(file_name, st.st_mode | 0o111)  # add execute permissions
        
    def _write_temp_sync_data(self) -> None:
        """Write temporary sync data JSON file by reading existing content and updating it."""
        if self.gen_temp_sync_data_write:
            sync_file_path = os.path.join(os.path.abspath("."), "genTempSyncData.json")
            
            # Read existing sync data if it exists
            existing_data = {}
            if os.path.exists(sync_file_path):
                try:
                    with open(sync_file_path, "r") as rf:
                        existing_data = json.load(rf)
                except (json.JSONDecodeError, FileNotFoundError):
                    # If file is corrupted or doesn't exist, start with empty dict
                    existing_data = {}
            
            # Update existing data with new test script data
            existing_data.update(self.temp_sync_files)
            
            # Write updated data back to file
            with open(sync_file_path, "w") as wf:
                json.dump(existing_data, wf, indent=4)
                
    def _temp_sync_file_json(self, template: str, temp_file_name: str, out_file_name: str, file_str: str) -> None:
        """
        Create a temp sync file JSON entry.
        
        Args:
            template (str): Template name
            temp_file_name (str): Template file name
            out_file_name (str): Output file name
            file_str (str): File content for MD5 hash calculation
            
        Returns:
            None
        """
        if self.gen_temp_sync_data_write:
            file_md5 = md5(file_str.encode('utf-8')).hexdigest()
            self.temp_sync_files[out_file_name] = {
                "fileMD5": file_md5,
                "template": template,
                "tempFileName": temp_file_name
            }


# Convenience function to maintain backward compatibility
def writeTestScript(fields: dict, gen_temp_sync_data_write: bool = False) -> None:
    """
    Backward compatibility function that creates and uses the WriteTestScript class.
    
    Args:
        fields (dict): Dictionary containing project configuration fields
        gen_temp_sync_data_write (bool): Flag to control temp sync data writing
    """
    test_script_writer = WriteTestScript(fields, gen_temp_sync_data_write)
    test_script_writer.write_test_script()