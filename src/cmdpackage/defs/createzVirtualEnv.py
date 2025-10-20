#!/usr/bin/python
# -*- coding: utf-8 -*-
from cmdpackage.defs.runSubProc import runSubProc

def createzVirtualEnv(fields: dict):
    try:
        yellow = "\033[33m"
        reset = "\033[0m"
        name = "name"
        rtnCompProc = runSubProc(f'virtualenv env/{fields[name]}')
        print(
            f'* Source the virtual environment with:  {yellow}. env/{fields[name]}/bin/activate{reset}')
        print(
            f'* Install "{fields[name]}" with:  {yellow}pip install -e .{reset}')
        print(f'* Verify install with:  {yellow}pip list{reset}')
        print(
            f'* Restore original shell environment with: {yellow}deactivate{reset}\n')
        print(
            f'* Create and test first new command:\n' + \
            f'  {yellow}{fields[name]} newCmd firstCMD firstARG{reset}\n' + \
            f'  {yellow}{fields[name]} -h{reset}\n' + \
            f'  {yellow}{fields[name]} firstCMD firstARG{reset}\n' + \
            f'  {yellow}{fields[name]} rmCmd firstCMD{reset}\n')
    except:
        print(rtnCompProc)
        pass



