#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

main_template = Template(dedent("""import sys, os
from .classes.argParse import ArgParse
from .commands.cmdSwitchbord import cmdSwitcbord


def main():
    # packName = os.path.basename(sys.argv[0])
    argParse = ArgParse()
    cmdSwitcbord(argParse)


if __name__ == "__main__":
    main()
"""))

