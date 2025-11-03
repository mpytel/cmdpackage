#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

argDefTemplate_template = Template(dedent("""from string import Template
from textwrap import dedent

argDefTemplate = Template(
    dedent(
        \"\"\"def $${argName}(argParse):
    args = argParse.args
    printIt("def $${defName} executed.", lable.INFO)
    printIt("Modify default behavour in src/${packName}/commands/$${defName}.py", lable.INFO)
    printIt(str(args), lable.INFO)

\"\"\"
    )
)
"""))

