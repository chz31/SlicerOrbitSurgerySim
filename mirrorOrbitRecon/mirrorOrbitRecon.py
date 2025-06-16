import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# mirrorOrbitRecon
#


class mirrorOrbitRecon(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("mirrorOrbitRecon")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#mirrorOrbitRecon">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

#
# mirrorOrbitReconParameterNode
#


@parameterNodeWrapper
class mirrorOrbitReconParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# mirrorOrbitReconWidget
#


class mirrorOrbitReconWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/mirrorOrbitRecon.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = mirrorOrbitReconLogic()

        # Connections

        #Input connections
        self.ui.originalModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.ui.originalModelSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.planeLmSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.ui.planeLmSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.mirroredModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.ui.mirroredModelSelector.setMRMLScene(slicer.mrmlScene)

        # Create a plane
        self.ui.createPlaneButton.connect("clicked(bool)", self.onCreatePlaneButton)

        # Enable interactive handle for the plane
        self.ui.planeAdjustCheckBox.connect("toggled(bool)", self.onPlaneAdjustCheckBox)

        # Mirror the skull
        self.ui.createMirrorPushButton.connect("clicked(bool)", self.onCreateMirrorPushButton)

        # Rigid registration
        self.ui.skullRigidRegistrationPushButton.connect("clicked(bool)", self.onSkullRigidRegistrationPushButton)
        self.ui.showRigidModelCheckbox.connect("clicked(bool)", self.onShowRigidModelCheckbox)

        # Affine registration"toggled(bool)"
        self.ui.skullAffineRegistrationPushButton.connect("clicked(bool)", self.onSkullAffineRegistrationPushButton)
        self.ui.showAffineModelCheckbox.connect("toggled(bool)", self.onShowAffineModelCheckbox)

        # Perform a plane cut
        self.ui.planeCutPushButton.connect("clicked(bool)", self.onPlaneCutPushButton)

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)



    def onSelect(self):
        #Enable initialRegistration push button
        # self.ui.initialRegistrationPushButton.enabled = bool(self.ui.inputOrbitModelSelector.currentNode() and self.ui.inputOrbitModelSelector.currentNode()
        #     and self.ui.plateModelSelector.currentNode() and self.ui.plateFiducialSelector.currentNode())
        #enable createMirrorPushButton
        self.ui.createPlaneButton.enabled = bool(self.ui.originalModelSelector.currentNode() and self.ui.planeLmSelector.currentNode() and self.ui.mirroredModelSelector.currentNode())

    def onCreatePlaneButton(self):
        #Get three landmarks from the
        self.planeLmNode = self.ui.planeLmSelector.currentNode()
        # self.mirrorPlaneNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", 'mirrorPlane')
        p1 = [0.0, 0.0, 0.0]
        p2 = [0.0, 0.0, 0.0]
        p3 = [0.0, 0.0, 0.0]
        self.planeLmNode.GetNthControlPointPositionWorld(0, p1)
        self.planeLmNode.GetNthControlPointPositionWorld(1, p2)
        self.planeLmNode.GetNthControlPointPositionWorld(2, p3)
        self.mirrorPlaneNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsPlaneNode", "mirrorPlane")
        self.mirrorPlaneNode.CreateDefaultDisplayNodes()
        self.mirrorPlaneNode.GetDisplayNode().SetVisibility(True)
        self.mirrorPlaneNode.SetPlaneType(slicer.vtkMRMLMarkupsPlaneNode.PlaneType3Points)
        self.mirrorPlaneNode.AddControlPointWorld(p1)
        self.mirrorPlaneNode.AddControlPointWorld(p2)
        self.mirrorPlaneNode.AddControlPointWorld(p3)
        self.ui.planeAdjustCheckBox.enabled=True
        self.ui.createMirrorPushButton.enabled=True

    def onPlaneAdjustCheckBox(self):
        # self.planeInteractionTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode',
        #                                                                    "interaction_transform")
        # self.planeInteractionTransformNode.CreateDefaultDisplayNodes()
        # self.planeInteractionTransformNode.GetDisplayNode().SetEditorVisibility(True)
        if self.ui.planeAdjustCheckBox.isChecked():
            displayNode = self.mirrorPlaneNode.GetDisplayNode()
            displayNode.SetHandlesInteractive(True)
            displayNode.SetRotationHandleVisibility(True)

    def onCreateMirrorPushButton(self):
        self.originalSkullModelNode = self.ui.originalModelSelector.currentNode()
        self.mirroredSkullModelNode = self.ui.mirroredModelSelector.currentNode()
        mirrorFunction = slicer.vtkSlicerDynamicModelerMirrorTool()
        dynamicModelerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLDynamicModelerNode")
        dynamicModelerNode.SetToolName("Mirror")
        dynamicModelerNode.SetNodeReferenceID("Mirror.InputModel", self.originalSkullModelNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("Mirror.InputPlane", self.mirrorPlaneNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("Mirror.OutputModel", self.mirroredSkullModelNode.GetID())
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
        # self.mirroredSkullModelNode.SetName(self.originalSkullModelNode.GetName() + "_mirror")
        # self.ui.createMirrorPushButton.enabled=False
        self.ui.skullRigidRegistrationPushButton.enabled = True

    def onSkullRigidRegistrationPushButton(self):
        #rigid registration
        self.parameterDictionary = {
            "pointDensity": 1.00,
            "normalSearchRadius": 2.00,
            "FPFHNeighbors": int(100),
            "FPFHSearchRadius": 5.00,
            "distanceThreshold": 3.00,
            "maxRANSAC": int(1000000),
            "ICPDistanceThreshold": float(1.50)
        }
        #Clone the mirrored model
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self.mirroredSkullModelNode)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        self.mirroredSkullRigidNode = shNode.GetItemDataNode(clonedItemID)
        self.mirroredSkullRigidNode.SetName(self.mirroredSkullModelNode.GetName() + "_rigid")

        #Perfrom itk rigid registration
        logic = mirrorOrbitReconLogic()
        self.sourcePoints, self.targetPoints, scalingTransformNode, ICPTransformNode = logic.ITKRegistration(self.mirroredSkullRigidNode,
                                                                                                   self.originalSkullModelNode,
                                                                                                   scalingOption=False,
                                                                                                   parameterDictionary=self.parameterDictionary,
                                                                                                   usePoisson=False)
        self.mirroredSkullModelNode.GetDisplayNode().SetVisibility(False)
        self.mirrorPlaneNode.GetDisplayNode().SetVisibility(False)
        self.ui.createMirrorPushButton.enabled=False
        self.ui.skullRigidRegistrationPushButton.enabled = False
        self.ui.showRigidModelCheckbox.enabled = True
        self.ui.showRigidModelCheckbox.checked = 1
        self.ui.skullAffineRegistrationPushButton.enabled = True
        self.ui.planeCutPushButton.enabled = True

    def onSkullAffineRegistrationPushButton(self):
        #Clone the rigid registered model again for affine
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self.mirroredSkullRigidNode)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        self.mirroredSkullAffineNode = shNode.GetItemDataNode(clonedItemID)
        self.mirroredSkullAffineNode.SetName(self.mirroredSkullModelNode.GetName() + "_affine")
        self.mirroredSkullAffineNode.GetDisplayNode().SetColor([0, 0, 255]) #blue
        #Affine deformable registration
        logic = mirrorOrbitReconLogic()
        transformation, translation = logic.CPDAffineTransform(self.mirroredSkullAffineNode, self.sourcePoints, self.targetPoints)
        matrix_vtk = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                matrix_vtk.SetElement(i, j, transformation[j][i])
        for i in range(3):
            matrix_vtk.SetElement(i, 3, translation[i])
        affineTransform = vtk.vtkTransform()
        affineTransform.SetMatrix(matrix_vtk)
        affineTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "Affine_transform_matrix")
        affineTransformNode.SetAndObserveTransformToParent(affineTransform)
        affineNodeName = self.originalSkullModelNode.GetName() + "_affine"
        affineTransformNode.SetName(affineNodeName)
        # self.mirroredSkullRigidNode.GetDisplayNode().SetVisibility(False)
        self.ui.showRigidModelCheckbox.checked = 0
        self.ui.showAffineModelCheckbox.enabled = True
        self.ui.showAffineModelCheckbox.checked = 1
        self.ui.skullAffineRegistrationPushButton.enabled = False


    def onShowRigidModelCheckbox(self):
        try:
            if self.ui.showRigidModelCheckbox.isChecked():
                self.mirroredSkullRigidNode.GetDisplayNode().SetVisibility(True)
            else:
                self.mirroredSkullRigidNode.GetDisplayNode().SetVisibility(False)
        except:
            pass

    def onShowAffineModelCheckbox(self):
        try:
            if self.ui.showAffineModelCheckbox.isChecked():
                self.mirroredSkullAffineNode.GetDisplayNode().SetVisibility(True)
            else:
                self.mirroredSkullAffineNode.GetDisplayNode().SetVisibility(False)
        except:
            pass


    def onPlaneCutPushButton(self):
        planeCutFunction = slicer.vtkSlicerDynamicModelerPlaneCutTool()
        dynamicModelerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLDynamicModelerNode")
        dynamicModelerNode.SetToolName("Plane Cut")
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputModel", self.mirroredSkullRigidNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputPlane", self.mirrorPlaneNode.GetID())
        self.positiveHalfModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "positive_half_skull")
        self.negativeHalfModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "negative_half_skull")
        dynamicModelerNode.SetNodeReferenceID("ROICut.OutputPositiveModel", self.self.positiveHalfModelNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("ROICut.OutputNegativeModel", self.self.negativeHalfModelNode.GetID())
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)




    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        # if self._parameterNode:
        #     self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
        #     self._parameterNodeGuiTag = None
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        # self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        # if self.parent.isEntered:
        #     self.initializeParameterNode()



#
# mirrorOrbitReconLogic
#


class mirrorOrbitReconLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return mirrorOrbitReconParameterNode(super().getParameterNode())

    def ITKRegistration(self, sourceModelNode, targetModelNode, scalingOption, parameterDictionary, usePoisson):
        import ALPACA
        #Pull functions from ALPACA in SlicerMorph: https://github.com/SlicerMorph/SlicerMorph/tree/master/ALPACA
        logic = ALPACA.ALPACALogic()
        (
            sourcePoints,
            targetPoints,
            sourceFeatures,
            targetFeatures,
            voxelSize,
            scaling,
        ) = logic.runSubsample(
            sourceModelNode,
            targetModelNode,
            scalingOption,
            parameterDictionary,
            usePoisson,
        )

        #Scaling transform
        print("scaling factor for the source is: " + str(scaling))
        scalingMatrix_vtk = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                scalingMatrix_vtk.SetElement(i,j,0)
        for i in range(3):
            scalingMatrix_vtk.SetElement(i, i, scaling)
        scalingTransform = vtk.vtkTransform()
        scalingTransform.SetMatrix(scalingMatrix_vtk)
        scalingTransformNode =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "scaling_transform_matrix")
        scalingTransformNode.SetAndObserveTransformToParent(scalingTransform)


        ICPTransform_similarity, similarityFlag = logic.estimateTransform(
            sourcePoints,
            targetPoints,
            sourceFeatures,
            targetFeatures,
            voxelSize,
            scalingOption,
            parameterDictionary,
        )


        vtkSimilarityTransform = logic.itkToVTKTransform(
            ICPTransform_similarity, similarityFlag
        )

        ICPTransformNode = logic.convertMatrixToTransformNode(
            vtkSimilarityTransform, ("Rigid Transformation Matrix")
        )
        sourceModelNode.SetAndObserveTransformNodeID(ICPTransformNode.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(sourceModelNode)
        sourceModelNode.GetDisplayNode().SetVisibility(True)
        red = [1, 0, 0]
        sourceModelNode.GetDisplayNode().SetColor(red)
        targetModelNode.GetDisplayNode().SetVisibility(True)

        sourcePoints = logic.transform_numpy_points(sourcePoints, ICPTransform_similarity)


        #Put scaling transform under ICP transform = rigid transform after scaling
        scalingTransformNode.SetAndObserveTransformNodeID(ICPTransformNode.GetID())

        return sourcePoints, targetPoints, scalingTransformNode, ICPTransformNode


    def CPDAffineTransform(self, sourceModelNode, sourcePoints, targetPoints):
       from cpdalp import AffineRegistration
       import vtk.util.numpy_support as nps

       polyData = sourceModelNode.GetPolyData()
       points = polyData.GetPoints()
       numpyModel = nps.vtk_to_numpy(points.GetData())

       reg = AffineRegistration(**{'X': targetPoints, 'Y': sourcePoints, 'low_rank':True})
       reg.register()
       TY = reg.transform_point_cloud(numpyModel)
       vtkArray = nps.numpy_to_vtk(TY)
       points.SetData(vtkArray)
       polyData.Modified()

       affine_matrix, translation = reg.get_registration_parameters()

       return affine_matrix, translation


#
# mirrorOrbitReconTest
#


class mirrorOrbitReconTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_mirrorOrbitRecon1()

    def test_mirrorOrbitRecon1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("mirrorOrbitRecon1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = mirrorOrbitReconLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
