The orbitSurgeySim module is used for interactively registered and compare the fit of plates (typically preformed plates) for orbital fracture repair. At this moment, it contains two modules:

1. PlateRegistration module: Users can interactively adjust plate positions and compare different types of preformed plates across vendors or different ways of plate placement of the same plate. Repeatable ways of plate fit metrics are generated for ranking the fit of plates or perform more detailed downstream analysis.

2. mirrorOrbitalRecon module: this module uses the mirror model of the unfractured contralateral side to reconstruct orbit. A reconstructed orbit is highly recommended for generating plate fit metrics. The core functions are rigid and affine registration methods reused from the ALPCACA/MALPACA and FastModelAlign modules of the SlicerMorph extension: https://github.com/SlicerMorph/SlicerMorph?tab=BSD-2-Clause-1-ov-file. See tutorials, Acknowledgement, and license for more information.

The sample data from the video tutorials are accessible via the Sample Data module of Slicer.The sample skull is segmented from the post dental surgery CBCT skull volume from the Slicer Sample Data module. Two synthetic plates from two different skulls are also created from the contours of two different skulls using the Baffle Planner tool of the SlicerHeart extension:  https://github.com/SlicerHeart/SlicerHeart

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
Fit metrics contains two types of data. First, it computes distances between each point of the plate model and the orbital model using the ray casting method (same as in the ModelToModel Distance module in Slicer). For this region, reconstructed orbital model is highly recommended. The fractured orbit is usually very difficult to segment and will have large holes. The distances are stored as scalar values in each vertex of the plate model and can be visualized as heatmap.

Second, it projects user-defined plate curve points onto the orbit (reconstructed orbit highly recommended) and measure distances between selected plate margins to the orbit. The curve points can be conveniently placed using Slicer generic Markup module.

For the below commercial plate, five curves are placed along five margins.

For the below synthetic plate from the sample data, four curves are placed along the peripehral are placed.

Users can placed their own curves and alter the density of points along each curve. Please make sure the number of curves and curve densities are consistent across plates for comparison.

Users can also visualize point projection and heatamp for each individual plate.

3. Compare fit is done by comparing the mean edges.
  

5. Facilitate collaborative planning.

mirrorOrbitRecon module tutorial.

Acknowledgement
The interaction transform handle is created by Kyle Sunderland, who has also provided many invaluable technical advice and support for this project. Andras Lasso and Steve Pieper has also provided valuable advice for this project.

Dr. Andrew Read-Fuller has provided invaluable clinical insights and advice for this project.

The rigid registration method is from an itk package originally created for the ALPACA module of the SlicerMorph extension developed by Dr. A. Murat Maga's lab. A copy of the license of SlicerMorph extension is provided. The affine deformable registration method is from the  library and is also used in the FastModelALign module of the SlicerMorph extension.

The development is supported by the Seedling Grant from Texas A&M Health Science Center awarded to Chi Zhang.
