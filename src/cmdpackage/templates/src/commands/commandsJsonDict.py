commandsJsonDict = {
    "switchFlags": {},
    "description": "Dictionary of commands, their discription and switches, and their argument discriptions.",
    "_globalSwitcheFlags": {},
    "newCmd": {
        "description": "Add new command <cmdName> with [argNames...]. Also creates a file cmdName.py.",
        "switchFlags": {},
        "cmdName": "Name of new command",
        "argName": "(argName...), Optional names of argument to associate with the new command.",
    },
    "modCmd": {
        "description": "Modify a command or argument descriptions, or add another argument for command. The cmdName.py file will not be modified.",
        "switchFlags": {},
        "cmdName": "Name of command being modified",
        "argName": "(argName...) Optional names of argument(s) to modify.",
    },
    "rmCmd": {
        "description": "Remove <cmdName> and delete file cmdName.py, or remove an argument for a command.",
        "switchFlags": {},
        "cmdName": "Name of command to remove, cmdName.py and other commands listed as argument(s) will be delated.",
        "argName": "Optional names of argument to remove.",
    },
    "runTest": {
        "description": "Run test(s) in ./tests directory. Use 'listTests' to see available tests.",
        "switchFlags": {
            "verbose": {"description": "Verbose output flag", "type": "bool"},
            "stop": {"description": "Stop on failure flag", "type": "bool"},
            "summary": {"description": "Summary only flag", "type": "bool"},
        },
        "testName": "Optional name of specific test to run (without .py extension)",
        "listTests": "List all available tests in the tests directory",
    },
    "fileDiff": {
        "description": "Show the differnces between two files.",
        "origFile": "Original file name",
        "newFile": "New file name",
    },
    "sync": {
        "description": "Sync modified files to originating template file",
        "switchFlags": {
            "dry-run": {
                "description": "Show what would be synced without making changes",
                "type": "bool",
            },
            "force": {
                "description": "Force sync even if files appear to have user modifications",
                "type": "bool",
            },
            "backup": {
                "description": "Create backup files before syncing",
                "type": "bool",
            },
        },
        "filePattern": "Optional file patterns to sync (e.g., '*.py', 'commands/*')",
        "action": "Action to perform: 'sync' (default), 'list', 'status', 'make', 'rmTemp'",
    },
}