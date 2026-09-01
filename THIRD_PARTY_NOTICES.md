# Third-Party Notices

This repository includes material from the following third-party sources.

## Espressif KiCad Library

Included material:

- The `ESP32-P4X` symbol in `symbols/AharoniLab_MCU.kicad_sym`
- `footprints/AharoniLab_Package_DFN_QFN.pretty/ESP32-P4.kicad_mod`

Source: <https://github.com/espressif/kicad-libraries>
Upstream revision: `dd76561`
License: Creative Commons Attribution-ShareAlike 4.0 International, with the
KiCad library design exception described in the upstream `LICENSE.md`.

Modifications: extracted the ESP32-P4X symbol and shared ESP32-P4 footprint
into Aharoni Lab library categories; updated the footprint library reference,
KiCad format metadata, validation metadata, and source attribution.

## SnapMagic ESP32-P4 3D Model

Included material:

- `3dmodels/AharoniLab_Package_DFN_QFN.3dshapes/ESP32-P4.step`

Source: <https://www.snapeda.com/parts/ESP32-P4NRW16/Espressif%20Systems/view-part/>
Original download: `ESP32-P4NRW16--3DModel-STEP-510211.STEP`
Original model title: `ESP32-P4NRW32.STEP`
SHA-256 after line-ending normalization: `8f2f73a16d7b0102adb99f68953d98fea7fcd68d85b1f989f208c0dadcfbe0ab`
License: Creative Commons Attribution-ShareAlike 4.0 International, with
SnapMagic Design Exception 1.0.

Modifications: renamed the file to `ESP32-P4.step` and linked it to the
ESP32-P4 footprint with a -90-degree X rotation. The STEP geometry itself is
unchanged.
