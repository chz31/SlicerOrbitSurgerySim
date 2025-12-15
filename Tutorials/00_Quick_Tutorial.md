# 🔄 Quick Tutorial: Plate Registration and Fit Comparison
*(~10–20 minutes, depending on your familiarity with 3D Slicer)*

This quick tutorial walks you through **registering two preformed orbital plates** and **comparing their fit** using **sample data prepared with this extension**.

No external data preparation is required.

---

## Overview of the workflow

You will:
1. Install the extension and download prepared sample data
2. Register a large and a small preformed orbital plate
3. Generate quantitative plate-to-orbit fit metrics
4. Compare plate fit across candidates

---

## 1. Install the Extension

1. Download and install **3D Slicer 5.10.0** from:  
   https://download.slicer.org/

2. Open **Extension Manager** (top-right corner of Slicer).

3. Search for **SlicerOrbitSurgerySim**, install it, and **restart Slicer**.

> **Note**  
> The **SlicerMorph** extension is a dependency and will be installed automatically.  
> If it fails to install, please install **SlicerMorph** manually from Extension Manager.

<img src="img/quick_step01.png" width="400">

---

## 2. Load Sample Data

This tutorial uses open-source segmentations derived from the **CBCTDental Surgery** dataset from Slicer's Sample Data module.

1. Open **Module Finder** → **Sample Data**.
2. Locate **PlateRegistrationSampleDataFiles**.
3. Click it and select a directory to download and unzip the sample data.

<img src="img/quick_step02.png" width="350">
<img src="img/quick_step03.png" width="250">

### Load the following files into Slicer
From the unzipped folder, drag and drop below files into Slicer:

- `skull_sample_left_fracture.ply`
- `left_orbit_lm.mrk.json`
- `synth_plate_large_left.ply`
- `synth_plate_large_left_lm.mrk.json`

Click **OK** when prompted.

<img src="img/quick_step04.png" width="300">
<img src="img/quick_step05.png" width="250">

### Load the reference CT volume
In **Sample Data**, click **CBCTDental Surgery**.

- The CT volume will load automatically (the skull model is segmented from the 'PostDentalSurgery' volume).
- Scroll through slices or drag the slice offset (top-bar of a slice window) to locate the orbit.
- Hold right mouse button and drag: zoom  
- Hold middle mouse button and drag: move slice position

<img src="img/quick_step06.png" width="300">
<img src="img/quick_step07.png" width="400">

(Optional) Switch to **Conventional** or **Conventional Widescreen** layout for better 2D/3D visualization.

<img src="img/quick_step08.png" width="250">

---

## 3. Open PlateRegistration and Select Inputs

1. Open **Module Finder**, type **PlateRegistration**, and switch to the module.

<img src="img/quick_step09.png" width="400">

> **First-time use notice**  
> Required Python packages will be installed automatically.  
> This may take a few minutes. Please do not close Slicer.

<img src="img/quick_step10.png" width="250">

2. In the **Input** section:
   - Select the **orbit model**
   - Select the **plate model**
   - Select the corresponding **landmark files**

<img src="img/quick_step11.png" width="500">

---

## 4. Initial Registration

1. In **Initial Registration**, click:
   - **Initial registration**
   - **Registration posterior stop**

<img src="img/quick_step12.png" width="450">

The plate should now be roughly aligned with the orbit.

<img src="img/quick_step13.png" width="350">

A new folder will appear in the **Node Viewer** to store registration results.  
Folder name format: _plate_model_name_timestamp_
- A timestamp is appended to ensure unique folder names

<img src="img/quick_step14.png" width="500">

---

## 5. Manual Plate Adjustment

1. In **Plate interactive adjustment**, check  
   **Enable 3D interaction transform handle**.

> Additional Python packages may be installed on first use.

<img src="img/quick_step15.png" width="500">
<img src="img/quick_step16.png" width="300">

2. A transform handle appears:
   - Rotation center: posterior stop landmark
   - Subsampled plate shown in blue

Use the handles in **3D or slice views** to rotate or translate the plate.

<img src="img/quick_step17.png" width="500">

3. Click **Mark intersection** to detect plate–orbit intersections:
   - Yellow line: 3D view
   - Yellow dots: 2D slices
   - Intersection percentage shown in the info box

<img src="img/quick_step18.png" width="400">
<img src="img/quick_step19.png" width="550">

> **Note**  
> The sample plates were manually created for demonstration purposes and may not perfectly fit the orbit.  
> Minor intersections are acceptable for this tutorial.

---

## 6. Save Registration Results

1. Click **Finalize Registration**.

<img src="img/quick_step20.png" width="500">

2. Choose a root directory (e.g., `~/Downloads/test_orbitSim`).

3. Click **Save current plate registration results**.

<img src="img/quick_step21.png" width="500">

---

## 7. Register a Second Plate

Drag the following files into Slicer:

- `synth_plate_small_left.ply`
- `synth_plate_small_left_lm.mrk.json`

<img src="img/quick_step22.png" width="500">

Repeat **Steps 3–6**, saving results into the **same root directory**.

---

## 8. Generate Fit Metrics

Fit metrics are computed using:
1. Vertex-to-surface distances (adapted from *Model-to-Model Distance*)
2. Distances from plate-edge points projected onto the reconstructed orbit

<img src="img/quick_step23.png" width="300">

### Prepare margin points
Copy the folders:

- `synth_plate_large_left`
- `synth_plate_small_left`

from: `./plateRegistrationSampleData/plateMarginPtsForProj`
into: `./your_root_folder/points_for_projection`.

<img src="img/quick_step24.png" width="700">

### Load reconstructed orbit
Drag `skull_sample_left_orbit_recon.ply` into Slicer.

### Generate fit metrics
Switch to the **Plate fit metrics** tab.

<img src="img/quick_step24_2.png" width="500">

Ensure:
- **Plate margin points root directory** points to `./your_root_folder/points_for_projection`
- **Reconstructed orbit model** is selected

<img src="img/quick_step25.png" width="700">

Click:
- **Compute distance map**
- **Project points from each plate**

<img src="img/quick_step26.png" width="500">

Results are saved under: `./your_root_folder/fit_output/fit_metrics`

### Optional visualization of fit metrics
To visualize plate-to-orbit heatmap and point projection results, select a plate folder under `./your_root_folder/fit_output/fit_metrics`, and click the two visualization buttons. <br>
<img src="img/quick_step27.png" width="800"><br>
<img src="img/quick_step28.png" width="350"><br>

>**Tips**: 
>You can hide loaded files by clicking and closing the "eye" icon to turn off visualizations in the top "Node" box or simply right click and delete them. <br>

<img src="img/quick_step29.png" width="450"><br>

---

## 9. Compare Plate Fit

Switch to **Compare fit** tab.

<img src="img/quick_step30.png" width="450">

Ensure:
- **Compare distances between plate margins and orbits** is checked
- Directory points to `./your_root_folder/fit_output/fit_metrics`

<img src="img/quick_step31.png" width="600">

Click **Compare fitness**.

Outputs include:
- Plate rankings (mean & per-edge distances)
- Scatter plot comparing plates

<img src="img/quick_step32.png" width="400">
<img src="img/quick_step33.png" width="350">

Results are saved under: `./your_root_folder/fit_output/compare_fit_comparison`

### Optional visualization
- Enable **Visualize existing results**
- Show superimposed plates and margin points

<img src="img/quick_step34.png" width="500">
<img src="img/quick_step35.png" width="500">

---


