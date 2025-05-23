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
from PIL import Image

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

def optimize_png(png_path: str) -> None:
    """Optimize PNG file size using PIL."""
    try:
        original_size = os.path.getsize(png_path)
        img = Image.open(png_path)
        img.save(png_path, optimize=True, quality=85)
        new_size = os.path.getsize(png_path)
        print(f"Optimized {os.path.basename(png_path)}: {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB")
    except Exception as e:
        print(f"Warning: Failed to optimize PNG {png_path}: {e}")

def is_component_file(file_path: str) -> bool:
    """Check if a file is a component file (not a library file)."""
    print(f"\nChecking if {file_path} is a component file:")

    # Normalize path for consistent splitting
    norm_path = os.path.normpath(file_path)
    parts = norm_path.split(os.sep)

    # We want files like symbols/passive/capacitors/capacitors.kicad_sym
    # That is: [symbols, passive, capacitors, capacitors.kicad_sym]
    if len(parts) >= 3 and parts[0] in ["symbols", "footprints", "3dmodels"]:
        print(f"  Processing: File is in a subdirectory of {parts[0]}")
        return True

    print(f"  Skipping: File is not in a subdirectory of symbols/footprints/3dmodels")
    return False

def generate_symbol_render(symbol_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a symbol using KiCad's command-line tools."""
    if not is_component_file(symbol_file):
        return False, {}
        
    print(f"\nGenerating renders for symbol: {symbol_file}")
    symbol_name = os.path.splitext(os.path.basename(symbol_file))[0]
    outputs = {}
    
    # Create a temporary project for rendering
    temp_dir = os.path.join(LAB_ROOT, "temp_render")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create a minimal schematic file
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
        
        # Generate different views of the symbol
        views = {
            "default": {
                "svg_output": os.path.join(output_dir, f"{symbol_name}_symbol.svg"),
                "png_output": os.path.join(output_dir, f"{symbol_name}_symbol.png"),
                "options": []
            },
            "bw": {
                "svg_output": os.path.join(output_dir, f"{symbol_name}_symbol_bw.svg"),
                "png_output": os.path.join(output_dir, f"{symbol_name}_symbol_bw.png"),
                "options": ["--black-and-white"]
            }
        }
        
        for view_name, view_config in views.items():
            print(f"\nGenerating {view_name} view...")
            # Export SVG using kicad-cli
            success, output = run_kicad_cli([
                "kicad-cli", "sch", "export", "svg",
                "--output", view_config["svg_output"],
                *view_config["options"],
                sch_file
            ])
            if success:
                print(f"Converting SVG to PNG for {view_name} view...")
                try:
                    cairosvg.svg2png(url=view_config["svg_output"], write_to=view_config["png_output"])
                    optimize_png(view_config["png_output"])
                    outputs[view_name] = view_config["png_output"]
                    print(f"Successfully generated {view_name} view")
                except Exception as e:
                    print(f"Failed to convert SVG to PNG: {e}")
            else:
                print(f"Failed to generate {view_name} symbol render: {output}")
        
        return len(outputs) > 0, outputs
    finally:
        # Clean up temporary files
        if os.path.exists(sch_file):
            os.remove(sch_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def generate_footprint_render(footprint_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a footprint using KiCad's command-line tools."""
    if not is_component_file(footprint_file):
        print(f"Skipping library file: {footprint_file}")
        return False, {}
        
    print(f"\nGenerating renders for footprint: {footprint_file}")
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
        }
    }
    
    for view_name, view_config in views.items():
        print(f"\nGenerating {view_name} view...")
        success, output = run_kicad_cli([
            "kicad-cli", "pcb", "export", "png",
            "--output", view_config["output"],
            *view_config["options"],
            footprint_file
        ])
        if success:
            print(f"Optimizing {view_name} view...")
            optimize_png(view_config["output"])
            outputs[view_name] = view_config["output"]
            print(f"Successfully generated {view_name} view")
        else:
            print(f"Failed to generate {view_name} footprint render: {output}")
    
    return len(outputs) > 0, outputs

def generate_3d_render(model_file: str, output_dir: str) -> Tuple[bool, Dict[str, str]]:
    """Generate renders of a 3D model using KiCad's command-line tools."""
    if not is_component_file(model_file):
        print(f"Skipping library file: {model_file}")
        return False, {}
        
    print(f"\nGenerating renders for 3D model: {model_file}")
    model_name = os.path.splitext(os.path.basename(model_file))[0]
    outputs = {}
    
    # Create a temporary PCB file with the 3D model
    temp_dir = os.path.join(LAB_ROOT, "temp_render")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
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
            "iso": {
                "output": os.path.join(output_dir, f"{model_name}_3d_iso.png"),
                "options": ["--page-size-mode", "1", "--view", "iso"]
            }
        }
        
        for view_name, view_config in views.items():
            print(f"\nGenerating {view_name} view...")
            success, output = run_kicad_cli([
                "kicad-cli", "pcb", "export", "3d",
                "--output", view_config["output"],
                *view_config["options"],
                pcb_file
            ])
            if success:
                print(f"Optimizing {view_name} view...")
                optimize_png(view_config["output"])
                outputs[view_name] = view_config["output"]
                print(f"Successfully generated {view_name} view")
            else:
                print(f"Failed to generate {view_name} 3D render: {output}")
        
        return len(outputs) > 0, outputs
    finally:
        # Clean up temporary files
        if os.path.exists(pcb_file):
            os.remove(pcb_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    """Generate renders for all modified components."""
    # Get the list of modified files from GitHub Actions
    modified_files = os.environ.get("MODIFIED_FILES", "").split()
    if not modified_files:
        print("No modified files found")
        sys.exit(0)
    
    print(f"\nProcessing {len(modified_files)} modified files:")
    for file in modified_files:
        print(f"- {file}")
    
    # Create output directory for renders
    output_dir = os.path.join(LAB_ROOT, "renders")
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    
    # Process each modified file
    all_renders = {}
    for file in modified_files:
        if file.endswith(".kicad_sym"):
            success, outputs = generate_symbol_render(file, output_dir)
            if success:
                all_renders[file] = outputs
        elif file.endswith(".kicad_mod"):
            success, outputs = generate_footprint_render(file, output_dir)
            if success:
                all_renders[file] = outputs
        elif file.endswith((".wrl", ".step")):
            success, outputs = generate_3d_render(file, output_dir)
            if success:
                all_renders[file] = outputs
    
    # Create a summary of generated renders
    if all_renders:
        print("\nGenerated renders summary:")
        total_size = 0
        for file, outputs in all_renders.items():
            print(f"\n{os.path.basename(file)}:")
            for view_name, output_file in outputs.items():
                size = os.path.getsize(output_file)
                total_size += size
                print(f"  - {view_name}: {os.path.basename(output_file)} ({size/1024:.1f}KB)")
        print(f"\nTotal size of generated renders: {total_size/1024:.1f}KB")
    else:
        print("\nNo renders were generated")

if __name__ == "__main__":
    main() 