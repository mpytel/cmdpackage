#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
from cmdpackage.defs.utilities import chkDir
import cmdpackage.templates.test_newCmd_roundtrip as test_newCmd_roundtrip
import cmdpackage.templates.test_modCmd_roundtrip as test_modCmd_roundtrip
import cmdpackage.templates.test_rmCmd_roundtrip as test_rmCmd_roundtrip
import cmdpackage.templates.test_argCmdDef_roundtrip as test_argCmdDef_roundtrip


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
        Main method to write all test scripts.
        """
        # Ensure test directory exists
        chkDir(self.test_dir)
        
        # Write individual test scripts
        self._write_new_cmd_test()
        self._write_mod_cmd_test()
        self._write_rm_cmd_test()
        self._write_arg_cmd_def_test()
        
        # Update temp sync data
        self._write_temp_sync_data()
        
    def _write_new_cmd_test(self) -> None:
        """Write test_newCmd_roundtrip.py test script."""
        file_name = os.path.join(self.test_dir, "test_newCmd_roundtrip.py")
        file_str = test_newCmd_roundtrip.test_newCmd_roundtrip_template.substitute(
            packName=self.program_name)
        
        with open(file_name, "w") as wf:
            wf.write(file_str)
        
        # Make executable
        # self._make_executable(file_name)
        
        # Track for sync data
        self._temp_sync_file_json("test_newCmd_roundtrip_template", 
                                  test_newCmd_roundtrip.__file__,
                                  file_name, file_str)
        
    def _write_mod_cmd_test(self) -> None:
        """Write test_modCmd_roundtrip.py test script."""
        file_name = os.path.join(self.test_dir, "test_modCmd_roundtrip.py")
        file_str = test_modCmd_roundtrip.test_modCmd_roundtrip_template.substitute(
            packName=self.program_name)
        
        with open(file_name, "w") as wf:
            wf.write(file_str)
        
        # Make executable
        #self._make_executable(file_name)
        
        # Track for sync data
        self._temp_sync_file_json("test_modCmd_roundtrip_template",
                                  test_modCmd_roundtrip.__file__,
                                  file_name, file_str)
        
    def _write_rm_cmd_test(self) -> None:
        """Write test_rmCmd_roundtrip.py test script."""
        file_name = os.path.join(self.test_dir, "test_rmCmd_roundtrip.py")
        file_str = test_rmCmd_roundtrip.test_rmCmd_roundtrip_template.substitute(
            packName=self.program_name)
        
        with open(file_name, "w") as wf:
            wf.write(file_str)
        
        # Make executable
        self._make_executable(file_name)
        
        # Track for sync data
        self._temp_sync_file_json("test_rmCmd_roundtrip_template",
                                  test_rmCmd_roundtrip.__file__,
                                  file_name, file_str)
        
    def _write_arg_cmd_def_test(self) -> None:
        """Write test_argCmdDef_roundtrip.py test script."""
        file_name = os.path.join(self.test_dir, "test_argCmdDef_roundtrip.py")
        file_str = test_argCmdDef_roundtrip.test_argCmdDef_roundtrip_template.substitute(
            packName=self.program_name)
        
        with open(file_name, "w") as wf:
            wf.write(file_str)
        
        # Make executable
        self._make_executable(file_name)
        
        # Track for sync data
        self._temp_sync_file_json("test_argCmdDef_roundtrip_template",
                                  test_argCmdDef_roundtrip.__file__,
                                  file_name, file_str)
        
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