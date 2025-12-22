#!/bin/bash

# Run the Python script with a timeout
timeout 10 python3 "$1"

# Check exit code
if [ $? -eq 0 ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi