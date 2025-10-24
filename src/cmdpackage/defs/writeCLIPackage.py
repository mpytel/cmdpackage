#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, json
from cmdpackage.defs.utilities import chkDir
from cmdpackage.templates.cmdTemplate import \
    mainFile, logPrintTemplate, \
    commandsFileStr, commandsJsonDict, \
    cmdSwitchbordFileStr, cmdOptSwitchbordFileStr, \
    argParseTemplate, optSwitchesTemplate, \
    newCmdTemplate, modCmdTemplate, rmCmdTemplate, \
    argCmdDefTemplateStr, argDefTemplateStr, \
    asyncDefTemplateStr, classCallTemplateStr, \
    simpleTemplateStr

def writeCLIPackage(fields: dict):
    print()
    field_name = "name"
    programName = fields[field_name]
    # -- package dir files
    ## write __init__.py to package dir from str
    packDir = os.path.join(os.path.abspath("."), 'src', programName)
    #print('packDir:', str(packDir))
    chkDir(packDir)
    fileName = os.path.join(packDir,"main.py")
    with open(fileName,"w") as wf:
        wf.write(mainFile)

    # -- defs dir files
    ## write logPrint.py def for def dir from template
    dirName = os.path.join(packDir,"defs")
    fileName = os.path.join(dirName,"logIt.py")
    fileStr = logPrintTemplate.substitute(packName=programName)
    chkDir(dirName)
    with open(fileName,"w") as wf:
        wf.write(fileStr)

    # -- classes dir files
    #write argPars.py to class directory from template
    field_name = "description"
    description = fields[field_name]
    dirName = os.path.join(packDir,"classes")
    fileName = os.path.join(dirName,"argParse.py")
    fileStr = argParseTemplate.substitute(description=description)
    chkDir(dirName)
    with open(fileName,"w") as wf:
        wf.write(fileStr)
    ## write optSwitches.py to clsass dir from template
    fileName = os.path.join(dirName,"optSwitches.py")
    fileStr = optSwitchesTemplate.substitute(packName=programName)
    with open(fileName,"w") as wf:
        wf.write(fileStr)

    # -- commands dir files
    ## write commands.py Commands class file
    dirName = os.path.join(packDir,"commands")
    fileName = os.path.join(dirName,"commands.py")
    chkDir(dirName)
    with open(fileName,"w") as wf:
        wf.write(commandsFileStr)
    # write commands.json to commands dir from dict
    fileName = os.path.join(dirName,"commands.json")
    with open(fileName,"w") as wf:
        cmdJson = json.dumps(commandsJsonDict,indent=2)
        wf.write(cmdJson)
    ## write cmdSwitchbord.py to def dir from str
    fileName = os.path.join(dirName,"cmdSwitchbord.py")
    with open(fileName,"w") as wf:
        wf.write(cmdSwitchbordFileStr)
    ## write cmdOptSwitchbord.py to def dir from str
    fileName = os.path.join(dirName,"cmdOptSwitchbord.py")
    with open(fileName,"w") as wf:
        wf.write(cmdOptSwitchbordFileStr)
    ## write command python files to commands dir from cmdTemplates
    cmdTemplates = {"newCmd": newCmdTemplate, 
                    "modCmd": modCmdTemplate, 
                    "rmCmd": rmCmdTemplate}

    for cmdName, cmdTemplate in cmdTemplates.items():
        indent = 0
        commandJsonDictStr = "commandJsonDict = {\n"
        indent += 4
        commandJsonDictStr += " "*indent + f'"{cmdName}": {json.dumps(commandsJsonDict.get(cmdName),indent=8)}'
        commandJsonDictStr += "\n}"
        fileName = os.path.join(dirName,f"{cmdName}.py")
        print(f'Using {cmdName} template to write {fileName}')
        cmdTemplatesStr = cmdTemplates[cmdName].substitute(commandJsonDict=commandJsonDictStr,packName=programName)
        with open(fileName,"w") as wf:
            wf.write(str(cmdTemplatesStr))
    # -- commands\templates dir files
    template_names = ['asyncDef', 'classCall', 'argCmdDef', 'simple']
    template_name_map = {
        "asyncDef": asyncDefTemplateStr,
        "classCall": classCallTemplateStr,
        "argCmdDef": argCmdDefTemplateStr,
        "simple": simpleTemplateStr,
    }
    ## write argCmdDef.py template file
    dirName = os.path.join(dirName, "templates")
    for template_name in template_names:
        fileName = os.path.join(dirName, f"{template_name}.py")
        chkDir(dirName)

        fileStr = "from string import Template\n"
        fileStr += "from textwrap import dedent\n\n"
        fileStr += f'cmdDefTemplate = Template(dedent("""{template_name_map.get(template_name)}\n"""))\n\n'
        if template_name == "argCmdDef":
            fileStr += f'argDefTemplate = Template(dedent("""{argDefTemplateStr}\n"""))'
        with open(fileName,"w") as wf:
            wf.write(fileStr)


