# Installation Guide

## Prerequisites

- **KiCad 10 or 9** -- launch it at least once to create the config directory
- **Git**
- **Python 3.8+**

## Automated Install (Recommended)

```bash
# Clone the library
git clone https://github.com/Aharoni-Lab/kicad-lab-library.git ~/kicad-libraries/kicad-lab-library

# Run the install script
cd ~/kicad-libraries/kicad-lab-library
python scripts/install.py
```

The script will:
1. Detect your KiCad config directory (supports both 10 and 9)
2. Set the `AHARONI_LAB_KICAD_LIB` environment variable in KiCad
3. Add all library entries to KiCad's global symbol and footprint tables

### Preview Changes First

```bash
python scripts/install.py --dry-run
```

## Manual Install

If the script doesn't work for your setup:

### 1. Set Environment Variable

Open KiCad > **Preferences** > **Configure Paths**. Add:

| Name | Path |
|------|------|
| `AHARONI_LAB_KICAD_LIB` | Full path to your cloned `kicad-lab-library` directory |

### 2. Add Symbol Libraries

Open KiCad > **Preferences** > **Manage Symbol Libraries** > **Global Libraries** tab. Click **Add** (folder icon) and browse to each `.kicad_sym` file in `symbols/`.

### 3. Add Footprint Libraries

Open KiCad > **Preferences** > **Manage Footprint Libraries** > **Global Libraries** tab. Click **Add** (folder icon) and browse to each `.pretty` directory in `footprints/`.

## Updating

```bash
cd ~/kicad-libraries/kicad-lab-library
git pull
python scripts/install.py
```

The install script skips entries that are already present, so re-running is safe.

## Uninstalling

```bash
cd ~/kicad-libraries/kicad-lab-library
python scripts/install.py --uninstall
```

This removes all `AharoniLab_` entries from KiCad's global tables and removes the environment variable.

## Verification

After installing, open KiCad:
1. Check **Preferences > Configure Paths** -- `AHARONI_LAB_KICAD_LIB` should point to the repo
2. Check **Preferences > Manage Symbol Libraries** -- any `AharoniLab_*` entries should be listed
3. Check **Preferences > Manage Footprint Libraries** -- any `AharoniLab_*` entries should be listed
4. Once components are added, search for `AharoniLab` in the Symbol Chooser to verify

## Troubleshooting

### "No KiCad config directory found"

Make sure you've launched KiCad at least once. The config directory is created on first launch:
- **Windows**: `%APPDATA%\kicad\10.0\` (or `9.0`)
- **macOS**: `~/Library/Preferences/kicad/10.0/` (or `9.0`)
- **Linux**: `~/.config/kicad/10.0/` (or `9.0`)

### Libraries don't appear in KiCad

1. Restart KiCad after running the install script
2. Check **Preferences > Configure Paths** -- `AHARONI_LAB_KICAD_LIB` should point to the repo
3. Check **Preferences > Manage Symbol Libraries** -- `AharoniLab_*` entries should be listed

### Path issues on Windows

The install script uses forward slashes in paths. If you see issues, check that the path in **Configure Paths** uses forward slashes (e.g., `C:/Users/you/kicad-libraries/kicad-lab-library`).
