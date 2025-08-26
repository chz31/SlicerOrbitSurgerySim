The orbitSurgeySim module is used for interactively registered and compare the fit of plates (typically preformed plates) for orbital fracture repair. 

At this moment,this extension contains two modules:

1. PlateRegistration module: Users can interactively adjust plate positions and compare different types of preformed plates across vendors or different ways of plate placement of the same plate. Repeatable ways of plate fit metrics are generated for ranking the fit of plates or perform more detailed downstream analysis.
<img width="1548" height="1455" alt="Screenshot from 2025-08-26 13-05-46" src="https://github.com/user-attachments/assets/1f382ba1-8821-496f-a263-c1d9af1b3922" />
The above picture illustrates registering 3D model of a vendor-provided plate at the fracture side using the plateRegistration module.

3. mirrorOrbitalRecon module: this module uses the mirror model of the unfractured contralateral side to reconstruct orbit. A reconstructed orbit is highly recommended for generating plate fit metrics. The core functions are rigid and affine registration methods reused from the ALPCACA/MALPACA and FastModelAlign modules of the SlicerMorph extension: https://github.com/SlicerMorph/SlicerMorph?tab=BSD-2-Clause-1-ov-file. See tutorials, Acknowledgement, and license for more information.

The tuturial below will only use open-source sample data. The sample data from the video tutorials are accessible via the Sample Data module of Slicer.The sample skull is segmented from the post dental surgery CBCT skull volume from the Slicer Sample Data module. Two synthetic plates from two different skulls are also created from the contours of two different skulls using the Baffle Planner tool of the SlicerHeart extension:  https://github.com/SlicerHeart/SlicerHeart

Tutorial (More detailed tutorial will provided soon)

plateRegistration module tutorial.
1. Plate registration.
Plate registration requires placing plates at the surface of the intact peripheral bone of the fracture site. Conventional registration typically produced overlapping between models. This would impact accuracy of virtual planning and fit evaluation. The plateRegistration module utilized the new Slicer tool, Interaction Transform Handle, and utility tools, (e.g., instant intersection markers, collision detection and markers, align posterior stop) to facilitate users to interacytively adjust plate position util resting just above the peripheral bone.

This video contains detailed instructions and captions about how different plates can be registered and saved for fit comparison.
(Insert video here: https://youtu.be/GVo89_oOOGM?si=q0GWMU0vH_xGB2DE)

Users can also use this tool to retrieve existing registered plates and adjust plate positions. This can facilitate collaborative planning and education. This video tutorial shows how to further editing a preregistered plate.
(Insert video here: https://www.youtube.com/watch?v=EaOGQawftLU&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=4)

2. Generating fit metrics
The second tab of plate registration is for generating fit metrics. It is highly recommended to first reconstructing the fractured orbit using the mirror image of the intact side. See mirrorOrbitRecon tutorial below for more detail.

Here is a detailed video tutorial:
Insert video here: https://www.youtube.com/watch?v=IyLVJwoHqCc&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=2

Fit metrics contains two types of data:
First, it computes distances from the plate surface to the orbit. This is done by using the ray casting method (same as in the ModelToModel Distance module in Slicer). For this region, reconstructed orbital model is highly recommended. The fractured orbit is usually very difficult to segment and will have large holes. The distances are stored as scalar values in each vertex of the plate model and can be visualized as heatmap.
Second, it projects user-defined plate curve points onto the orbit (reconstructed orbit highly recommended) and measure distances between selected plate margins to the orbit. The curve points can be conveniently placed using Slicer generic Markup module.

For the synthetic plate from the sample data, four curves are placed along the peripehral are placed.

Users can placed their own curves, such as adding one more curve along the junction of the medial wall and floor parts of the plate, and alter the density of points along each curve. Please make sure the number of curves and point density of each curve are consistent across all plates for comparison.


3. Compare fit is done by comparing the mean edges.
Here is a detailed video tutorial: https://www.youtube.com/watch?v=P6sXtbH0i2w&list=PLvFNLt1ZOjPL5FHAWSB3U7QnUEgU7rQY-&index=3

Fit are compared and ranked by:
1) Mean overall plate-orbit distances, which is the mean scalar values (saved as csv as well) of each plate, measured in mm.
2) The overall mean distance between points on plate margins and their projections on the orbit.
3) Separate ranking of each plate margin based on mean distances from the points along this margin to their projections on the orbit.

All of these data are stored in csv files and plotted as scatterplots as well (see tutorial above) in /plate/registration/roots/fit_output/compare_fit_output
<img width="1347" height="679" alt="image" src="https://github.com/user-attachments/assets/8b1cd59a-17be-4fcd-9b84-b0d223a1e260" />
Below is a sample plot shows the mean distance of each plate margin to the orbit from five plate registration attempts: three using the same large plate, and two using the small plate with a different contour. The accompanied csv shows the actual mean distances.
<img width="3000" height="1500" alt="Mean margin-orbit distances" src="https://github.com/user-attachments/assets/3cfc2d3d-f9d4-49f3-abbd-21c62feed259" />
<img width="2133" height="236" alt="image" src="https://github.com/user-attachments/assets/be11ad78-0d33-4299-b251-8976671e64be" />


Distance map (heatmap) scalar values of each plate are stored in the csv file in plate/registration/roots/fit_output/fit_metrics/plate_folder.

A histogram is also provided to visualize distance ranges of all points of the plate model to the orbit.

4. Facilitate collaborative planning.
The module can 

mirrorOrbitRecon module tutorial.

Acknowledgement
The interaction transform handle is created by Kyle Sunderland, who has also provided many invaluable technical advice and support for this project. Andras Lasso and Steve Pieper has also provided valuable advice for this project.

Dr. Andrew Read-Fuller has provided invaluable clinical insights and advice for this project.

The rigid registration method is from an itk package originally created for the ALPACA module of the SlicerMorph extension developed by Dr. A. Murat Maga's lab. A copy of the license of SlicerMorph extension is provided. The affine deformable registration method is from the  library and is also used in the FastModelALign module of the SlicerMorph extension.

The development is supported by the Seedling Grant from Texas A&M Health Science Center awarded to Chi Zhang.
