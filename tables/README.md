# .Lab Library Tables Setup Guide

This guide explains how to add the library tables to your KiCad configuration. You can choose between automated or manual setup.

## Automated Setup (Experimental)

We provide a script that can automatically update your KiCad configuration:

```bash
# Install the library validator if you haven't already
pip install git+https://github.com/Aharoni-Lab/kicad-library-validator.git

# Run the update script
python -m kicad_lib_validator.utils.update_kicad_tables structure.yaml

# For a dry run (shows what would be changed without making changes)
python -m kicad_lib_validator.utils.update_kicad_tables structure.yaml --dry-run
```

Note: The automated script is experimental. If you encounter any issues, please use the manual setup method below.

## Manual Setup

### 1. Set Up Environment Variable

First, you need to set up the `LAB_DIR` environment variable to point to your library root directory:

### Windows
```batch
setx LAB_DIR "/home/runner/work/kicad-lab-library/kicad-lab-library"
```

### Linux/macOS
```bash
echo 'export LAB_DIR="/home/runner/work/kicad-lab-library/kicad-lab-library"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Locate KiCad's Library Tables

KiCad stores its library tables in different locations depending on your operating system:

### Windows
1. Open File Explorer
2. Navigate to `%APPDATA%\kicad\9.0\`
   - You can paste this path directly in the address bar
   - Or press `Win + R`, type `%APPDATA%\kicad\9.0\`, and press Enter
3. You should find two files:
   - `sym-lib-table` (for symbol libraries)
   - `fp-lib-table` (for footprint libraries)

### Linux/macOS
1. Open Terminal
2. Navigate to `~/.config/kicad/9.0/`
3. You should find two files:
   - `sym-lib-table` (for symbol libraries)
   - `fp-lib-table` (for footprint libraries)

### 3. Add Symbol Libraries

1. Open the `sym-lib-table` file in a text editor
2. Find the last closing parenthesis `)` in the file
3. Copy all entries from our `sym-lib-table` file:
   ```
   tables/sym-lib-table
   ```
4. Paste the entries just before the final closing parenthesis
5. Make sure to maintain proper indentation
6. Save the file

### 4. Add Footprint Libraries

1. Open the `fp-lib-table` file in a text editor
2. Find the last closing parenthesis `)` in the file
3. Copy all entries from our `fp-lib-table` file:
   ```
   tables/fp-lib-table
   ```
4. Paste the entries just before the final closing parenthesis
5. Make sure to maintain proper indentation
6. Save the file

### 5. Verify Setup

After adding the libraries:

1. Save all table files
2. Restart KiCad to ensure the environment variable is recognized
3. Open a schematic and verify that the symbol libraries are available:
   - Click on 'Place Symbol'
   - Check the library browser for our libraries
4. Open a PCB layout and verify that the footprint libraries are available:
   - Click on 'Add Footprint'
   - Check the footprint browser for our libraries

## Troubleshooting

If the libraries are not found:

1. Verify that the environment variable is set correctly:
   - Windows: Open Command Prompt and type `echo %LAB_DIR%`
   - Linux/macOS: Open Terminal and type `echo $LAB_DIR`
2. Check that the paths in the library tables are correct
3. Ensure you have the necessary permissions to access the library files
4. If using KiCad 8.0 or earlier, adjust the paths accordingly:
   - Replace `9.0` with your KiCad version in the paths above

## Note

The library tables in this directory are specific to this library and should be kept in version control. 
They contain only the entries for this library's symbols and footprints.