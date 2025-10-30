#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to extract remaining templates from cmdTemplate.py
This script will complete the template extraction process by identifying
and extracting all remaining template objects from the large cmdTemplate.py file.
"""

import os
import re
from pathlib import Path

def extract_template_from_cmdtemplate():
    """Extract all remaining templates from cmdTemplate.py"""
    
    # Read the original cmdTemplate.py file
    cmdtemplate_path = "/Users/primwind/proj/python/cmdpackage/src/cmdpackage/templates/cmdTemplate.py"
    templates_base = "/Users/primwind/proj/python/cmdpackage/templates"
    
    with open(cmdtemplate_path, 'r') as f:
        content = f.read()
    
    # Templates we still need to extract based on the templateSources mapping
    remaining_templates = {
        "commandsJsonDict": "src/src_templates/commands/commandsJsonDict.json",
        "commandsFileStr": "src/src_templates/commands/commandsFileStr.py", 
        "cmdSwitchbordFile": "src/src_templates/commands/cmdSwitchbordFile.py",
        "cmdOptSwitchbordFileStr": "src/src_templates/commands/cmdOptSwitchbordFileStr.py",
        "newCmdTemplate": "src/src_templates/commands/newCmdTemplate.py",
        "modCmdTemplate": "src/src_templates/commands/modCmdTemplate.py", 
        "rmCmdTemplate": "src/src_templates/commands/rmCmdTemplate.py",
        "runTestTemplate": "src/src_templates/commands/runTestTemplate.py",
        "fileDiffTemplate": "src/src_templates/commands/fileDiffTemplate.py",
        "syncTemplate": "src/src_templates/commands/syncTemplate.py"
    }
    
    # Regular expression to find template definitions
    template_pattern = r'(\w+)\s*=\s*(Template\(|dedent\()\s*\n'
    
    # Find all template definitions
    matches = re.finditer(template_pattern, content)
    
    template_locations = {}
    for match in matches:
        template_name = match.group(1)
        start_pos = match.start()
        template_locations[template_name] = start_pos
    
    print(f"Found {len(template_locations)} template definitions")
    
    # Extract each remaining template
    for template_name, target_path in remaining_templates.items():
        if template_name in template_locations:
            print(f"Extracting {template_name}...")
            
            # Find the template content
            start_pos = template_locations[template_name]
            
            # Find the end of this template by looking for the next template or end of file
            next_template_pos = len(content)
            for other_name, other_pos in template_locations.items():
                if other_pos > start_pos and other_pos < next_template_pos:
                    next_template_pos = other_pos
            
            # Extract the template definition
            template_content = content[start_pos:next_template_pos].strip()
            
            # Add the standard header
            file_content = '''#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

''' + template_content
            
            # Create the target file
            full_target_path = os.path.join(templates_base, target_path)
            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
            
            with open(full_target_path, 'w') as f:
                f.write(file_content)
            
            print(f"  Created: {full_target_path}")
        else:
            print(f"Warning: Template {template_name} not found in cmdTemplate.py")

if __name__ == "__main__":
    extract_template_from_cmdtemplate()
    print("Template extraction completed!")