import os, time
from inspect import currentframe, getframeinfo


# Class of different termianl styles
class color:

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    # message: color
    l2cDict: dict = {
        "BK": RESET,
        "ERROR: ": RED,
        "PASS: ": GREEN,
        "WARN: ": YELLOW,
        "SAVED: ": BLUE,
        "DEBUG: ": MAGENTA,
        "REPLACED: ": CYAN,
        "INFO: ": WHITE,
        "STEP: ": MAGENTA,
        "IMPORT: ": UNDERLINE,
        "RESET": RESET,
        "File Not Found: ": YELLOW,
        "Directory Not Found: ": YELLOW,
        "FAIL: ": RED,
        "Useage: ": WHITE,
        "DELETE: ": YELLOW,
        "EXISTS: ": GREEN,
        "READ: ": GREEN,
        "TOUCHED: ": GREEN,
        "MKDIR: ": GREEN,
        "NEW CMD ADDED: ": GREEN,
        "CMD MODIFIED: ": GREEN,
        "CMD REMOVED: ": GREEN,
        "ARG REMOVED: ": GREEN,
        "IndexError: ": RED,
        "Testing: ": CYAN,
        "Update: ": CYAN,
        "TODO: ": CYAN,
        "ABORTPRT": YELLOW,
        "Unknown PiSeedType: ": RED,
        "Incorect PiValue Path: ": RED,
    }


class lable:
    SAVED = "SAVED: "
    REPLACED = "REPLACED: "
    BLANK = "BK"
    ERROR = "ERROR: "
    PASS = "PASS: "
    WARN = "WARN: "
    DEBUG = "DEBUG: "
    INFO = "INFO: "
    STEP = "STEP: "
    IMPORT = "IMPORT: "
    RESET = "RESET"
    FileNotFound = "File Not Found: "
    DirNotFound = "Directory Not Found: "
    FAIL = "FAIL: "
    Useage = "Useage: "
    MKDIR = "MKDIR: "
    DELETE = "DELETE: "
    EXISTS = "EXISTS: "
    READ = "READ: "
    TOUCHED = "TOUCHED: "
    NewCmd = "NEW CMD ADDED: "
    ModCmd = "CMD MODIFIED: "
    RmCmd = "CMD REMOVED: "
    RmArg = "ARG REMOVED: "
    IndexError = "IndexError: "
    TESTING = "Testing: "
    UPDATE = "Update: "
    TODO = "TODO: "
    ABORTPRT = "ABORTPRT"
    UnknownPiSeedType = "Unknown PiSeedType: "
    IncorectPiValuePath = "Incorect PiValue Path: "


# log function
def logIt(*message, logFileName="tc.log"):
    # write log
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    prtStr = ""
    needClip = False
    if len(message) > 0:
        for mess in message:
            if mess == lable.BLANK:
                pass
            elif mess in color.l2cDict:
                prtStr = mess + prtStr
            else:
                needClip = True
                prtStr += str(mess) + " "
        if needClip:
            prtStr = prtStr[:-1]

    prtStr = "[" + now + "] " + prtStr + "\n"

    with open(logFileName, "a") as f:
        f.write(prtStr)


def printIt(*message, asStr: bool = False) -> str:
    prtStr = ""
    rtnStr = ""
    needClip = False
    abortPrt = False
    for mess in message:
        if mess == lable.ABORTPRT:
            abortPrt = True
    if not abortPrt:
        if len(message) > 0:
            for mess in message:
                if mess == lable.BLANK:
                    prtStr = message[0]
                    rtnStr = message[0]
                    needClip = False
                elif mess in color.l2cDict:
                    prtStr = color.l2cDict[mess] + mess + color.RESET + prtStr
                    rtnStr = mess + rtnStr
                else:
                    needClip = True
                    prtStr += str(mess) + " "
                    rtnStr += str(mess) + " "
            if needClip:
                prtStr = prtStr[:-1]
                rtnStr = rtnStr[:-1]
        if not asStr:
            print(prtStr)
    return rtnStr


def cStr(inStr: str, cVal: str):
    return cVal + inStr + color.RESET


def deleteLog(logFileName="tc.log"):
    if os.path.isfile(logFileName):
        os.remove(logFileName)


def getCodeFile():
    cf = currentframe()
    codeObj = ""
    if cf:
        if cf.f_back:
            codeObj = cf.f_back.f_code
    if codeObj:
        codeObjStr = str(codeObj).split(",")[1].split('"')[1]
        codeObjStr = os.path.basename(codeObjStr)
    else:
        codeObjStr = "file-no-found"
    return codeObjStr


def getCodeLine():
    cf = currentframe()
    codeObj = None
    if cf:
        if cf.f_back:
            codeObj = cf.f_back.f_code
    return codeObj


def germDbug(loc: str, currPi, nextPi):
    loc += currPi.piSeedKeyType
    if nextPi == None:
        print(loc, currPi.piSeedKeyDepth, nextPi)
        print("piType:", currPi.piType, nextPi)
        print("piTitle:", currPi.piTitle, nextPi)
        print("piSD:", currPi.piSD, nextPi)
    else:
        print(loc, currPi.piSeedKeyDepth, nextPi.piSeedKeyDepth)
        print("piType:", currPi.piType, nextPi.piType)
        print("piTitle:", currPi.piTitle, nextPi.piTitle)
        print("piSD:", currPi.piSD, nextPi.piSD)
    print("--------------------")
