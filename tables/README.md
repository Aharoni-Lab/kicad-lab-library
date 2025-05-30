# .Lab Library Tables Setup Guide

This guide explains how to manually add the library tables to your KiCad configuration.

## 1. Set Up Environment Variable

First, you need to set up the `.LAB_DIR` environment variable to point to your library root directory:

### Windows
```batch
setx .LAB_DIR "C:\Users\dbaha\Documents\Projects\kicad-lab-library"
```

### Linux/macOS
```bash
echo 'export .LAB_DIR="C:\Users\dbaha\Documents\Projects\kicad-lab-library"' >> ~/.bashrc
source ~/.bashrc
```

## 2. Add Symbol Libraries

1. Locate KiCad's symbol library table file:
   - Windows: `%APPDATA%\kicad\8.0\sym-lib-table`
   - Linux/macOS: `~/.config/kicad/8.0/sym-lib-table`
2. Open the file in a text editor
3. Find the closing parenthesis of the last library entry
4. Copy all entries from `tables\sym-lib-table` and paste them before the final closing parenthesis

## 3. Add Footprint Libraries

1. Locate KiCad's footprint library table file:
   - Windows: `%APPDATA%\kicad\8.0\fp-lib-table`
   - Linux/macOS: `~/.config/kicad/8.0/fp-lib-table`
2. Open the file in a text editor
3. Find the closing parenthesis of the last library entry
4. Copy all entries from `tables\fp-lib-table` and paste them before the final closing parenthesis

## 4. Verify Setup

After adding the libraries:

1. Save the table files
2. Restart KiCad to ensure the environment variable is recognized
3. Open a schematic and verify that the symbol libraries are available
4. Open a PCB layout and verify that the footprint libraries are available

## Troubleshooting

If the libraries are not found:

1. Verify that the environment variable is set correctly:
   - Windows: Open Command Prompt and type `echo %.LAB_DIR%`
   - Linux/macOS: Open Terminal and type `echo $.LAB_DIR`
2. Check that the paths in the library tables are correct
3. Ensure you have the necessary permissions to access the library files

## Note

The library tables in this directory are specific to this library and should be kept in version control. 
They contain only the entries for this library's symbols and footprints.