import os
from cmdpackage.defs.utilities import chkDir
from cmdpackage.templates.test_newCmd_roundtrip import test_newCmd_roundtrip_template

def writeTestScript(fields: dict) -> None:
    """Write a basic test script for the package."""
    print()
    field_name = "name"
    programName = fields[field_name]
    # -- package dir files
    ## write __init__.py to package dir from str
    testDir = os.path.join(os.path.abspath("."), "tests")
    chkDir(testDir)
    fileName = os.path.join(testDir,"test_newCmd_roundtrip.py")
    outStr = test_newCmd_roundtrip_template.substitute(packName=programName)
    with open(fileName,"w") as wf:
        wf.write(outStr)