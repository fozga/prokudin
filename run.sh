#!/bin/bash

# run.sh - Launches the PyQt application in Docker with X11 forwarding
# Usage: ./run.sh [input_directory]
# Example: ./run.sh /path/to/my/images

# Helper function to create directory with correct ownership
create_directory_as_user() {
    local dir_path="$1"
    if [[ -n "$SUDO_USER" ]]; then
        sudo -u "$SUDO_USER" mkdir -p "$dir_path"
    else
        mkdir -p "$dir_path"
    fi
}

# Function to validate directory existence and permissions
validate_directory() {
    local dir="$1" type="$2"
    [[ -d "$dir" ]] || { echo "ERROR: $type directory does not exist: $dir"; exit 1; }
    [[ -r "$dir" ]] || { echo "ERROR: $type directory is not readable: $dir"; exit 1; }
}

# Set default directories
DEFAULT_INPUT_DIR="$(pwd)/input"
if [[ -n "$SUDO_USER" ]]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME="$HOME"
fi
OUTPUT_DIR="$USER_HOME/prokudin/output"

# Get the script's directory (project root) early
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$SCRIPT_DIR" ]]; then
    echo "ERROR: Failed to determine script directory."
    exit 1
fi

# Validate and set input directory
if [[ -n "$1" ]]; then
    # User provided an input directory argument
    TEMP_INPUT_DIR="$1"
    
    # Convert to absolute path if relative path is provided
    if [[ ! "$TEMP_INPUT_DIR" = /* ]]; then
        TEMP_INPUT_DIR="$(pwd)/${TEMP_INPUT_DIR}"
    fi
    
    # Check if the provided path exists (do not create it)
    if [[ -d "$TEMP_INPUT_DIR" ]]; then
        # Path exists, use it
        INPUT_DIR="$TEMP_INPUT_DIR"
        echo "Using provided input directory: $INPUT_DIR"
    else
        # Path doesn't exist, fall back to default behavior (no argument provided)
        echo "WARNING: Directory '$TEMP_INPUT_DIR' does not exist, using default input directory"
        INPUT_DIR="$DEFAULT_INPUT_DIR"
    fi
else
    # No argument provided, use default
    INPUT_DIR="$DEFAULT_INPUT_DIR"
fi

# Ensure input, output, and presets directories exist with correct ownership
if [[ ! -d "$INPUT_DIR" ]]; then
    echo "Creating input directory: $INPUT_DIR"
    create_directory_as_user "$INPUT_DIR"
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "Creating output directory: $OUTPUT_DIR"
    create_directory_as_user "$OUTPUT_DIR"
fi

PRESETS_DIR="$SCRIPT_DIR/presets"
if [[ ! -d "$PRESETS_DIR" ]]; then
    echo "Creating presets directory: $PRESETS_DIR"
    create_directory_as_user "$PRESETS_DIR"
fi

CONFIG_DIR="$SCRIPT_DIR/config"
if [[ ! -d "$CONFIG_DIR" ]]; then
    echo "Creating config directory: $CONFIG_DIR"
    create_directory_as_user "$CONFIG_DIR"
fi

# Final validation that directories are accessible
validate_directory "$INPUT_DIR" "Input"
validate_directory "$OUTPUT_DIR" "Output"
validate_directory "$PRESETS_DIR" "Presets"
validate_directory "$CONFIG_DIR" "Config"

echo "Using input directory: $INPUT_DIR"
echo "Using output directory: $OUTPUT_DIR"
echo "Using presets directory: $PRESETS_DIR"
echo "Using config directory: $CONFIG_DIR"

# Enable X server access for Docker
xhost +local:docker &>/dev/null || {
    echo "ERROR: Failed to configure X11 permissions"
    exit 1
}

# Run container with GUI support and mounted input/output/presets/config folders
# All folders are mounted as read-write for data I/O
# Source code is mounted as read-only
docker run -it --rm \
    -e XDG_RUNTIME_DIR=/tmp/runtime-root \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "$INPUT_DIR:/app/input:ro" \
    -v "$OUTPUT_DIR:/app/output" \
    -v "$PRESETS_DIR:/app/presets" \
    -v "$CONFIG_DIR:/app/config" \
    -v "$SCRIPT_DIR/src:/opt/app/src:ro" \
    pyqt-app python3 -m src.main

# Reset X server access (optional security measure)
xhost -local:docker &>/dev/null