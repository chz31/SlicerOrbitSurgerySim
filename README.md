# SlicerOrbitSurgerySim — A 3D Slicer Extension for orbital surgery simulation and planning

The **SlicerOrbitSurgerySim** extension is used to interactively register and compare the fit of preformed plates for repairing orbital fractures. There are different types and sizes of plates from different vendors. For how preformed and customzed plates are used for repairing orbital fractures, see this [introduction](https://surgeryreference.aofoundation.org/cmf/trauma/midface/orbit-floor/reconstruction).

## Modules
At this moment,this extension contains two modules:

1. **PlateRegistration**
   
   Users can interactively adjust plate positions and compare different types of preformed plates across vendors or different ways of plate placement of the same plate. Repeatable ways of plate fit metrics are generated for ranking the fit of plates or performing more detailed downstream analysis.


2. **mirrorOrbitalRecon**

   This module uses the mirrored model of the unfractured contralateral side to reconstruct the fractured orbit. A reconstructed orbit is highly recommended for generating plate fit metrics. The core functions are rigid and affine registration methods reused from the ALPACA/MALPACA and FastModelAlign modules of the [SlicerMorph extension](https://github.com/SlicerMorph/SlicerMorph?tab=BSD-2-Clause-1-ov-file). See Tutorials, Acknowledgement, and license for more information.

---

## Detailed tutorials and Methods introduction:

## Video tutorials:
- Plate registration: [Tutorial 1: plate registration](https://youtu.be/GVo89_oOOGM?si=q0GWMU0vH_xGB2DE)
- Generate fit metrics: [Tutorial 2: generate fit metrics](https://www.youtube.com/watch?v=IyLVJwoHqCc&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=2)
- Compare fit of multiple plates: [Tutorial 3: compare plate fit](https://www.youtube.com/watch?v=P6sXtbH0i2w&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=3)
- Modify pre-registered plate position and combine multiple registration results for comparison: [Tutorial 4: edit pre-registered plate](https://www.youtube.com/watch?v=EaOGQawftLU&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=4)
- Fractured orbit reconstruction using the mirror of the contralateral side: [mirrorOrbitRecon tutorial](https://youtu.be/t951sCvk_lc?si=wHra2VXSp__asPQt)

## 🔄 Quick Tutorial: Try Plate Registration and fit comparison (may take 10-20 minutes depends on how you are familiar with Slicer)

Follow this simple walkthrough using the sample dataset included in the extension.

### 1. Install the Extension
Download and install the stable Slicer 5.10.0 at https://download.slicer.org/.

Open **Extension Manager** at the upper right corner. Search for 'SlicerOrbitSurgerySim', click, download, and restart Slicer.
Note that it will also install the **SlicerMorph** extension for you automatically, which is a dependency. If SlicerMorph is failed to install automatically, please manually install it.

<img src="Tutorials/img/quick_step01.png" width="300">

### 2. Load sample data
The tutorial uses open‑source segmented from the **CBCTDental Surgery** volume accessible at the Slicer Sample Data module.

Open Module Finder -> **Sample Data** module → click the sample data called **PlateRegistrationSampleDataFiles** to select a directory to download and unzip the folder.<br>
<img src="Tutorials/img/quick_step02.png" width="350"> <img src="Tutorials/img/quick_step03.png" width="250">

In the unzipped folder, select:
- skull_sample_left_fracture.ply
- left_orbit_lm.mrk.json
- synth_plate_large_left.py
- synth_plate_large_left_lm.mrk.json

Drag and drop them to Slicer. Click **OK**. You should see the data loaded in the 3D Window:<br>
<img src="Tutorials/img/quick_step04.png" width="300"> <img src="Tutorials/img/quick_step05.png" width="250">

In the **Sample Data** Module, click CT volume **CBCTDental Surgery** as the sample data is segmented from it.
- You should see that the PostDentalSurgery volume is automatically loaded and displayed in 2D slice views. 
- You can move the top ball or scroll the mouse to find the orbital region. To zoom in or out, hold and drag the right mouse button. To move slice position, hold and drag the mouse scroll button.

<img src="Tutorials/img/quick_step06.png" width="350"> <img src="Tutorials/img/quick_step07.png" width="300">

Optional: switch view to **Conventional** or **Conventional Widescreen** layout for better 2D & 3D view.<br>
<img src="Tutorials/img/quick_step08.png" width="250">

### 3. Switch to the plateRegistration module and select data

Open **Module Finder**, type **PlateRegistration** and click "OK" to switch to the module.<br>
<img src="Tutorials/img/quick_step09.png" width="400"> 

**If this is the first time loading the module, it will install the required Python packages. It may take a few minutes.**<br>
<img src="Tutorials/img/quick_step10.png" width="250">

In the **input** section of the **PlateRegistration** tab, select orbit and plate models and landmark files in the drop-down menu<br>
<img src="Tutorials/img/quick_step11.png" width="450">

### 4. Initial registration
In the **Initial Registration** section, click **initial registration**, then **Registration Posterior Stop**:<br>
<img src="Tutorials/img/quick_step12.png" width="450">

You should see the plate is roughly aligned to the orbit. <br>
<img src="Tutorials/img/quick_step13.png" width="350">

In the **Node viewer** box, you should also see a folder created to store the plate registration results, which will be saved later
The name format is **_plate_model_name_time_stamp_**. The time stamp shows when the folder is created to avoid duplicate names.<br>

<img src="Tutorials/img/quick_step14.png" width="400">

### 5. Manual Adjustment
In the **Plate interactive adjustment**, check the **Enable 3D interaction transform handle" check box.
If this is the first time, it will install required Python package:<br>
<img src="Tutorials/img/quick_step15.png" width="500"> <img src="Tutorials/img/quick_step16.png" width="300">

The interaction transformed handle will be created with the center of rotation at the posterior stop landmark, and a new subsampled plate model will be displayed in blue.
In both 3D and 2D slice views, drag the handle bars to rotate the plate. Drag the arrow or center of rotation to translate the plate position if necessary. <br>
<img src="Tutorials/img/quick_step17.png" width="500">

Click **Mark intersection** push button to detect plate-orbit intersection, which will be marked in both 3D (yellow line) and 2D (yellow dots) views. The percentage of intersection points will also be displayed in the information box.<br>
<img src="Tutorials/img/quick_step18.png" width="400"><br>
<img src="Tutorials/img/quick_step19.png" width="550"><br>

**Ideally, there should be no intersection between plate and orbit. However, the plate models were manually created (using the _Baffle Planner_ module from the _SlicerHeart_ extension) based on roughly tracing the contours of two different skulls.
Therefore, these plates were merely for demo purposes. Users can stop whenever they want with a suboptimal alignment and move on to the next steps.**


### 6. Save the data
Once done, click **Finalize Registration** to finalize registration. <br>
<img src="Tutorials/img/quick_step20.png" width="500"><br>

Select a root directory for saving plate registration results. In this case, a root folder `./Downloads/test_orbitSim` was created as the root folder to store registration and fit comparison results.
Click **Save current plate registration results** to save the plate registration results.<br>
<img src="Tutorials/img/quick_step21.png" width="500"><br>


### 7. Repeat steps 3-7 for another plate
Once the plate registration results are saved, drag the small plate and landmark files from the downloaded sample data folder into Slicer:
- synth_plate_small_left.ply
- synth_plate_small_left_lm.mrk<br>
<img src="Tutorials/img/quick_step22.png" width="500"><br>

Repeat step 3-7 for register the small plate and save results into the same directory (no change directory is needed for step 7). <br>

### 8. Fit metrics generation
Fit measurements are based on:<br>
(1) Computing vertex-to-vertex distances between a plate and reconstructed orbit using functions adapted from the Slicer _Model-to-Model_ Distance module <br>
(2) Distances between user-defined edge-specific curve points and their projected points on the reconstructed orbit.<br>
The sample data has provided four curves, each with seven evenly sampled points, for four plate edges.<br>

<img src="Tutorials/img/quick_step23.png" width="300"><br>

Simply copy-paste the two subfolders 'synth_plate_large_left' and 'synth_plate_small_left' from the ./plateRegistrationSampleData/plateMarginPtsForProj folder 
into the empty folder **points_for_projection** folder automatically created under the root folder you specified or created in **step 7**. <br>
<img src="Tutorials/img/quick_step24.png" width="700"><br>

In the sample data folder **plateRegistratIonSampleData**, also drag the **skull_sample_left_orbit_recon.py** into Slicer. This is the model with the left orbit reconstructed using the mirror of the contralateral. You can change color to better visualize it <br>

Go back to Slicer. Switch to the **Plate fit metrics** tab.<br>
<img src="Tutorials/img/quick_step24_2.png" width="500"><br>

If Slicer was not closed after **step 8**, you should see the **plate margin points root directory** entry now points to the **_your_root_folder/points_for_projection_** directory. If not, manually select that folder. <br>
In the **Repaired orbit model** drop-down menu, select the **skull_sample_left_orbit_recon.** model.<br>
<img src="Tutorials/img/quick_step25.png" width="700"><br>

Click **Compute distance map between the plate and the orbit** and **Project Points from each plate to the orbit** push buttons. Each step may take one to a few minutes.<br>
<img src="Tutorials/img/quick_step26.png" width="500"><br>

The heatmap models, heatmap distances, and point projection results are saved under `your_root_folder/fit_output/fit_metrics`.

(Optional) You can visualize plate-to-orbit heatmap and point projection results by selecting a plate folder under _your_root_folder/fit_output/fit_metrics_, and click the two visualization buttons. <br>
<img src="Tutorials/img/quick_step27.png" width="800"><br>
<img src="Tutorials/img/quick_step28.png" width="350"><br>

If previously loaded heatmap models and point projection results blocked the vision, you can hide them by clicking and closing the "eye" icon to turn off visualizations in the top "Node" box or simply right click and delete them. <br>
<img src="Tutorials/img/quick_step29.png" width="450"><br>

### 9. Fit Comparison
Switch to the **Compare fit** tab of the **PlateRegistration** module. <br>
<img src="Tutorials/img/quick_step30.png" width="450"><br>

If Slicer is not closed after Step 8:
- The **Compare distances between plate margins and orbits** checkbox should be checked.
- The directory combobox should point to `your_root_folder/fit_output/fit_metrics`.<br>
If run this step in a freshly opened Slicer, manually check the check box and select the `your_root_folder/fit_output/fit_metrics_` directory.<br>
<img src="Tutorials/img/quick_step31.png" width="600"><br>

Click **Compare fitness** push button, wait for one or a few minutes. You should see ranking output displayed:
- Rankings according the mean plate-edge-to-orbit distances, per edge distances, and mean heatmap distances
- A scatterplot shows the mean per edge distances of plates <br>
<img src="Tutorials/img/quick_step32.png" width="400"> <img src="Tutorials/img/quick_step33.png" width="350">

All ranking results, distances, and plots are saved under `your_root_folder/fit_output/compare_fit_comparison`

To visualize superimposition of registered plates with heatmap:
- Check the "Visualize existing results" checkbox.
- Click "Show superimposed plates with distance heatmap" to show registered plates with heatmap
- Click "show points on the margins" to show points on the plate margins. The colors match with the scatterplot colors.

<img src="Tutorials/img/quick_step34.png" width="500"> 
<img src="Tutorials/img/quick_step35.png" width="500">


---

## Acknowledgement

The **Interaction Transform Handle** is created by **Kyle Sunderland** (Perk Lab, Queens University), who has also provided many invaluable technical advice and support for this project. **Dr. Andras Lasso** (Perk Lab, Queens Univeristy) and **Dr. Steve Pieper** (Isomics, Inc.) and the Slicer Community have also provided valuable advice for this project.

**Dr. Andrew Read‑Fuller** (Texas A&M College of Dentistry) has provided invaluable clinical insights and advice for this project. **Braedon Gunn** (Texas A&M College of Dentistry) has meticulously segmented many fractured orbital bones that paved the road for this project and tested the extension on multiple patient scans.

The rigid registration (itk package) and affine registration functions depend on the functions originally developed for **ALPACA** and **FastModelAlign** modules of the [**SlicerMorph**](https://github.com/SlicerMorph) extension developed by **Dr. A. Murat Maga**'s lab.

The development is supported by the Seedling Grant from Texas A&M University Health Science Center awarded to Chi Zhang.
