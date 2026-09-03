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

## KiCad Official Libraries

Included material:

- The `TLV62568DBV`, `TLV62569DBV`, and `TLV62569DDC` symbols in
  `symbols/AharoniLab_Power.kicad_sym` (from `Regulator_Switching`)
- `footprints/AharoniLab_Package_SOT.pretty/SOT-23-5.kicad_mod`
  (from `Package_TO_SOT_SMD.pretty`)
- `footprints/AharoniLab_Package_SOT.pretty/SOT-23-6.kicad_mod`: pad, fab, and
  courtyard geometry reproduced from `Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod`
  (silkscreen and metadata redrawn)
- `3dmodels/AharoniLab_Package_SOT.3dshapes/SOT-23-5.step` and `SOT-23-6.step`
  (from `Package_TO_SOT_SMD.3dshapes`)
- The `TestPoint` symbol in `symbols/AharoniLab_Connector.kicad_sym`
  (from `Connector`)
- `3dmodels/AharoniLab_Inductor_SMD.3dshapes/L_Murata_DFE201610P.step`
  (from `Inductor_SMD.3dshapes`), used as a same-size stand-in model for the
  TDK `L_TDK_TFM201610ALMA` footprint
- The `W25Q128JVSIQ` symbol in `symbols/AharoniLab_Memory.kicad_sym`
  (from `Memory_Flash`: `W25Q128JVS`, derived upstream from `W25Q32JVSS`)
- The `Crystal_GND24` symbol in `symbols/AharoniLab_Passive.kicad_sym`
  (from `Device`)
- `footprints/AharoniLab_Package_SO.pretty/SOIC-8_5.3x5.3mm_P1.27mm.kicad_mod`
  and `3dmodels/AharoniLab_Package_SO.3dshapes/SOIC-8_5.3x5.3mm_P1.27mm.step`
  (from `Package_SO`)
- `footprints/AharoniLab_Crystal.pretty/Crystal_SMD_3225-4Pin_3.2x2.5mm.kicad_mod`
  and `3dmodels/AharoniLab_Crystal.3dshapes/Crystal_SMD_3225-4Pin_3.2x2.5mm.step`
  (from `Crystal`)
- Symbol graphics of `61201221621`, `FTSH-106-01-L-DV` and `B3B-PH-K-S` in
  `symbols/AharoniLab_Connector.kicad_sym` (from `Connector_Generic`:
  `Conn_02x06_Odd_Even` and `Conn_01x03`)
- `footprints/AharoniLab_Connector.pretty/JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical.kicad_mod`
  and its STEP model (from `Connector_JST`)
- `footprints/AharoniLab_Connector.pretty/Wuerth_WR-BHD_61201221621_2x06_P2.54mm_Vertical.kicad_mod`:
  geometry derived from `Connector_IDC.pretty/IDC-Header_2x06_P2.54mm_Vertical.kicad_mod`;
  `3dmodels/AharoniLab_Connector.3dshapes/IDC-Header_2x06_P2.54mm_Vertical.step`
  (from `Connector_IDC.3dshapes`)
- `3dmodels/AharoniLab_Connector.3dshapes/PinHeader_2x06_P1.27mm_Vertical_SMD.step`
  (from `Connector_PinHeader_1.27mm.3dshapes`), stand-in model for the Samtec
  FTSH-106 footprints
- `footprints/AharoniLab_LED_SMD.pretty/LED_0805_2012Metric.kicad_mod` and its
  STEP model (from `LED_SMD`)

Sources: <https://gitlab.com/kicad/libraries/kicad-symbols> (revision `b705e03a`),
<https://gitlab.com/kicad/libraries/kicad-footprints> (revision `c2593cf2`),
<https://gitlab.com/kicad/libraries/kicad-packages3D> (revision `e62ed1fc`).
SHA-256 after line-ending normalization:
`SOT-23-5.step` `720a6eab0024069bbee68e7cb4c3ff1149468a34611225cdc852662c5d0ec2b7`,
`SOT-23-6.step` `c9fe686b4d1b56927a41fa84a9bc1efb61d8a45a123a3db43bcaa05c2891d635`,
`L_Murata_DFE201610P.step` `0829341686f236e20609ac5135af9e13e03950a3b8eacf3588f502bb45483e97`,
`SOIC-8_5.3x5.3mm_P1.27mm.step` `121aee742692bb7bc9ef49972786ecb89d1b2d62ab089ed278651a884c800331`,
`Crystal_SMD_3225-4Pin_3.2x2.5mm.step` `d2a89df82ee5f0f56ef23ee59c8161b8d4e92af2b21959d72778316dde3f9f22`,
`IDC-Header_2x06_P2.54mm_Vertical.step` `22db52d400c42c3f1f280f407cfa3b928f5cee52d32e0c24e4ce2542c7fb8bc7`,
`JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical.step` `00cbe1522070150893f96728ffaa78070972f025d63c45f899e18b3060a41f2d`,
`PinHeader_2x06_P1.27mm_Vertical_SMD.step` `dfbdf4cac7fb2444a0fee0da9561e052e641708453d0fad0c510694f3ad40b05`,
`LED_0805_2012Metric.step` `0aa8b791804f5d72a2fc7d1bf231dd9959207d83df8ad801176fbc459f575b98`.
License: Creative Commons Attribution-ShareAlike 4.0 International, with the
KiCad Libraries License exception (<https://www.kicad.org/libraries/license/>).

Modifications: flattened the `TLV62569*` and `W25Q128JVS` symbols, which
upstream derives via `extends`, into complete symbols; added lab validation and
provenance properties; repointed footprint and 3D model references to the
AharoniLab libraries; removed the upstream `KiLib_Generator` property; switched
datasheet links to HTTPS; added lab properties and a default AharoniLab
footprint to the `TestPoint` symbol; moved the box-header polarization notch
to the even-pin row and set 1.1 mm holes per the Wuerth drawing. STEP geometry
is unchanged.

## SnapMagic USB4105-GF-A-120 3D Model

Included material:

- `3dmodels/AharoniLab_Connector.3dshapes/USB4105-GF-A-120.step`

Source: <https://www.snapeda.com/parts/USB4105-GF-A-120/Global+Connector+Technology/view-part/>
Original download: `USB4105-GF-A-120--3DModel-STEP-56544.STEP` (byte-identical to
`USB4105-GF-A-120.step` inside `USB4105-GF-A-120.zip`)
Original model title: `USB4105-GF-A-120.STEP`
SHA-256 after line-ending normalization: `bbfaec895482fcd791d00205404932dd262c6f9e28186767ca85987841c2a718`
License: Creative Commons Attribution-ShareAlike 4.0 International, with
SnapMagic Design Exception 1.0.

Modifications: renamed the file to `USB4105-GF-A-120.step` and linked it to the
`GCT_USB4105-GF-A-120` footprint with a -90-degree X rotation and a 1.1 mm Y
offset. The STEP geometry itself is unchanged. The footprint's pad geometry
follows the SnapEDA footprint from the same download, which matches the GCT
recommended PCB layout; the schematic symbol was redrawn from the GCT datasheet.

## Texas Instruments 3D Models

Included material (TI package models, obtained through Ultra Librarian downloads;
geometry unchanged, each linked to its footprint with a -90-degree X rotation;
TI design-resource terms permit use in designs built around the TI part):

- `3dmodels/AharoniLab_Package_DFN_QFN.3dshapes/DPY0002A.stp`: TI model `DPY0002A_ASM` (X1SON-2, Creo, 2018-09-20), from `ul_TPD1E10B06DPYR.zip`; SHA-256 after line-ending normalization `16f57d9cdb3d67d3c0533ba7742feefd12568538ce331a61799e4f38dabc0ea0`.
- `3dmodels/AharoniLab_Package_DFN_QFN.3dshapes/RUX0012A.stp`: TI model `RUX0012A_ASM` (VQFN-HR-12, Creo, 2018-10-04), from `ul_TPS2121RUXR.zip`; SHA-256 after line-ending normalization `07757e0861b58b27cbcba8e95c9c0f4f5828c1419abbfa2450bebbb7804ad91b`.
