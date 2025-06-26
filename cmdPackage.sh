#!/bin/bash

# --- Resolve the script's own full path and directory ---
# This line is crucial. It finds the absolute path of THIS script,
# regardless of how it was called (relative, absolute, or via PATH).
SCRIPT_FULL_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_FULL_PATH")"

# Print for debugging/verification
echo "DEBUG: The script's full path is: $SCRIPT_FULL_PATH"
echo "DEBUG: The script's directory is: $SCRIPT_DIR"
echo "DEBUG: The current working directory (where you called the script from) is: $(pwd)"

# --- Start of your original script logic ---
PROGRAM_NAME="$1"

if [ -z "$PROGRAM_NAME" ]; then
    echo "Usage: $0 <program_name>"
    exit 1
fi

# Define the base directory for cmdPacks within the current working directory
# Note: This still places your project in the directory you *called the script from*.
# If you want it always in a fixed location (e.g., ~/cmdPacks), then use $HOME/cmdPacks
CURRENT_WORKING_DIR="$(pwd)"
TARGET_PROGRAM_DIR="$CURRENT_WORKING_DIR/$PROGRAM_NAME"

# --- Check if the specific program directory already exists ---
if [ -d "$TARGET_PROGRAM_DIR" ]; then
    echo "Error: Program directory '$TARGET_PROGRAM_DIR' already exists. Exiting."
    exit 1
else
    echo "Program directory '$TARGET_PROGRAM_DIR' does not exist. Creating it now..."
    mkdir "$TARGET_PROGRAM_DIR" || { echo "Error: Failed to create program directory '$TARGET_PROGRAM_DIR'."; exit 1; }
    echo "Program directory '$TARGET_PROGRAM_DIR' created successfully."
fi

# --- Proceed with package generation ---
cd "$TARGET_PROGRAM_DIR" || { echo "Error: Could not change directory to $TARGET_PROGRAM_DIR"; exit 1; }

virtualenv "env/$PROGRAM_NAME"
source "env/$PROGRAM_NAME/bin/activate"

# Install cmdpackage using its true resolved path
#pip install -i https://test.pypi.org/simple/ cmdpackage
pip install --disable-pip-version-check $SCRIPT_DIR
# Do not change the code bellow blank lines are importent
# for heredoc cli script input.
cmdpackage<<inPi











inPi
pip uninstall cmdpackage<<inY
Y
inY
pip install --disable-pip-version-check -e .
"$PROGRAM_NAME" newCmd helloWorld greeting<<inNewCmd
Echo the greeting text.
The test text to echo.
inNewCmd
"$PROGRAM_NAME" helloWorld "Your ready to add and remove commands, and modify code in your myPack project $PROGRAM_NAME."