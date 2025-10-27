#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
from cmdpackage.defs.utilities import chkDir
import cmdpackage.templates.cmdTemplate as pyTemplate
import cmdpackage.templates.copilotInstructions_md as mdTempate


class WriteCLIPackage:
    """
    A class for writing CLI package files and directory structure.
    
    This class handles the creation of a complete CLI package structure including
    main files, definitions, classes, commands, and templates.
    """
    
    def __init__(self, fields: dict, gen_temp_sync_data_write: bool = False):
        """
        Initialize the WriteCLIPackage with project configuration.
        
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
        
    def write_cli_package(self) -> None:
        """
        Main method to write the complete CLI package structure.
        """
        print()
        
        # Write package directory files
        self._write_package_files()
        
        # Write defs directory files
        self._write_defs_files()
        
        # Write classes directory files
        self._write_classes_files()
        
        # Write commands directory files
        self._write_commands_files()
        
        # Write command template files
        self._write_command_templates()
        
        # Write template definition files
        self._write_template_definitions()
        
        # Write copilot instructions
        self._write_copilot_instructions()
        
        # Write temp sync data
        self._write_temp_sync_data()

    def _write_package_files(self) -> None:
        """Write main package files."""
        chkDir(self.src_dir)
        
        # Write main.py
        file_name = os.path.join(self.src_dir, "main.py")
        file_str = pyTemplate.mainFile
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("mainFile", pyTemplate.__file__, file_name, file_str)
            
    def _write_defs_files(self) -> None:
        """Write definition files to the defs directory."""
        dir_name = os.path.join(self.src_dir, "defs")
        chkDir(dir_name)
        
        # Write logIt.py
        file_name = os.path.join(dir_name, "logIt.py")
        file_str = pyTemplate.logPrintTemplate.substitute(packName=self.program_name)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("logPrintTemplate", pyTemplate.__file__, file_name, file_str)
            
        # Write validation.py
        file_name = os.path.join(dir_name, "validation.py")
        file_str = pyTemplate.validationTemplate.substitute(packName=self.program_name)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("validationTemplate", pyTemplate.__file__, file_name, file_str)
            
    def _write_classes_files(self) -> None:
        """Write class files to the classes directory."""
        dir_name = os.path.join(self.src_dir, "classes")
        chkDir(dir_name)
        
        # Write argParse.py
        file_name = os.path.join(dir_name, "argParse.py")
        file_str = pyTemplate.argParseTemplate.substitute(
            description=self.description, packName=self.program_name)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("logPrinargParseTemplatetTemplate", pyTemplate.__file__, file_name, file_str)
            
        # Write optSwitches.py
        file_name = os.path.join(dir_name, "optSwitches.py")
        file_str = pyTemplate.optSwitchesTemplate.substitute(packName=self.program_name)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("optSwitchesTemplate", pyTemplate.__file__, file_name, file_str)
            
    def _write_commands_files(self) -> None:
        """Write command files to the commands directory."""
        dir_name = os.path.join(self.src_dir, "commands")
        chkDir(dir_name)
        
        # Write commands.py
        file_name = os.path.join(dir_name, "commands.py")
        file_str = pyTemplate.commandsFileStr
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("commandsFileStr", pyTemplate.__file__, file_name, file_str)
            
        # Write commands.json
        file_name = os.path.join(dir_name, "commands.json")
        with open(file_name, "w") as wf:
            cmd_json = json.dumps(pyTemplate.commandsJsonDict, indent=2)
            wf.write(cmd_json)
        self._temp_sync_file_json("commandsJsonDict", pyTemplate.__file__, file_name, file_str)
            
        # Write cmdSwitchbord.py
        file_name = os.path.join(dir_name, "cmdSwitchbord.py")
        file_str = pyTemplate.cmdSwitchbordFile.substitute(packName=self.program_name)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("cmdSwitchbordFile", pyTemplate.__file__, file_name, file_str)
            
        # Write cmdOptSwitchbord.py
        file_name = os.path.join(dir_name, "cmdOptSwitchbord.py")
        file_str = pyTemplate.cmdOptSwitchbordFileStr
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json("cmdOptSwitchbordFileStr", pyTemplate.__file__, file_name, file_str)
            
    def _write_command_templates(self) -> None:
        """Write command template files."""
        dir_name = os.path.join(self.src_dir, "commands")
        
        cmd_templates_names = ["newCmd", "modCmd", "rmCmd", "runTest"]
        cmd_templates = {
            "newCmd": pyTemplate.newCmdTemplate,
            "modCmd": pyTemplate.modCmdTemplate,
            "rmCmd": pyTemplate.rmCmdTemplate,
            "runTest": pyTemplate.runTestTemplate
        }
        
        for template_name in cmd_templates_names:
            indent = 0
            command_json_dict_str = "commandJsonDict = {\n"
            indent += 4
            command_json_dict_str += " " * indent + \
                f'"{template_name}": {json.dumps(pyTemplate.commandsJsonDict.get(template_name), indent=8)}'
            command_json_dict_str += "\n}"
            
            file_name = os.path.join(dir_name, f"{template_name}.py")
            cmd_templates_str = cmd_templates[template_name].substitute(
                commandJsonDict=command_json_dict_str, packName=self.program_name)
            file_str = str(cmd_templates_str)
            with open(file_name, "w") as wf:
                wf.write(file_str)
            self._temp_sync_file_json(template_name, pyTemplate.__file__, file_name, file_str)
                
    def _write_template_definitions(self) -> None:
        """Write template definition files."""
        dir_name = os.path.join(self.src_dir, "commands", "templates")
        
        template_names = ['asyncDef', 'classCall', 'argCmdDef', 'simple']
        template_name_map = {
            "asyncDef": pyTemplate.asyncDefTemplateStr,
            "classCall": pyTemplate.classCallTemplateStr,
            "argCmdDef": pyTemplate.argCmdDefTemplateStr,
            "simple": pyTemplate.simpleTemplateStr,
        }
        
        for template_name in template_names:
            file_name = os.path.join(dir_name, f"{template_name}.py")
            chkDir(dir_name)
            
            file_str = "from string import Template\n"
            file_str += "from textwrap import dedent\n\n"
            file_str += f'cmdDefTemplate = Template(dedent("""{template_name_map.get(template_name)}\n"""))\n\n'
            if template_name == "argCmdDef":
                file_str += f'argDefTemplate = Template(dedent("""{pyTemplate.argDefTemplateStr}\n"""))'
            with open(file_name, "w") as wf:
                wf.write(file_str)
            self._temp_sync_file_json(template_name, pyTemplate.__file__, file_name, file_str)
                
    def _write_copilot_instructions(self) -> None:
        """Write copilot instructions file."""
        dir_name = os.path.join(os.path.abspath("."), '.github')
        file_name = os.path.join(dir_name, "copilot-instructions.md")
        chkDir(dir_name)
        
        file_str = mdTempate.copilotInstructions_md.substitute(
            packName=self.program_name, version=self.version)
        with open(file_name, "w") as wf:
            wf.write(file_str)
        self._temp_sync_file_json(
            "copilotInstructions_md", mdTempate.__file__, file_name, file_str)
            
    def _write_temp_sync_data(self) -> None:
        """Write temporary sync data JSON file."""
        if self.gen_temp_sync_data_write:
            file_name = os.path.join(os.path.abspath("."), "genTempSyncData.json")
            # print(f'Writing temp sync data to {file_name}')
            with open(file_name, "w") as wf:
                json.dump(self.temp_sync_files, wf, indent=4)
                
    def _temp_sync_file_json(self, template: str, temp_file_name: str, out_file_name: str, file_str: str) -> None:
        """
        Create a temp sync file JSON entry.
        
        Args:
            template (str): Template name
            temp_file_name (str): Template file name
            out_file_name (str): Output file name
            
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
def writeCLIPackage(fields: dict, GenTempSyncDataWrite: bool = False) -> None:
    """
    Backward compatibility function that creates and uses the WriteCLIPackage class.
    
    Args:
        fields (dict): Dictionary containing project configuration fields
        GenTempSyncDataWrite (bool): Flag to control temp sync data writing
    """
    cli_package_writer = WriteCLIPackage(fields, GenTempSyncDataWrite)
    cli_package_writer.write_cli_package()