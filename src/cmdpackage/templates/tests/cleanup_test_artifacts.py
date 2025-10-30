#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

# Template source file mappings
templateSources = {
    "cleanup_test_artifacts_template": "tests/cleanup_test_artifacts.py",
}

cleanup_test_artifacts_template = Template(
    dedent(
        """#!/usr/bin/env python3
\"\"\"
Utility script to clean up test artifacts that might be left behind during testing.

This script removes:
1. Test command .py files from src/vc/commands/
2. Test command entries from commands.json
3. Any other test-related artifacts

Usage: python cleanup_test_artifacts.py
\"\"\"

import os
import json
import sys
from pathlib import Path


def cleanup_test_artifacts():
    \"\"\"Clean up all test artifacts\"\"\"
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("🧹 Cleaning up test artifacts...")
    
    # Clean up .py files - look for any file starting with "test"
    commands_dir = project_root / "src" / "vc" / "commands"
    
    cleaned_files = 0
    if commands_dir.exists():
        for file_path in commands_dir.glob("test*.py"):
            try:
                file_path.unlink()
                print(f"  ✓ Removed file: {file_path.name}")
                cleaned_files += 1
            except Exception as e:
                print(f"  ✗ Could not remove {file_path.name}: {e}")

    # Clean up commands.json entries - look for any key starting with "test"
    commands_file = commands_dir / "commands.json"
    if commands_file.exists():
        try:
            with open(commands_file, "r") as f:
                data = json.load(f)
            
            # Find all test commands (keys starting with "test")
            test_commands = [key for key in data.keys() if key.startswith("test")]
            
            cleaned_entries = 0
            for cmd in test_commands:
                if cmd in data:
                    del data[cmd]
                    cleaned_entries += 1
                    print(f"  ✓ Removed JSON entry: {cmd}")
            
            if cleaned_entries > 0:
                # Write back the cleaned data
                with open(commands_file, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"  ✓ Updated commands.json (removed {cleaned_entries} entries)")
            else:
                print("  ✓ commands.json is already clean")
                    
        except Exception as e:
            print(f"  ✗ Could not clean commands.json: {e}")
    
    # Summary
    total_cleaned = cleaned_files
    if total_cleaned > 0:
        print(f"\\n🎉 Cleanup complete! Removed {total_cleaned} test artifacts.")
    else:
        print("\\n✨ No test artifacts found - workspace is clean!")


if __name__ == "__main__":
    cleanup_test_artifacts()"""
    )
)
