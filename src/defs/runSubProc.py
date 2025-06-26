from subprocess import run, DEVNULL, CompletedProcess

def runSubProc(theCmd: str, noOutput=True) -> CompletedProcess:
    if noOutput:
        rtnCompProc = run(theCmd, shell=True,
                                stdout=DEVNULL,
                                stderr=DEVNULL)
    else:
        rtnCompProc = run(theCmd, shell=True)
    return rtnCompProc