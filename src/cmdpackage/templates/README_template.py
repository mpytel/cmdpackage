#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

# Template source file mappings
templateSources = {"README_template": "README.md"}

README_template = Template(
    dedent(
        """# ${packName}
version: ${version}
framework information and overview for adding commands to ${packName} are provided in README_Command_modifications.md

${description}   
## Overview
TBD
                                     
## Installation
### From Source
```bash
git clone <repository-url>
cd ${packName}
pip install -e .
```
"""
    )
)
