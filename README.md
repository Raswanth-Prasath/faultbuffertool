# Fault Buffer Tool for QGIS

The Fault Buffer Tool is a QGIS plugin that creates uncertainty buffers around mapped fault traces based on literature-backed values. This tool supports geologists and engineers in visualizing and quantifying the uncertainty in fault locations for hazard assessment and scientific research.

## Description

The Fault Buffer Tool allows users to define, justify, and plot well-informed uncertainty zones around mapped fault locations. It offers several approaches to uncertainty calculation based on peer-reviewed literature and geologic judgment.

Developed at Arizona State University, this tool aims to facilitate the use and advancement of fault location uncertainty analysis by the broader fault mapping community.

## Features

- **Multiple uncertainty calculation approaches:**
  - General uncertainty (literature-based values)
  - Uncertainty with ranking based on:
    - Fault confidence (strong, distinct, weak, uncertain)
    - Primary/secondary classification
    - Simple/complex classification
  - Geologic judgment (custom uncertainty values)

- **Fault type handling:**
  - Strike-slip faults (symmetric buffers, 1:1 ratio)
  - Normal faults (asymmetric buffers, 1:4 ratio)
  - Reverse faults (asymmetric buffers, 1:2 ratio)

- **Confidence intervals:**
  - 50th percentile
  - 84th percentile
  - 97th percentile

## Installation

1. Download the plugin ZIP file from the [GitHub repository](https://github.com/Raswanth-Prasath/faultbuffertool)
2. In QGIS, go to **Plugins → Manage and Install Plugins**
3. Select **Install from ZIP**
4. Browse to the downloaded ZIP file and click **Install Plugin**
5. Once installed, the plugin will appear in the **Plugins** menu and toolbar

## Usage

1. **Prepare your fault map:**
   - Create a fault line shapefile with appropriate attributes
   - Required attributes depend on your chosen uncertainty approach:
     - `Quality` (1-4): Confidence ranking (1=uncertain, 2=weak, 3=distinct, 4=strong)
     - `PriSec` (P/S): Primary or secondary fault classification
     - `SimpComp` (S/C): Simple or complex fault classification
     - `Dip_direct` (N,S,E,W,NE,SE,SW,NW): Fault dip direction for asymmetric buffers
     - `Fault_type` (S,N,R): Strike-slip, Normal, or Reverse
     - `geo_unc`: Custom uncertainty value (only needed for geologic judgment option)

2. **Launch the plugin:**
   - Go to **Plugins → FaultBufferTool → Fault Buffer Tool**

3. **Set parameters:**
   - Select the input fault line layer
   - Choose the output file location
   - Select the error approach:
     - General uncertainty
     - Uncertainty with ranking (select criteria to use)
     - Geologic judgment
   - Choose confidence interval (50th, 84th, or 97th percentile)
   - Select fault type handling method

4. **Generate buffers:**
   - Click **OK** to create the buffer shapefile
   - The new layer will be added to your map with appropriate styling

## Input Requirements

- The fault shapefile can have a coordinate reference system of latitude and longitude (EPSG:4326) or the local UTM zone
- The plugin will output the buffer file in the local UTM zone

## Example Attributes

| Attribute | Description | Values |
|-----------|-------------|--------|
| Quality | Fault confidence | 4 (strong), 3 (distinct), 2 (weak), 1 (uncertain) |
| PriSec | Primary or secondary | P (primary), S (secondary) |
| SimpComp | Simple or complex | S (simple), C (complex) |
| Dip_direct | Fault dip direction | N, E, S, W, NE, SE, SW, NW |
| Fault_type | Type of fault | S (strike-slip), N (normal), R (reverse) |
| geo_unc | Custom uncertainty value | Integer value (in meters or feet) |

## Credits

**Developers:**
- Raswanth Prasath S V

**Project Contributors:**
- Chelsea Scott

## Acknowledgments 

-We acknowledge support for this project from Pacific Gas and Electric, Co. 

## License

This plugin is licensed under GNU General Public License v2.0 or later.

<!-- ## Citation

If you use this tool in your research or publications, please cite:
- Scott, C., Prasath, R., Arrowsmith, R., Madugo, C., & Kottke, A. (2025). Fault Buffer Tool: A GIS-based tool for quantifying uncertainty in mapped fault locations. *Journal of Structural Geology*. -->

## Support

For issues, feature requests, or questions, please use the [GitHub issue tracker](https://github.com/Raswanth-Prasath/faultbuffertool/issues).
