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
- Symbol graphics and pin layout of `TMP117AIDRVR` in
  `symbols/AharoniLab_Sensor.kicad_sym` (from `Sensor_Temperature`:
  `TMP117xxDRV`, derived upstream from `TMP102xxDRL`)
- `3dmodels/AharoniLab_Package_DFN_QFN.3dshapes/WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm.step`
  (from `Package_SON.3dshapes`), linked to the lab-drawn `Texas_DRV0006A_*`
  footprints
- The `AS7341-DLGM` symbol in `symbols/AharoniLab_Sensor.kicad_sym` (from
  `Sensor_Optical`: `AS7341DLG`) and
  `footprints/AharoniLab_Package_DFN_QFN.pretty/AMS_OLGA-8_2x3.1mm_P0.8mm.kicad_mod`
  (from `Package_LGA`; no upstream STEP model exists)
- The `MCP4728T-E_UN` symbol in `symbols/AharoniLab_Misc.kicad_sym`
  (from `Analog_DAC`: `MCP4728`)
- Symbol graphics and pin layout of `TLV4333IPWR` in
  `symbols/AharoniLab_OpAmp.kicad_sym` (from `Amplifier_Operational`: `LM2902`,
  which carries the same quad op-amp pinout)
- The `DMN2056U-7` and `DMN2004DWK-7` symbols in
  `symbols/AharoniLab_Transistor.kicad_sym` (from `Transistor_FET`:
  `Q_NMOS_GSD` and `Q_Dual_NMOS_S1G1D2S2G2D1`)
- The `SN74LVC2G04DBVR` symbol in `symbols/AharoniLab_Logic.kicad_sym`
  (from `74xGxx`: `74LVC2G04`)
- Symbol graphics and pin layout of `TMUX1308PWR` in
  `symbols/AharoniLab_Misc.kicad_sym` (from `Analog_Switch`: `TMUX4051PW`,
  which carries the same TSSOP-16 pinout)
- `footprints/AharoniLab_Package_SO.pretty/MSOP-10_3x3mm_P0.5mm.kicad_mod`,
  `TSSOP-14_4.4x5mm_P0.65mm.kicad_mod` and `TSSOP-16_4.4x5mm_P0.65mm.kicad_mod`
  with their STEP models (from `Package_SO`)
- `footprints/AharoniLab_Package_SOT.pretty/SOT-23.kicad_mod` and its STEP model
  (from `Package_TO_SOT_SMD`)
- `footprints/AharoniLab_Resistor_SMD.pretty/R_1206_3216Metric_N.kicad_mod` and
  `3dmodels/AharoniLab_Resistor_SMD.3dshapes/R_1206_3216Metric.step`
  (from `Resistor_SMD`)
- Silkscreen and courtyard geometry of
  `footprints/AharoniLab_LED_SMD.pretty/LED_PLCC-2_3.5x2.8mm_Nested2214_KA.kicad_mod`
  (from `LED_SMD`: `LED_PLCC-2_3.4x3.0mm_AK`); its land pattern is lab-drawn
  from the Wuerth and ams-OSRAM drawings and no upstream STEP model exists

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
`LED_0805_2012Metric.step` `0aa8b791804f5d72a2fc7d1bf231dd9959207d83df8ad801176fbc459f575b98`,
`WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm.step` `a159a524ab16d3406353a16f8c20b59f5679eea26e2d41174628288b5b9da702`,
`MSOP-10_3x3mm_P0.5mm.step` `b8f88eac3ce221c2ccb0b5048f9ad49c2ef4af148f8ae50c4e232e357683f547`,
`TSSOP-14_4.4x5mm_P0.65mm.step` `3ee5786aae56190997aa793ba3cfc003fd616782770e29719b4562f012982245`,
`TSSOP-16_4.4x5mm_P0.65mm.step` `6ad5e98224d02a427d9a6b929a28dbc158b9925fba5adec12db05079f1016948`,
`SOT-23.step` `dd5d1711204e1d8d26cd11490923bd84340820baa69538c385a4300ec2539bc0`,
`R_1206_3216Metric.step` `f5d1ea5c47935091292bd1c6c698e0df88d3d4bbf92bf66b4c97e49df5be9ebc`.
License: Creative Commons Attribution-ShareAlike 4.0 International, with the
KiCad Libraries License exception (<https://www.kicad.org/libraries/license/>).

Modifications: flattened the `TLV62569*`, `W25Q128JVS` and `TMP117xxDRV` symbols, which
upstream derives via `extends`, into complete symbols; added lab validation and
provenance properties; repointed footprint and 3D model references to the
AharoniLab libraries; removed the upstream `KiLib_Generator` property; switched
datasheet links to HTTPS; added lab properties and a default AharoniLab
footprint to the `TestPoint` symbol; moved the box-header polarization notch
to the even-pin row and set 1.1 mm holes per the Wuerth drawing; reused the
`LM2902`, `Q_NMOS_GSD`, `Q_Dual_NMOS_S1G1D2S2G2D1` and `TMUX4051PW` drawings for
the pin-compatible parts named above, retyped the MCP4728 `RDY/BSY` pin as
open-collector, renamed its `VOUTx` pins to `OUTx`, widened its pin-name offset
to 20 mils (also on the quad op-amp) and retyped the TMUX1308 pin 7 as a hidden
no-connect. STEP geometry
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
