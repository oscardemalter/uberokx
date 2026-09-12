#!/usr/bin/env python
"""
Split UberOKX.txt into separate files based on section headers.
Splits large monolithic text file into organized project structure.
"""

import re
import pathlib
import sys


def split_uberox_file(input_file: str = "UberOKX.txt") -> None:
    """
    Split a monolithic UberOKX.txt file into separate files.
    
    Expected format:
    ===== 00_filename.py =====
    file content here
    ===== 01_another_file.py =====
    more content
    
    Args:
        input_file: Path to the input file to split
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        SystemExit: If file format is invalid
    """
    root = pathlib.Path(".")
    input_path = pathlib.Path(input_file)

    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read and parse file
    try:
        txt = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        print(f"ERROR: Could not read file with UTF-8 encoding: {e}")
        raise SystemExit(1)

    # Split on section headers: ===== filename.ext =====
    try:
        parts = re.split(r"(?m)^===== +(.+?) +===== *$", txt)
    except re.error as e:
        print(f"ERROR: Invalid regex pattern: {e}")
        raise SystemExit(1)

    if len(parts) < 3:
        print("ERROR: No sections found in file. Expected format: ===== filename =====")
        raise SystemExit(1)

    # Process each section
    i = 1
    n = 0
    
    while i + 1 < len(parts):
        header = parts[i].strip()
        body = parts[i + 1]
        i += 2

        # Skip sections starting with "00_" (metadata)
        if header.startswith("00_"):
            print(f"skipped: {header} (metadata)")
            continue

        # Remove numeric prefix (e.g., "01_" -> "")
        name = re.sub(r"^\d+_", "", header)

        # Reject old format (u1.txt, u2.txt, etc.)
        if re.match(r"u\d+\.txt$", name):
            print(
                "ERROR: Old format detected (u1..u7). "
                "Ask for complete blocks using latest format."
            )
            raise SystemExit(1)

        # Create file
        path = root / name
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Strip trailing newlines but ensure file ends with newline
            content = body.strip("\n") + "\n"
            path.write_text(content, encoding="utf-8")
            n += 1
            print(f"✓ wrote: {name}")
        except IOError as e:
            print(f"ERROR: Could not write file {path}: {e}")
            raise SystemExit(1)

    print(f"\nDONE: {n} fichiers créés/mis à jour")
    
    if n == 0:
        print("WARNING: No files were created. Check your input file format.")


if __name__ == "__main__":
    # Allow custom input file via command line
    input_file = sys.argv[1] if len(sys.argv) > 1 else "UberOKX.txt"
    
    try:
        split_uberox_file(input_file)
    except Exception as e:
        print(f"FATAL: {e}")
        sys.exit(1)
