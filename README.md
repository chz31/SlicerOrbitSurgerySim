# orbitSurgerySim — Orbit Surgery Simulation (3D Slicer Extension)

The **orbitSurgerySim** extension is used to interactively register and compare the fit of surgical plates (typically preformed plates) for repairing orbital fractures (usually caused by blunt force trauma). There are different types of plates with different contours and from different vendors. For how preformed and customzed plates are used for repairing orbital fractures, see this [introduction](https://surgeryreference.aofoundation.org/cmf/trauma/midface/orbit-floor/reconstruction).

---

## Modules
At this moment,this extension contains two modules:

1. **PlateRegistration**
   
   Users can interactively adjust plate positions and compare different types of preformed plates across vendors or different ways of plate placement of the same plate. Repeatable ways of plate fit metrics are generated for ranking the fit of plates or performing more detailed downstream analysis.

<img width="350" height="350" alt="Screenshot from 2025-08-26 13-05-46" src="https://github.com/user-attachments/assets/1f382ba1-8821-496f-a263-c1d9af1b3922" />

<sub>Figure 1 </sub><br><sub>The above picture shows a registered 3D model of a preformed plate placed at the fracture side using the plateRegistration module. </sub>


2. **mirrorOrbitalRecon**

   This module uses the mirrored model of the unfractured contralateral side to reconstruct the fractured orbit. A reconstructed orbit is highly recommended for generating plate fit metrics. The core functions are rigid and affine registration methods reused from the ALPACA/MALPACA and FastModelAlign modules of the [SlicerMorph extension](https://github.com/SlicerMorph/SlicerMorph?tab=BSD-2-Clause-1-ov-file). See Tutorials, Acknowledgement, and license for more information.

<img width="250" height="250" alt="image" src="https://github.com/user-attachments/assets/a3150e7f-6deb-4f57-a1f4-3c8b02db0efa" />
<img width="250" height="250" alt="image" src="https://github.com/user-attachments/assets/aa361c10-ab6f-4b5c-9df6-48a7ce752c45" />

<sub>Figure 2 </sub><br><sub>Left picture is a fractured orbit. Right picture is a reconstructed one using the mirror of the intact contralateral side.</sub>

---

## Sample Data

The tutorial below will use open‑source sample data. The sample data from the video tutorials are accessible via the **Sample Data** module of Slicer. The sample skull is segmented from the **post‑dental‑surgery CBCT** skull volume from the Slicer Sample Data module. Two synthetic plates from two different skulls are also created from the contours of two different skulls using the **Baffle Planner** tool of the [SlicerHeart extension](https://github.com/SlicerHeart/SlicerHeart)

<img width="300" height="300" alt="Screenshot from 2025-08-14 12-43-18" src="https://github.com/user-attachments/assets/5783fbea-25d2-4f3a-9a03-b665746639b5" />
<sub>Figure 3 </sub><br><sub>Sample data for plate registration. </sub>

---

## Tutorial *(More detailed tutorial will be provided soon)*

### PlateRegistration module tutorial

#### 1. Plate registration

Plate registration requires placing plates at the surface of the intact peripheral bone of the fracture site. Conventional registration typically produced overlapping between models. This would impact accuracy of virtual planning and fit evaluation. The PlateRegistration module utilized the new Slicer tool, **Interaction Transform Handle**, and utility tools (e.g., instant intersection markers, collision detection and markers, align posterior stop) to facilitate users to **interactively** adjust plate position until resting just above the peripheral bone.

This video contains detailed instructions and captions about how different plates can be registered and saved for fit comparison.

Video tutorial: [Orbital Surgery Plate Model Registration and Fit Comparison Tutorial 1: plate registration](https://youtu.be/GVo89_oOOGM?si=q0GWMU0vH_xGB2DE)

[![Tutorial 1: plate registration](https://img.youtube.com/vi/GVo89_oOOGM/hqdefault.jpg)](https://youtu.be/GVo89_oOOGM?si=q0GWMU0vH_xGB2DE)


#### 2. Generating fit metrics

The second tab of PlateRegistration is for generating fit metrics. It is highly recommended to first reconstruct the fractured orbit using the mirror image of the intact side. See mirrorOrbitalRecon tutorial below for more detail.

Here is a detailed video tutorial:
[Orbital Surgery Plate Model Registration and Fit Comparison Tutorial 2: generate fit metrics](https://www.youtube.com/watch?v=IyLVJwoHqCc&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=2)

[![Tutorial 2: generate fit metrics](https://img.youtube.com/vi/IyLVJwoHqCc/hqdefault.jpg)](https://www.youtube.com/watch?v=IyLVJwoHqCc&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=2)

**Fit metrics contain two types of data:**

- First, it computes distances from the plate surface to the orbit. This is done by using the **ray‑casting** method (same as in the ModelToModelDistance module in Slicer). For this region, a reconstructed orbital model is highly recommended. The fractured orbit is usually very difficult to segment and will have large holes. The distances are stored as scalar values in each vertex of the plate model and can be visualized as a **heatmap** on the plate model (see tutorial video above).

- Second, it projects user‑defined plate curve points onto the orbit (reconstructed orbit highly recommended) and measures distances between selected plate margins and the orbit. Points on the plate margins and their orbital projections can be conveniently visualized using the PlateRegistration module (see tutorial video above).

<img width="350" height="350" alt="image" src="https://github.com/user-attachments/assets/5aaed092-dfa7-454a-bfe8-00ffa1130b37" />

<sub>Figure 4 </sub><br><sub>Points projection from margins the synthetic plate (Sample data) to the reconstructed orbit. </sub>

The curve points can be conveniently placed using Slicer’s generic **Markups** module. For the synthetic plate from the sample data, four curves are placed along margins or other user-defined area:

The curve points can be conveniently placed using Slicer generic Markup module. For the synthetic plate from the sample data, four curves are placed along the peripehral are placed:

<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/1f1cb61c-3fa5-445d-b5c0-10e45d71e019" />

<sub>Figure 5 </sub><br><sub>Four fiducial curves are placed on the four margins of the synthetic plate. </sub>

For the model of a vendor-provided plate, an adiditonal curve is placed along the junction of the medial wall and floor parts of the plate

<img width="300" height="300" alt="Screenshot from 2025-08-26 13-27-34" src="https://github.com/user-attachments/assets/b609423c-5682-47dc-890d-6572862f58d9" />

<sub>Figure 5 </sub><br><sub>Five fiducial curves are placed on four margins of a preformed meshed plates </sub>

Users can placed their own curves and alter the density of points along each curve. Please make sure the number of curves and point density of each curve are consistent across all plates for comparison.


#### 3. Compare fit

Here is a detailed video tutorial for how plate fit can be compared:

Video tutorial: [Orbital Surgery Plate Model Registration and Fit Comparison Tutorial 3: compare plate fit](https://www.youtube.com/watch?v=P6sXtbH0i2w&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=3
)

[![Tutorial 3: compare plate fit](https://img.youtube.com/vi/P6sXtbH0i2w/hqdefault.jpg)](https://www.youtube.com/watch?v=P6sXtbH0i2w&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=3)


**Fit is compared and ranked by:**

1) Mean overall plate‑orbit distances, which is the mean scalar values (saved as CSV as well) of each plate, measured in mm.

2) The overall mean distance between points on plate margins and their projections on the orbit.

3) Separate ranking of each plate margin based on mean distances from the points along this margin to their projections on the orbit.

All of these data are stored in CSV files and plotted as scatterplots as well (see tutorial above) in:

`/plate/registration/roots/fit_output/compare_fit_output`

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/8b1cd59a-17be-4fcd-9b84-b0d223a1e260" />
<sub>Figure 6 </sub><br><sub>the compare fit output folder's content </sub>

Below is a sample plot shows the mean distance between points on each plate margin to the orbit from five registered plates represented five plate placement attempts: three using the same large plate, and two using the small plate with a different contour. The accompanied csv shows the actual mean distances as well as the overall mean
<img width="3000" height="1500" alt="Mean margin-orbit distances" src="https://github.com/user-attachments/assets/3cfc2d3d-f9d4-49f3-abbd-21c62feed259" />
<img width="2133" height="236" alt="image" src="https://github.com/user-attachments/assets/be11ad78-0d33-4299-b251-8976671e64be" />

This graph and csv shows the distance of all points from one plate margin to their orbital projections across five registered plates. This can facilitate analyze which local regions fit well or not well across different registered plates.
<img width="3000" height="1500" alt="anterior_floor_point_dists_to_orbit" src="https://github.com/user-attachments/assets/01865398-2296-4e93-861e-b28f2d95cd06" />
<img width="2678" height="231" alt="image" src="https://github.com/user-attachments/assets/d668d3a3-7cb8-4925-9992-08d0e9d16d63" />


Distance map (heatmap) scalar values of each plate are stored in the csv file in plate/registration/roots/fit_output/fit_metrics/plate_folder. The models with scalar values in the vtk format are also saved and can be conveniently retrieved using 

A histogram is also provided to visualize distance ranges of all points of the plate model to the orbit.

4. Facilitate collaborative planning.
Users can also use this tool to retrieve existing registered plates and adjust plate positions. This can facilitate collaborative planning and education. This video tutorial shows how to further editing a preregistered plate.
(Insert video here: https://www.youtube.com/watch?v=EaOGQawftLU&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=4)


mirrorOrbitRecon module tutorial (will come soon).

Acknowledgement
The interaction transform handle is created by Kyle Sunderland, who has also provided many invaluable technical advice and support for this project. Andras Lasso and Steve Pieper has also provided valuable advice for this project.

Dr. Andrew Read-Fuller has provided invaluable clinical insights and advice for this project.

The rigid registration method is from an itk package originally created for the ALPACA module of the SlicerMorph extension developed by Dr. A. Murat Maga's lab. A copy of the license of SlicerMorph extension is provided. The affine deformable registration method is from the  library and is also used in the FastModelALign module of the SlicerMorph extension.

The development is supported by the Seedling Grant from Texas A&M Health Science Center awarded to Chi Zhang.
