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
├── pyproject.toml                # Package configuration
└── .gitignore
```

## Core Concepts

### Command Types and Templates
${packName} supports multiple command templates for different use cases:

1. **argCmdDef** (Default template) - Full-featured command with argument handling
2. **simple** - Minimal template for basic commands  
3. **classCall** - Object-oriented template for structured commands
4. **asyncDef** - Async template for concurrent operations

### Command Management Flow
1. **Creation**: `newCmd` creates commands from templates
2. **Modification**: `modCmd` updates existing commands
3. **Removal**: `rmCmd` cleans up commands and their dependencies
4. **Testing**: `runTest` validates functionality with various scenarios

### Configuration System
- **commands.json**: Central registry storing all command definitions and metadata
- **.${packName}rc**: User preferences file (generated at runtime)
- **Template variables**: Dynamic substitution using `$${variable}` syntax

## Key Features

### Dynamic Command Generation
Commands are generated from templates with variable substitution:
- Package name: `$${packName}`
- Version: `$${version}` 
- Custom variables as needed

### Interactive Help System
- Colored terminal output using ANSI codes
- Context-sensitive help for each command
- Argument validation and error reporting

### Extensible Architecture
- Template-based command creation
- Plugin-style command loading
- Modular structure supporting easy extensions

## Development Guidelines

### Code Style
- Use f-strings for string formatting where possible
- Follow PEP 8 naming conventions
- Add docstrings to all classes and functions
- Use type hints for function parameters and return values

### Error Handling
- Implement graceful error handling with informative messages
- Use colored output for errors and warnings
- Validate user inputs thoroughly

### Testing
- Write comprehensive tests for each command type
- Test round-trip scenarios (create → modify → remove)
- Validate template generation and substitution
- Test error conditions and edge cases

### Template Development
- Templates should be self-contained and reusable
- Use clear variable naming with `$${variable}` syntax
- Include comprehensive help text and examples
- Test templates with various parameter combinations

## Common Tasks

### Adding New Commands
1. Define template in `templates/` directory
2. Add command logic in `commands/`
3. Update `commands.json` registry
4. Create corresponding tests
5. Update documentation

### Modifying Templates
1. Update template files in `templates/`
2. Test template generation
3. Verify variable substitution
4. Update related tests
5. Document changes

### Debugging Issues
1. Check `commands.json` for command definitions
2. Verify template syntax and variables
3. Review log output for errors
4. Test with various input scenarios
5. Check file permissions and paths

## Architecture Notes

### Command Processing Pipeline
1. **argParse.py** - Parses command-line arguments
2. **cmdSwitchbord.py** - Routes to appropriate command handler
3. **commands.py** - Loads and manages command definitions
4. **Individual command files** - Execute specific functionality

### Template System
- Templates use Python's `string.Template` class
- Variable substitution with `$${variable}` syntax
- Support for conditional logic and loops
- Extensible template inheritance

### Configuration Management
- Runtime configuration in `.${packName}rc`
- Command metadata in `commands.json`
- Template-specific settings per command type

This framework is designed to be highly extensible and maintainable. When working with ${packName}, focus on:
- Clean separation of concerns
- Comprehensive error handling
- Thorough testing coverage
- Clear documentation and examples
- Consistent coding patterns across all modules
"""
    )
)