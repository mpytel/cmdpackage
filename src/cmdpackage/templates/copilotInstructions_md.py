#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

# Template source file mappings
templateSources = {
    "copilotInstructions_md": ".github/copilot-instructions.md",
}

copilotInstructions_md = Template(
    dedent(
        """# GitHub Copilot Instructions for ${packName}

## Project Overview

**${packName}** is a dynamic command-line framework for creating, modifying, and managing custom commands with interactive help and argument parsing. It's a Python package (version ${version}) that allows users to build extensible CLI applications through an interactive interface.

## Project Structure

```
${packName}/
├── src/${packName}/
│   ├── main.py                     # Entry point - calls cmdSwitchbord
│   ├── classes/
│   │   ├── argParse.py            # Argument parsing logic
│   │   └── optSwitches.py         # Option flag management and .${packName}rc file handling
│   ├── commands/
│   │   ├── commands.json          # Central command registry and metadata
│   │   ├── cmdSwitchbord.py       # Command dispatcher/router
│   │   ├── commands.py            # Command loading and management
│   │   ├── newCmd.py              # Create new commands
│   │   ├── modCmd.py              # Modify existing commands
│   │   ├── rmCmd.py               # Remove commands
│   │   ├── runTest.py             # Test runner
│   │   └── templates/             # Code generation templates
│   │       ├── argCmdDef.py       # Default template with argument handling
│   │       ├── simple.py          # Minimal template
│   │       ├── classCall.py       # OOP template
│   │       └── asyncDef.py        # Async template
│   ├── defs/
│   │   ├── logIt.py              # Logging and colored output utilities
│   │   └── validation.py         # Input validation functions
│   └── .${packName}rc                     # User configuration file (runtime-generated)
├── tests/
│   ├── test_newCmd_roundtrip.py  # Tests for command creation
│   ├── test_modCmd_roundtrip.py  # Tests for command modification
│   ├── test_rmCmd_roundtrip.py   # Tests for command removal
│   └── test_argCmdDef_roundtrip.py # Template-specific tests
├── env/${packName}/                       # Virtual environment
├── pyproject.toml               # Package configuration
└── README_Command_modifications.md # Detailed usage documentation
```

## Core Architecture

### Command Flow
1. **Entry Point**: `main.py` → `ArgParse` → `cmdSwitchbord`
2. **Command Dispatch**: `cmdSwitchbord.py` routes to appropriate command handlers
3. **Command Registry**: `commands.json` stores all command metadata
4. **Configuration**: `.${packName}rc` file stores user-specific flag defaults
5. **Code Generation**: Templates in `templates/` generate actual command `.py` files

### Key Components

#### ArgParse Class (`classes/argParse.py`)
- Parses command-line arguments
- Separates regular arguments from option flags
- Handles both `-flag` (boolean) and `--option` (string) syntax

#### Commands Management (`commands/commands.py`)
- Loads command definitions from `commands.json`
- Provides interface for command metadata access
- Maintains command registry

#### Option Switches (`classes/optSwitches.py`)
- Manages `.${packName}rc` configuration file
- Handles command-specific flag defaults
- Provides flag toggle functionality (`+flag`/`-flag` syntax)

## Core Commands

### `newCmd` - Command Creation
- **Purpose**: Creates new commands with arguments and option flags
- **Usage**: `${packName} newCmd <cmdName> [args...] [--stringOpts] [-boolFlags]`
- **Features**:
  - Interactive description prompts
  - Template selection (`--template` option)
  - Automatic `.py` file generation
  - JSON metadata registration
  - `.${packName}rc` flag defaults setup

### `modCmd` - Command Modification  
- **Purpose**: Modifies existing commands, adds arguments/flags
- **Usage**: `${packName} modCmd <cmdName> [args...] [--stringOpts] [-boolFlags]`
- **Features**:
  - Command description updates
  - Argument description updates
  - New argument addition
  - New flag/option addition
  - Maintains existing command structure

### `rmCmd` - Command Removal
- **Purpose**: Removes commands and cleans up files
- **Usage**: `${packName} rmCmd <cmdName> [argNames...]`
- **Features**:
  - Complete command removal
  - Selective argument removal
  - File cleanup (`.py` files)
  - JSON metadata cleanup

## Flag System

### Flag Types
- **Boolean Flags** (`-flag`): Single hyphen, stores true/false
- **String Options** (`--option`): Double hyphen, stores text values

### Flag Management
- **Creation**: Defined during `newCmd` or added via `modCmd`
- **Storage**: Defaults saved in `.${packName}rc` under `commandFlags.<cmdName>`
- **Toggle Syntax**: Use `+flag` to enable, `-flag` to disable at runtime

### Example `.${packName}rc` Structure
```json
{
  "switchFlags": {},
  "commandFlags": {
    "deploy": {
      "verbose": false,
      "config": "",
      "force": true
    }
  }
}
```

## Templates System

### Available Templates
1. **argCmdDef** (default): Full argument handling with validation
2. **simple**: Minimal template for basic commands  
3. **classCall**: Object-oriented approach using classes
4. **asyncDef**: Asynchronous operations template

### Template Usage
```bash
${packName} newCmd --template simple myCmd
${packName} newCmd --templates=classCall processor --input
```

## Testing Framework

### Test Structure
- **Round-trip tests**: Create → Modify → Verify → Cleanup
- **Test files**: `test_*_roundtrip.py` for each major command
- **Test categories**:
  - Command creation and modification
  - Flag and option handling
  - Error handling and validation
  - File system operations
  - JSON metadata integrity

### Running Tests
```bash
${packName} runTest                    # Run all tests
python tests/test_newCmd_roundtrip.py  # Run specific test
```

### Test Environment
- Uses virtual environment: `env/${packName}/`
- Activates environment automatically in test runners
- Cleans up test artifacts after each run

## Development Guidelines

### Code Organization
- **Single Responsibility**: Each command handler focuses on one operation
- **JSON-Driven**: Command metadata centralized in `commands.json`
- **Template-Based**: Code generation uses pluggable templates
- **Configuration-Managed**: User preferences in `.${packName}rc`

### Error Handling
- Use `logIt.py` utilities for consistent colored output
- Validate inputs using `validation.py` functions
- Handle file operations gracefully
- Provide clear user feedback for errors

### File Management
- **Commands**: Store in `src/${packName}/commands/`
- **Metadata**: Update `commands.json` atomically
- **Configuration**: Manage `.${packName}rc` through `optSwitches.py`
- **Cleanup**: Always clean up generated files in error cases

### Adding New Commands
1. Create command handler in `commands/`
2. Add entry to `commands.json`
3. Update command dispatcher in `cmdSwitchbord.py`
4. Create corresponding test file
5. Document in README files

## Common Patterns

### Command Handler Structure
```python
def myCommand(argParse: ArgParse):
    args = argParse.args
    cmdObj = Commands()
    
    # Validate inputs
    if len(args.arguments) == 0:
        printIt("Command name required", lable.ERROR)
        return
    
    # Process command logic
    # Update JSON metadata
    # Handle file operations
    # Provide user feedback
```

### JSON Metadata Pattern
```python
# Load current commands
cmdObj = Commands()
commands = copy.deepcopy(cmdObj.commands)

# Modify metadata
commands[cmdName] = {
    "description": "...",
    "switchFlags": {...},
    "argName": "..."
}

# Save back
cmdObj.commands = commands
```

### Test Pattern
```python
def test_feature_name(result: TestResult) -> bool:
    print_test("Test description")
    
    # Setup
    # Execute command
    # Verify results
    # Cleanup
    
    if success:
        result.add_result("test_name", True)
        return True
    else:
        result.add_result("test_name", False, "error_message")
        return False
```

## Key Considerations

### File System
- All paths should be absolute when possible
- Handle virtual environment activation in tests
- Clean up generated files in error cases
- Respect existing file structure

### JSON Handling
- Always use `copy.deepcopy()` when modifying command metadata
- Maintain JSON structure consistency
- Handle missing keys gracefully
- Validate JSON integrity after modifications

### User Experience
- Provide interactive prompts for descriptions
- Use colored output for better readability
- Give clear error messages with suggestions
- Show progress and confirmation messages

### Virtual Environment
- Tests must activate the `env/${packName}` environment
- Use `source env/${packName}/bin/activate` in shell commands
- Ensure package is installed in development mode (`pip install -e .`)

This framework emphasizes dynamic command creation, user-friendly interaction, and robust testing to ensure reliable CLI tool development.
"""
    )
)
