#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

resetPi_template = Template(dedent("""import os, sys
from ${packName}.defs.logIt import printIt, lable, deleteLog
from pathlib import Path
from ${packName}.defs.piFileIO import getKeyItem
from ${packName}.defs.piTouch import isPiID
from shutil import rmtree, copyfile


def resetPi(argParse):
    print("*** ${packName} system is being reset ***")
    keepUser = ""
    if not argParse:
        # called outside of termanal so keep root user if path in .${packName}rc
        keepUser = getKeyItem("rootUser")
        if keepUser:
            keepUser = Path(keepUser).stem
            printIt(f"Preserving root ({keepUser})", lable.INFO)
    else:
        args = argParse.parser.parse_args()
        theArgs = args.arguments
        if len(theArgs) > 0:
            # any agument will force root to be perserved.
            keepUser = getKeyItem("rootUser")
    # delete user dirs
    piPathStr = getKeyItem("pisDir")
    if piPathStr:
        piPath: Path = Path(piPathStr)
        if piPath.is_dir():
            for aPath in piPath.iterdir():
                if keepUser:
                    if keepUser != aPath.stem:
                        # KEY POINT: If the stem from .${packName}rc is not found
                        if aPath.is_dir() and isPiID(aPath.name):
                            print("pisDir rm", str(aPath))
                            rmtree(aPath)
                else:
                    if aPath.is_dir() and isPiID(aPath.name):
                        print("pisDir rm", str(aPath))
                        rmtree(aPath)
        backupPiWave(piPath)
    piPathStr = getKeyItem("piScratchDir")
    if piPathStr:
        piPath: Path = Path(piPathStr)
        if piPath.is_dir():
            print("piScratchDir rm", piPathStr)
            rmtree(piPath)
    piPathStr = getKeyItem("piClassDir")
    if piPathStr:
        piPath: Path = Path(piPathStr)
        if piPath.is_dir():
            print("piClassDir rm", piPathStr)
            rmtree(piPath)
    deleteLog()
    if sys.stdin.isatty():
        printIt("${packName} system files deleted", lable.IMPORT)
    packName = os.path.basename(sys.argv[0])
    # build system
    exec("from ${packName}.classes.piPiPackage import PiPiPackage")
    exec(f'PiPiPackage("{packName}")')


def backupPiWave(piPath: Path):
    piWaveFileIndex = 0
    piWavePath = piPath.joinpath("piWave")
    piWaveFile = piWavePath.joinpath(f"piWave{str(piWaveFileIndex).zfill(3)}.${packName}")
    if piWaveFile.is_file():
        piWaveFileIndex += 1
        piWaveHoldFile = piWavePath.joinpath(f"piWave{str(piWaveFileIndex).zfill(3)}.${packName}")
        while piWaveHoldFile.is_file():
            piWaveFileIndex += 1
            piWaveHoldFile = piWavePath.joinpath(f"piWave{str(piWaveFileIndex).zfill(3)}.${packName}")
        shiftPiWaveFileNames(piWavePath, piWaveFileIndex)


def shiftPiWaveFileNames(piWavePath: Path, piWaveFileIndex: int):
    for fileIndex in range(piWaveFileIndex, 0, -1):
        fromName = piWavePath.joinpath(f"piWave{str(fileIndex-1).zfill(3)}.${packName}")
        toName = piWavePath.joinpath(f"piWave{str(fileIndex).zfill(3)}.${packName}")
        os.rename(fromName, toName)
"""))

