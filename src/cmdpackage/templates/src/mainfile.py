#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

mainFile = dedent(
    """import sys, os
from .classes.argParse import ArgParse
from .commands.cmdSwitchbord import cmdSwitchbord

def main():
        #packName = os.path.basename(sys.argv[0])
        argParse = ArgParse()
        cmdSwitchbord(argParse)

if __name__ == '__main__':
    main()
"""
)