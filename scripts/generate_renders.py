#!/usr/bin/env python3
"""
Script to generate renders of symbols, footprints, and 3D models for PR review.
Uses KiCad's command-line tools to generate PNG images.
"""
import os
import sys
import glob
import subprocess
import cairosvg
import shutil
from pathlib import Path
from typing import List, Tuple, Dict

LAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_kicad_cli(command: List[str]) -> Tuple[bool, str]:
    """Run a KiCad CLI command and return success status and output. Print stdout and stderr for debugging."""
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False, f"Error: {e.stderr}"

def generate_symbol_render(symbol_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a symbol using KiCad's command-line tools (SVG) and convert to PNG."""
    symbol_name = os.path.splitext(os.path.basename(symbol_file))[0]
    outputs = {}
    temp_dir = os.path.join(LAB_ROOT, "temp_render")
    os.makedirs(temp_dir, exist_ok=True)
    sch_file = os.path.join(temp_dir, "temp.kicad_sch")
    with open(sch_file, "w") as f:
        f.write(f"""(kicad_sch (version 20211123) (generator eeschema)
  (paper "A4")
  (lib_symbols
    (symbol "{symbol_name}" (pin_numbers hide) (pin_names (offset 0.254))
      (in_bom yes) (on_board yes)
      (property "Reference" "{symbol_name}" (id 0) (at 0 0 0)
        (effects (font (size 1.27 1.27)) (justify left))
      )
      (property "Value" "{symbol_name}" (id 1) (at 0 2.54 0)
        (effects (font (size 1.27 1.27)) (justify left))
      )
      (property "Footprint" "" (id 2) (at 0 5.08 0)
        (effects (font (size 1.27 1.27)) (justify left))
      )
    )
  )
  (junction (at 0 0) (diameter 0) (color 0 0 0 0))
  (wire (pts (xy 0 0) (xy 0 0)) (stroke (width 0) (type default)))
  (label "{symbol_name}" (at 0 0 0) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify left))
  )
)""")
    views = {
        "default": {
            "svg": os.path.join(output_dir, f"{symbol_name}_symbol.svg"),
            "png": os.path.join(output_dir, f"{symbol_name}_symbol.png"),
            "options": []
        },
        "bw": {
            "svg": os.path.join(output_dir, f"{symbol_name}_symbol_bw.svg"),
            "png": os.path.join(output_dir, f"{symbol_name}_symbol_bw.png"),
            "options": ["--black-and-white"]
        },
        "large": {
            "svg": os.path.join(output_dir, f"{symbol_name}_symbol_large.svg"),
            "png": os.path.join(output_dir, f"{symbol_name}_symbol_large.png"),
            "options": []
        }
    }
    for view_name, view_config in views.items():
        # Use a unique output directory for each view
        view_outdir = os.path.join(output_dir, f"{symbol_name}_{view_name}_svgdir")
        os.makedirs(view_outdir, exist_ok=True)
        success, output = run_kicad_cli([
            "kicad-cli", "sch", "export", "svg",
            "--output", view_outdir,
            *view_config["options"],
            sch_file
        ])
        temp_svg = os.path.join(view_outdir, "temp.svg")
        if success and os.path.exists(temp_svg):
            try:
                shutil.move(temp_svg, view_config["svg"])
                cairosvg.svg2png(url=view_config["svg"], write_to=view_config["png"])
                outputs[view_name] = view_config["png"]
            except Exception as e:
                print(f"Failed to convert SVG to PNG for {view_name}: {e}")
        else:
            print(f"Failed to generate {view_name} symbol render: {output}")
        # Clean up the view output directory
        shutil.rmtree(view_outdir, ignore_errors=True)
    # Clean up temporary files
    os.remove(sch_file)
    os.rmdir(temp_dir)
    return len(outputs) > 0, outputs

def generate_footprint_render(footprint_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a footprint using KiCad's command-line tools."""
    footprint_name = os.path.splitext(os.path.basename(footprint_file))[0]
    outputs = {}
    
    # Generate different views of the footprint
    views = {
        "top": {
            "output": os.path.join(output_dir, f"{footprint_name}_top.png"),
            "options": ["--page-size-mode", "1", "--black-and-white", "false", "--layers", "F.Cu,F.SilkS,F.Mask"]
        },
        "bottom": {
            "output": os.path.join(output_dir, f"{footprint_name}_bottom.png"),
            "options": ["--page-size-mode", "1", "--black-and-white", "false", "--layers", "B.Cu,B.SilkS,B.Mask"]
        },
        "all_layers": {
            "output": os.path.join(output_dir, f"{footprint_name}_all.png"),
            "options": ["--page-size-mode", "1", "--black-and-white", "false", "--layers", "*.Cu,*.SilkS,*.Mask"]
        },
        "large": {
            "output": os.path.join(output_dir, f"{footprint_name}_large.png"),
            "options": ["--page-size-mode", "2", "--black-and-white", "false", "--layers", "*.Cu,*.SilkS,*.Mask"]
        }
    }
    
    for view_name, view_config in views.items():
        success, output = run_kicad_cli([
            "kicad-cli", "pcb", "export", "png",
            "--output", view_config["output"],
            *view_config["options"],
            footprint_file
        ])
        if success:
            outputs[view_name] = view_config["output"]
        else:
            print(f"Failed to generate {view_name} footprint render: {output}")
    
    return len(outputs) > 0, outputs

def generate_3d_render(model_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a 3D model using KiCad's command-line tools."""
    model_name = os.path.splitext(os.path.basename(model_file))[0]
    outputs = {}
    
    # Create a temporary PCB file with the 3D model
    temp_dir = os.path.join(LAB_ROOT, "temp_render")
    os.makedirs(temp_dir, exist_ok=True)
    
    pcb_file = os.path.join(temp_dir, "temp.kicad_pcb")
    with open(pcb_file, "w") as f:
        f.write(f"""(kicad_pcb (version 20211123) (generator pcbnew)
  (paper "A4")
  (setup
    (last_trace_width 0.25)
    (trace_clearance 0.2)
    (zone_clearance 0.508)
    (zone_45_only no)
    (trace_min 0.2)
    (segment_width 0.2)
    (edge_width 0.1)
    (via_size 0.8)
    (via_drill 0.4)
    (via_min_size 0.4)
    (via_min_drill 0.3)
    (uvia_size 0.3)
    (uvia_drill 0.1)
    (uvias_allowed no)
    (uvia_min_size 0.2)
    (uvia_min_drill 0.1)
    (pcb_text_width 0.3)
    (pcb_text_size 1.5 1.5)
    (mod_edge_width 0.12)
    (mod_text_size 1 1)
    (mod_text_width 0.15)
    (pad_size 1.5 1.5)
    (pad_drill 0.6)
    (pad_to_mask_clearance 0.051)
    (aux_axis_origin 0 0)
    (visible_elements
      (pad_fp_text yes)
      (pad_fp_value yes)
      (fp_text yes)
      (fp_value yes)
      (fp_other yes)
      (edge_cuts yes)
      (courtyard yes)
      (fab_layers yes)
      (other_layers yes)
    )
  )
  (module "{model_name}" (layer F.Cu) (tedit 0)
    (at 0 0 0)
    (model "{model_file}"
      (at (xyz 0 0 0))
      (scale (xyz 1 1 1))
      (rotate (xyz 0 0 0))
    )
  )
)""")
    
    # Generate different views of the 3D model
    views = {
        "front": {
            "output": os.path.join(output_dir, f"{model_name}_3d_front.png"),
            "options": ["--page-size-mode", "1", "--view", "front"]
        },
        "top": {
            "output": os.path.join(output_dir, f"{model_name}_3d_top.png"),
            "options": ["--page-size-mode", "1", "--view", "top"]
        },
        "iso": {
            "output": os.path.join(output_dir, f"{model_name}_3d_iso.png"),
            "options": ["--page-size-mode", "1", "--view", "iso"]
        },
        "large": {
            "output": os.path.join(output_dir, f"{model_name}_3d_large.png"),
            "options": ["--page-size-mode", "2", "--view", "iso"]  # Use A3 for larger view
        }
    }
    
    for view_name, view_config in views.items():
        success, output = run_kicad_cli([
            "kicad-cli", "pcb", "export", "3d",
            "--output", view_config["output"],
            *view_config["options"],
            pcb_file
        ])
        if success:
            outputs[view_name] = view_config["output"]
        else:
            print(f"Failed to generate {view_name} 3D render: {output}")
    
    # Clean up temporary files
    os.remove(pcb_file)
    os.rmdir(temp_dir)
    
    return len(outputs) > 0, outputs

def main():
    """Generate renders for all modified components."""
    # Get the list of modified files from GitHub Actions
    modified_files = os.environ.get("MODIFIED_FILES", "").split()
    if not modified_files:
        print("No modified files found")
        sys.exit(0)
    
    # Create output directory for renders
    output_dir = os.path.join(LAB_ROOT, "renders")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each modified file
    all_renders = {}
    for file in modified_files:
        if file.endswith(".kicad_sym"):
            print(f"Generating renders for symbol: {file}")
            success, outputs = generate_symbol_render(file, output_dir)
            if success:
                all_renders[file] = outputs
            else:
                print(f"Failed to generate symbol renders: {outputs}")
        elif file.endswith(".kicad_mod"):
            print(f"Generating renders for footprint: {file}")
            success, outputs = generate_footprint_render(file, output_dir)
            if success:
                all_renders[file] = outputs
            else:
                print(f"Failed to generate footprint renders: {outputs}")
        elif file.endswith((".wrl", ".step")):
            print(f"Generating renders for 3D model: {file}")
            success, outputs = generate_3d_render(file, output_dir)
            if success:
                all_renders[file] = outputs
            else:
                print(f"Failed to generate 3D model renders: {outputs}")
    
    # Create a summary of generated renders
    if all_renders:
        print("\nGenerated renders:")
        for file, outputs in all_renders.items():
            print(f"\n{os.path.basename(file)}:")
            for view_name, output_file in outputs.items():
                print(f"  - {view_name}: {os.path.basename(output_file)}")
    else:
        print("\nNo renders were generated")

if __name__ == "__main__":
    main() 