#!/bin/bash

# Set the virtual environment directory name
VENV_DIR="venv"

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "Python3 is not installed. Please install it first."
    exit 1
fi

# Check if venv directory already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists in ./$VENV_DIR"
else
    echo "Creating virtual environment in ./$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created successfully."
fi

# Activate the virtual environment
if [[ "$SHELL" == *"zsh"* ]]; then
    source "$VENV_DIR/bin/activate"
elif [[ "$SHELL" == *"bash"* ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Shell not recognized. Please activate the venv manually: source $VENV_DIR/bin/activate"
fi

echo "Virtual environment activated. You can now install dependencies using pip."

