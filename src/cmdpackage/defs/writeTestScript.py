import os
from cmdpackage.defs.utilities import chkDir
from cmdpackage.templates.test_newCmd_roundtrip import test_newCmd_roundtrip_template
from cmdpackage.templates.test_modCmd_roundtrip import test_modCmd_roundtrip_template
from cmdpackage.templates.test_rmCmd_roundtrip import test_rmCmd_roundtrip_template

def writeTestScript(fields: dict) -> None:
    """Write a basic test script for the package."""
    field_name = "name"
    programName = fields[field_name]
    # -- package dir files
    ## write __init__.py to package dir from str
    testDir = os.path.join(os.path.abspath("."), "tests")
    chkDir(testDir)
    
    # build test script
    # write test_newCmd_roundtrip.py
    fileName = os.path.join(testDir,"test_newCmd_roundtrip.py")
    outStr = test_newCmd_roundtrip_template.substitute(packName=programName)
    with open(fileName,"w") as wf:
        wf.write(outStr)
    # chgmod to make executable
    st = os.stat(fileName)
    os.chmod(fileName, st.st_mode | 0o111)  # add execute permissions

    # write test_modCmd_roundtrip.py
    fileName = os.path.join(testDir, "test_modCmd_roundtrip.py")
    outStr = test_modCmd_roundtrip_template.substitute(packName=programName)
    with open(fileName, "w") as wf:
        wf.write(outStr)
    # chgmod to make executable
    st = os.stat(fileName)
    os.chmod(fileName, st.st_mode | 0o111)  # add execute permissions

    # write test_rmCmd_roundtrip.py
    fileName = os.path.join(testDir, "test_rmCmd_roundtrip.py")
    outStr = test_rmCmd_roundtrip_template.substitute(packName=programName)
    with open(fileName, "w") as wf:
        wf.write(outStr)
    # chgmod to make executable
    st = os.stat(fileName)
    os.chmod(fileName, st.st_mode | 0o111)  # add execute permissions
