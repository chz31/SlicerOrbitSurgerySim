import logging
import os
from typing import Annotated, Optional

import vtk

import numpy as np
import copy
import math

import qt

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
# MirrorOrbitRecon
#


class MirrorOrbitRecon(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("MirrorOrbitRecon")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Chi Zhang (Texas A&M College of Dentistry)"]
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#mirrorOrbitRecon">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
In addition to Slicer base functions, the module reused itk functions for rigid registration from the ALPACA and FastModelAlign Modules of SlicerMorph extension (https://slicermorph.github.io/).
""")
        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # plateRegistration1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="fractureOrbitMirrorReconstruction",
        sampleName="orbitMirrorReconSampleData",
        thumbnailFileName=os.path.join(iconsPath, "MirrorOrbitReconSampleData.png"),
        uris="https://github.com/chz31/orbitSurgeySim_sampleData/raw/refs/heads/main/orbiMirrorReconSampleData.zip",
        loadFiles=False,
        fileNames="orbiMirrorReconSampleData.zip",
        loadFileType='ZipFile',
        checksums=None,
        customDownloader=downloadSampleDataInFolder,
    )

def downloadSampleDataInFolder(source):
    sampleDataLogic = slicer.modules.sampledata.widgetRepresentation().self().logic
    # Retrieve directory
    category = "fractureOrbitMirrorReconstruction"
    savedDirectory = slicer.app.userSettings().value(
          "SampleData/Last%sDownloadDirectory" % category,
          qt.QStandardPaths.writableLocation(qt.QStandardPaths.DocumentsLocation))

    destFolderPath = str(qt.QFileDialog.getExistingDirectory(slicer.util.mainWindow(), 'Destination Folder', savedDirectory))
    if not os.path.isdir(destFolderPath):
      return
    print('Selected data folder: %s' % destFolderPath)
    for uri, fileName, checksum  in zip(source.uris, source.fileNames, source.checksums):
      sampleDataLogic.downloadFile(uri, destFolderPath, fileName, checksum)

    # Save directory
    slicer.app.userSettings().setValue("SampleData/Last%sDownloadDirectory" % category, destFolderPath)
    filepath=destFolderPath+"/setup.py"
    if (os.path.exists(filepath)):
      spec = importlib.util.spec_from_file_location("setup",filepath)
      setup = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(setup)
      setup.setup()


#
# MirrorOrbitReconParameterNode
#


@parameterNodeWrapper
class MirrorOrbitReconParameterNode:
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
# MirrorOrbitReconWidget
#


class MirrorOrbitReconWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/MirrorOrbitRecon.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        #install itk rigid registration and pycpd packages
        needInstall = False
        try:
            from itk import Fpfh
            import cpdalp
        except ModuleNotFoundError:
            needInstall = True

        if needInstall:
            progressDialog = slicer.util.createProgressDialog(
                windowTitle="Installing...",
                labelText="Installing Python dependencies. This may take a minute...",
                maximum=0,
            )
            slicer.app.processEvents()
            try:
                slicer.util.pip_install(["itk~=5.4.0"])
                slicer.util.pip_install(["scikit-learn"])
                slicer.util.pip_install(["itk-fpfh~=0.2.0"])
                slicer.util.pip_install(["itk-ransac~=0.2.1"])
                slicer.util.pip_install(f"cpdalp")
            except:
                slicer.util.infoDisplay("Issue while installing the ITK Python packages")
                progressDialog.close()
            import itk

            fpfh = itk.Fpfh.PointFeature.MF3MF3.New()
            progressDialog.close()

        try:
            import cpdalp
            import itk
            from itk import Fpfh
            from itk import Ransac
        except ModuleNotFoundError as e:
            print("Module Not found. Please restart Slicer to load packages.")


        progressDialog = slicer.util.createProgressDialog(
            windowTitle="Importing...",
            labelText="Importing Python packages. This may take few seconds...",
            maximum=0,
        )
        slicer.app.processEvents()
        with slicer.util.WaitCursor():
            fpfh = itk.Fpfh.PointFeature.MF3MF3.New()
        progressDialog.close()

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = MirrorOrbitReconLogic()

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
        self.ui.showRigidModelCheckbox.connect("toggled(bool)", self.onShowRigidModelCheckbox)

        # Affine registration"
        self.ui.skullAffineRegistrationPushButton.connect("clicked(bool)", self.onSkullAffineRegistrationPushButton)
        self.ui.showAffineModelCheckbox.connect("toggled(bool)", self.onShowAffineModelCheckbox)

        # Perform a plane cut
        self.ui.planeCutPushButton.connect("clicked(bool)", self.onPlaneCutPushButton)

        # Select which side to keep
        self.ui.keepHalfPushButton.connect("clicked(bool)", self.onKeepHalfPushButton)

        # Rigid registration of a half model
        self.ui.rigidMirroredHalfButton.connect("clicked(bool)", self.onRigidMirroredHalfButton)
        self.ui.showRigidHalfModelCheckBox.connect("toggled(bool)", self.onShowRigidHalfModelCheckBox)

        # Affine registration of a half model
        self.ui.affineMirroredHalfButton.connect("clicked(bool)", self.onAffineMirroredHalfButton)
        self.ui.showAffineHalfModelCheckbox.connect("toggled(bool)", self.onShowAffineHalfModelCheckbox)

        # Reset
        self.ui.resetPushButton.connect("clicked(bool)", self.onResetPushButton)

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
        self.mirroredSkullModelNode.GetDisplayNode().SetVisibility(True)
        self.ui.skullRigidRegistrationPushButton.enabled = True
        self.ui.resetPushButton.enabled = True

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
        logic = MirrorOrbitReconLogic()
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
        self.mirroredSkullAffineNode.GetDisplayNode().SetColor(0, 1, 0) #blue
        # self.mirroredSkullAffineNode.GetDisplayNode().SetShading(True)
        #Affine deformable registration
        logic = MirrorOrbitReconLogic()
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
        dynamicModelerNode.SetToolName("Plane cut")
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputModel", self.mirroredSkullRigidNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputPlane", self.mirrorPlaneNode.GetID())
        self.positiveHalfModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "positive_half_mirror")
        self.negativeHalfModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "negative_half_mirror")
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.OutputPositiveModel", self.positiveHalfModelNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.OutputNegativeModel", self.negativeHalfModelNode.GetID())
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
        self.positiveHalfModelNode.GetDisplayNode().SetVisibility(True)
        self.positiveHalfModelNode.GetDisplayNode().SetColor(0.5, 0, 0)
        # self.positiveHalfModelNode.GetDisplayNode().SetShading(True)
        self.negativeHalfModelNode.GetDisplayNode().SetVisibility(True)
        self.negativeHalfModelNode.GetDisplayNode().SetColor(0, 0, 0.5)
        # self.negativeHalfModelNode.GetDisplayNode().SetShading(True)
        #
        #Also cut the skull model in half
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputModel", self.originalSkullModelNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.InputPlane", self.mirrorPlaneNode.GetID())
        self.positiveHalfOriginalModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "positive_half_original")
        self.negativeHalfOriginalModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "negative_half_original")
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.OutputPositiveModel", self.positiveHalfOriginalModel.GetID())
        dynamicModelerNode.SetNodeReferenceID("PlaneCut.OutputNegativeModel", self.negativeHalfOriginalModel.GetID())
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
        # self.positiveHalfOriginalModel.CreateDefaultDisplayNodes()
        self.positiveHalfOriginalModel.GetDisplayNode().SetVisibility(False)
        # self.negativeHalfOriginalModel.CreateDefaultDisplayNodes()
        self.negativeHalfOriginalModel.GetDisplayNode().SetVisibility(False)
        #
        self.ui.showRigidModelCheckbox.checked = 0
        self.ui.showAffineModelCheckbox.checked = 0
        self.ui.planeCutPushButton.enabled = False
        self.ui.keepHalfPushButton.enabled = True


    def onKeepHalfPushButton(self):
        if self.ui.leftSideRadioButton.checked == 1:
            self.negativeHalfModelNode.GetDisplayNode().SetVisibility(False)
            self.positiveHalfModelNode.GetDisplayNode().SetVisibility(True)
            self.halfModelRigidNode = self.positiveHalfModelNode
            self.halfOriginalNode = self.positiveHalfOriginalModel
        else:
            self.negativeHalfModelNode.GetDisplayNode().SetVisibility(True)
            self.positiveHalfModelNode.GetDisplayNode().SetVisibility(False)
            self.halfModelRigidNode = self.negativeHalfModelNode
            self.halfOriginalNode = self.negativeHalfOriginalModel
        self.ui.rigidMirroredHalfButton.enabled = True


    def onRigidMirroredHalfButton(self):
        #Perfrom itk rigid registration
        self.halfModelRigidNode.SetName(self.mirroredSkullModelNode.GetName() + "_half_rigid")
        logic = MirrorOrbitReconLogic()
        self.sourcePointsHalf, self.targetPointsHalf, halfScalingTransformNode, halfICPTransformNode = logic.ITKRegistration(self.halfModelRigidNode,
                                                                                                   self.halfOriginalNode,
                                                                                                   scalingOption=False,
                                                                                                   parameterDictionary=self.parameterDictionary,
                                                                                                   usePoisson=False)
        self.halfModelRigidNode.GetDisplayNode().SetColor(1, 0.67, 0)
        # self.halfModelRigidNode.GetDisplayNode.SetShading(True)
        self.mirrorPlaneNode.GetDisplayNode().SetVisibility(False)
        self.ui.rigidMirroredHalfButton.enabled = False
        self.ui.showRigidHalfModelCheckBox.enabled = True
        self.ui.showRigidHalfModelCheckBox.checked= 1
        self.ui.affineMirroredHalfButton.enabled = True


    def onShowRigidHalfModelCheckBox(self):
        try:
            if self.ui.showRigidHalfModelCheckBox.isChecked():
                self.halfModelRigidNode.GetDisplayNode().SetVisibility(True)
            else:
                self.halfModelRigidNode.GetDisplayNode().SetVisibility(False)
        except:
            pass


    def onAffineMirroredHalfButton(self):
        #Clone the rigid registered model again for affine
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self.halfModelRigidNode)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        self.halfModelaffineNode = shNode.GetItemDataNode(clonedItemID)
        self.halfModelaffineNode.SetName(self.mirroredSkullModelNode.GetName() + "_half_affine")
        self.halfModelaffineNode.GetDisplayNode().SetColor(0, 0, 1) #blue
        # self.halfModelaffineNode.GetDisplayNode().SetShading(True)
        #Affine deformable registration
        logic = MirrorOrbitReconLogic()
        transformation, translation = logic.CPDAffineTransform(self.halfModelaffineNode, self.sourcePoints, self.targetPoints)
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
        affineNodeName = self.mirroredSkullModelNode.GetName() + "half_affine"
        affineTransformNode.SetName(affineNodeName)

        self.ui.affineMirroredHalfButton.enabled = False
        self.ui.showRigidHalfModelCheckBox.checked = 0
        self.ui.showAffineHalfModelCheckbox.enabled = True
        self.ui.showAffineHalfModelCheckbox.checked = 1

    def onShowAffineHalfModelCheckbox(self):
        try:
            if self.ui.showAffineHalfModelCheckbox.isChecked():
                self.halfModelaffineNode.GetDisplayNode().SetVisibility(True)
            else:
                self.halfModelaffineNode.GetDisplayNode().SetVisibility(False)
        except:
            pass

    def onResetPushButton(self):
        self.ui.originalModelSelector.setCurrentNode(None)
        self.ui.planeLmSelector.setCurrentNode(None)
        self.ui.mirroredModelSelector.setCurrentNode(None)
        self.ui.createPlaneButton.enabled = False
        self.ui.planeAdjustCheckBox.checked = 0
        self.ui.planeAdjustCheckBox.enabled = False
        self.ui.createMirrorPushButton.enabled = False
        self.ui.skullRigidRegistrationPushButton.enabled = False
        self.ui.showRigidModelCheckbox.checked = 0
        self.ui.showRigidModelCheckbox.enabled = False
        self.ui.skullAffineRegistrationPushButton.enabled = 0
        self.ui.showAffineModelCheckbox.checked = 0
        self.ui.showAffineModelCheckbox.enabled = False
        self.ui.planeCutPushButton.enabled = False
        self.ui.keepHalfPushButton.enabled = False
        try:
            self.halfModelRigidNode.GetDisplayNode.SetVisibility(False)
        except:
            pass
        self.ui.rigidMirroredHalfButton.enabled=False
        self.ui.showRigidHalfModelCheckBox.checked = 0
        self.ui.showRigidHalfModelCheckBox.enabled = False
        self.ui.affineMirroredHalfButton.enabled = False
        self.ui.showAffineHalfModelCheckbox.checked = 0
        self.ui.showAffineHalfModelCheckbox.enabled = False
        self.ui.resetPushButton.enabled = 0

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
# MirrorOrbitReconLogic
#


class MirrorOrbitReconLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py

    The rigid and cpd registration functions are reused from the ALPACA and FastModelAlign modules of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return MirrorOrbitReconParameterNode(super().getParameterNode())

    def ITKRegistration(self, sourceModelNode, targetModelNode, scalingOption, parameterDictionary, usePoisson):
        #This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        # import ALPACA
        # logic = ALPACA.ALPACALogic()
        (
            sourcePoints,
            targetPoints,
            sourceFeatures,
            targetFeatures,
            voxelSize,
            scaling,
        ) = self.runSubsample(
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


        ICPTransform_similarity, similarityFlag = self.estimateTransform(
            sourcePoints,
            targetPoints,
            sourceFeatures,
            targetFeatures,
            voxelSize,
            scalingOption,
            parameterDictionary,
        )


        vtkSimilarityTransform = self.itkToVTKTransform(
            ICPTransform_similarity, similarityFlag
        )

        ICPTransformNode = self.convertMatrixToTransformNode(
            vtkSimilarityTransform, ("Rigid Transformation Matrix")
        )
        sourceModelNode.SetAndObserveTransformNodeID(ICPTransformNode.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(sourceModelNode)
        sourceModelNode.GetDisplayNode().SetVisibility(True)
        red = [1, 0, 0]
        sourceModelNode.GetDisplayNode().SetColor(1, 0, 0)
        # sourceModelNode.GetDisplayNode().SetShading(True)
        targetModelNode.GetDisplayNode().SetVisibility(True)

        sourcePoints = self.transform_numpy_points(sourcePoints, ICPTransform_similarity)


        #Put scaling transform under ICP transform = rigid transform after scaling
        scalingTransformNode.SetAndObserveTransformNodeID(ICPTransformNode.GetID())

        return sourcePoints, targetPoints, scalingTransformNode, ICPTransformNode


    def runSubsample(
        self,
        sourceModel,
        targetModel,
        scalingOption,
        parameters,
        usePoissonSubsample=False,
    ):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        print("parameters are ", parameters)
        print(":: Loading point clouds and downsampling")

        sourceModelMesh = sourceModel.GetMesh()
        targetModelMesh = targetModel.GetMesh()

        # Scale the mesh and the landmark points
        fixedBoxLengths, fixedlength = self.getBoxLengths(targetModelMesh)
        movingBoxLengths, movinglength = self.getBoxLengths(sourceModelMesh)

        # Sub-Sample the points for rigid refinement and deformable registration
        point_density = parameters["pointDensity"]

        # Voxel size is the diagonal length of cuboid in the voxelGrid
        voxel_size = np.sqrt(np.sum(np.square(np.array(fixedBoxLengths)))) / (
            55 * point_density
        )

        print("Scale length are  ", fixedlength, movinglength)
        print("Voxel Size is ", voxel_size)

        scalingFactor = fixedlength / movinglength
        if scalingOption is False:
            scalingFactor = 1
        print("Scaling factor is ", scalingFactor)

        sourceFullMesh_vtk = self.scale_vtk_point_coordinates(sourceModelMesh, scalingFactor)
        targetFullMesh_vtk = targetModelMesh

        if usePoissonSubsample:
            print("Using Poisson Point Subsampling Method")
            sourceMesh_vtk = self.subsample_points_poisson(
                sourceFullMesh_vtk, radius=voxel_size
            )
            targetMesh_vtk = self.subsample_points_poisson(
                targetFullMesh_vtk, radius=voxel_size
            )
        else:
            sourceMesh_vtk = self.subsample_points_voxelgrid_polydata(
                sourceFullMesh_vtk, radius=voxel_size
            )
            targetMesh_vtk = self.subsample_points_voxelgrid_polydata(
                targetFullMesh_vtk, radius=voxel_size
            )

        movingMeshPoints, movingMeshPointNormals = self.extract_pca_normal(
            sourceMesh_vtk, 30
        )
        fixedMeshPoints, fixedMeshPointNormals = self.extract_pca_normal(
            targetMesh_vtk, 30
        )

        print("------------------------------------------------------------")
        print("movingMeshPoints.shape ", movingMeshPoints.shape)
        print("movingMeshPointNormals.shape ", movingMeshPointNormals.shape)
        print("fixedMeshPoints.shape ", fixedMeshPoints.shape)
        print("fixedMeshPointNormals.shape ", fixedMeshPointNormals.shape)
        print("------------------------------------------------------------")

        fpfh_radius = parameters["FPFHSearchRadius"] * voxel_size
        fpfh_neighbors = parameters["FPFHNeighbors"]
        # New FPFH Code
        pcS = np.expand_dims(fixedMeshPoints, -1)
        normal_np_pcl = fixedMeshPointNormals
        target_fpfh = self.get_fpfh_feature(
            pcS, normal_np_pcl, fpfh_radius, fpfh_neighbors
        )
        # print(f"target_fpfh {target_fpfh.shape}: {target_fpfh}")

        pcS = np.expand_dims(movingMeshPoints, -1)
        normal_np_pcl = movingMeshPointNormals
        source_fpfh = self.get_fpfh_feature(
            pcS, normal_np_pcl, fpfh_radius, fpfh_neighbors
        )
        # print(f"source_fpfh {source_fpfh.shape}: {source_fpfh}")

        target_down = fixedMeshPoints
        source_down = movingMeshPoints
        return source_down, target_down, source_fpfh, target_fpfh, voxel_size, scalingFactor


    def getBoxLengths(self, inputMesh):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import vtk

        box_filter = vtk.vtkBoundingBox()
        box_filter.SetBounds(inputMesh.GetBounds())
        diagonalLength = box_filter.GetDiagonalLength()
        fixedLengths = [0.0, 0.0, 0.0]
        box_filter.GetLengths(fixedLengths)
        return fixedLengths, diagonalLength


    def get_fpfh_feature(self, points_np, normals_np, radius, neighbors):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import itk

        pointset = itk.PointSet[itk.F, 3].New()
        pointset.SetPoints(
            itk.vector_container_from_array(points_np.flatten().astype("float32"))
        )

        normalset = itk.PointSet[itk.F, 3].New()
        normalset.SetPoints(
            itk.vector_container_from_array(normals_np.flatten().astype("float32"))
        )
        fpfh = itk.Fpfh.PointFeature.MF3MF3.New()
        fpfh.ComputeFPFHFeature(pointset, normalset, float(radius), int(neighbors))
        result = fpfh.GetFpfhFeature()

        fpfh_feats = itk.array_from_vector_container(result)
        fpfh_feats = np.reshape(fpfh_feats, [33, pointset.GetNumberOfPoints()]).T
        return fpfh_feats


    def scale_vtk_point_coordinates(self, vtk_polydata, scalingFactor):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        from vtk.util import numpy_support

        points = vtk_polydata.GetPoints()
        pointdata = points.GetData()
        points_as_numpy = numpy_support.vtk_to_numpy(pointdata)
        points_as_numpy = points_as_numpy * scalingFactor
        self.set_numpy_points_in_vtk(vtk_polydata, points_as_numpy)

        return vtk_polydata

    def set_numpy_points_in_vtk(self, vtk_polydata, points_as_numpy):
        """
        Sets the numpy points to a vtk_polydata
        """
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import vtk
        from vtk.util import numpy_support

        vtk_data_array = numpy_support.numpy_to_vtk(
            num_array=points_as_numpy, deep=True, array_type=vtk.VTK_FLOAT
        )
        points2 = vtk.vtkPoints()
        points2.SetData(vtk_data_array)
        vtk_polydata.SetPoints(points2)
        return


    def subsample_points_poisson(self, inputMesh, radius):
        """
        Return sub-sampled points as numpy array.
        The radius might need to be tuned as per the requirements.
        """
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import vtk
        from vtk.util import numpy_support

        f = vtk.vtkPoissonDiskSampler()
        f.SetInputData(inputMesh)
        f.SetRadius(radius)
        f.Update()

        sampled_points = f.GetOutput()
        return sampled_points

    def subsample_points_voxelgrid_polydata(self, inputMesh, radius):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        subsample = vtk.vtkVoxelGrid()
        subsample.SetInputData(inputMesh)
        subsample.SetConfigurationStyleToLeafSize()

        subsample.SetLeafSize(radius, radius, radius)
        subsample.Update()
        points = subsample.GetOutput()
        return points


    def extract_pca_normal(self, mesh, normalNeighbourCount):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import vtk
        from vtk.util import numpy_support

        normals = vtk.vtkPCANormalEstimation()
        normals.SetSampleSize(normalNeighbourCount)
        # normals.SetFlipNormals(True)
        normals.SetNormalOrientationToPoint()
        # normals.SetNormalOrientationToGraphTraversal()
        normals.SetInputData(mesh)
        normals.Update()
        out1 = normals.GetOutput()
        normal_array = numpy_support.vtk_to_numpy(out1.GetPointData().GetNormals())
        point_array = numpy_support.vtk_to_numpy(mesh.GetPoints().GetData())
        return point_array, normal_array


    def estimateTransform(
        self,
        sourcePoints,
        targetPoints,
        sourceFeatures,
        targetFeatures,
        voxelSize,
        scalingOption,
        parameters,
    ):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)

        import itk

        similarityFlag = False
        # Establish correspondences by nearest neighbour search in feature space
        corrs_A, corrs_B = self.find_correspondences(
            targetFeatures, sourceFeatures, mutual_filter=True
        )

        targetPoints = targetPoints.T
        sourcePoints = sourcePoints.T

        fixed_corr = targetPoints[:, corrs_A]  # np array of size 3 by num_corrs
        moving_corr = sourcePoints[:, corrs_B]  # np array of size 3 by num_corrs

        num_corrs = fixed_corr.shape[1]
        print(f"FPFH generates {num_corrs} putative correspondences.")

        targetPoints = targetPoints.T
        sourcePoints = sourcePoints.T

        # Check corner case when both meshes are same
        if np.allclose(fixed_corr, moving_corr):
            print("Same meshes therefore returning Identity Transform")
            transform = itk.VersorRigid3DTransform[itk.D].New()
            transform.SetIdentity()
            return [transform, transform]

        import time

        bransac = time.time()

        maxAttempts = 1
        attempt = 0
        best_fitness = -1
        best_rmse = np.inf
        while attempt < maxAttempts:
            # Perform Initial alignment using Ransac parallel iterations with no scaling
            transform_matrix, fitness, rmse = self.ransac_using_package(
                movingMeshPoints=sourcePoints,
                fixedMeshPoints=targetPoints,
                movingMeshFeaturePoints=moving_corr.T,
                fixedMeshFeaturePoints=fixed_corr.T,
                number_of_iterations=parameters["maxRANSAC"],
                number_of_ransac_points=3,
                inlier_value=float(parameters["distanceThreshold"]) * voxelSize,
                scalingOption=False,
                check_edge_length=True,
                correspondence_distance=0.9,
            )

            transform = itk.transform_from_dict(transform_matrix)
            fitness_forward, rmse_forward = self.get_fitness(
                sourcePoints,
                targetPoints,
                float(parameters["distanceThreshold"]) * voxelSize,
                transform,
            )

            mean_fitness = fitness_forward
            mean_rmse = rmse_forward
            print(
                "Non-Scaling Attempt = ",
                attempt,
                " Fitness = ",
                mean_fitness,
                " RMSE is ",
                mean_rmse,
            )

            if mean_fitness > 0.99:
                # Only compare RMSE if mean_fitness is greater than 0.99
                if mean_rmse < best_rmse:
                    best_fitness = mean_fitness
                    best_rmse = mean_rmse
                    best_transform = transform_matrix
            else:
                if mean_fitness > best_fitness:
                    best_fitness = mean_fitness
                    best_rmse = mean_rmse
                    best_transform = transform_matrix

            # Rigid Transform is un-fit for this use-case so perform scaling based RANSAC
            # if mean_fitness < 0.9:
            #  break
            attempt = attempt + 1

        print("Best Fitness without Scaling ", best_fitness, " RMSE is ", best_rmse)

        if scalingOption:
            maxAttempts = 10
            attempt = 0

            correspondence_distance = 0.9
            ransac_points = 3
            ransac_iterations = int(parameters["maxRANSAC"])

            while mean_fitness < 0.99 and attempt < maxAttempts:
                transform_matrix, fitness, rmse = self.ransac_using_package(
                    movingMeshPoints=sourcePoints,
                    fixedMeshPoints=targetPoints,
                    movingMeshFeaturePoints=moving_corr.T,
                    fixedMeshFeaturePoints=fixed_corr.T,
                    number_of_iterations=ransac_iterations,
                    number_of_ransac_points=ransac_points,
                    inlier_value=float(parameters["distanceThreshold"]) * voxelSize,
                    scalingOption=True,
                    check_edge_length=False,
                    correspondence_distance=correspondence_distance,
                )

                transform = itk.transform_from_dict(transform_matrix)
                fitness_forward, rmse_forward = self.get_fitness(
                    sourcePoints,
                    targetPoints,
                    float(parameters["distanceThreshold"]) * voxelSize,
                    transform,
                )

                mean_fitness = fitness_forward
                mean_rmse = rmse_forward
                print(
                    "Scaling Attempt = ",
                    attempt,
                    " Fitness = ",
                    mean_fitness,
                    " RMSE = ",
                    mean_rmse,
                )

                if (mean_fitness > best_fitness) or (
                    mean_fitness == best_fitness and mean_rmse < best_rmse
                ):
                    best_fitness = mean_fitness
                    best_rmse = mean_rmse
                    best_transform = transform_matrix
                    similarityFlag = True
                attempt = attempt + 1

        aransac = time.time()
        print("RANSAC Duraction ", aransac - bransac)
        print("Best Fitness after scaling ", best_fitness)

        first_transform = itk.transform_from_dict(best_transform)
        sourcePoints = self.transform_numpy_points(sourcePoints, first_transform)

        print("-----------------------------------------------------------")
        print(parameters)
        print("Starting Rigid Refinement")
        distanceThreshold = parameters["ICPDistanceThreshold"] * voxelSize
        inlier, rmse = self.get_fitness(sourcePoints, targetPoints, distanceThreshold)
        print("Before Inlier = ", inlier, " RMSE = ", rmse)
        _, second_transform = self.final_iteration_icp(
            targetPoints,
            sourcePoints,
            distanceThreshold,
            float(parameters["normalSearchRadius"] * voxelSize),
        )

        final_mesh_points = self.transform_numpy_points(sourcePoints, second_transform)
        inlier, rmse = self.get_fitness(
            final_mesh_points, targetPoints, distanceThreshold
        )
        print("After Inlier = ", inlier, " RMSE = ", rmse)
        first_transform.Compose(second_transform)
        return first_transform, similarityFlag



    def find_correspondences(self, feats0, feats1, mutual_filter=True):
        """
        This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        Using the FPFH features find noisy corresspondes.
        These corresspondes will be used inside the RANSAC.
        """
        nns01, dists1 = self.find_knn_cpu(feats0, feats1, knn=1, return_distance=True)
        corres01_idx0 = np.arange(len(nns01))
        corres01_idx1 = nns01

        if not mutual_filter:
            return corres01_idx0, corres01_idx1

        nns10, dists2 = self.find_knn_cpu(feats1, feats0, knn=1, return_distance=True)
        corres10_idx1 = np.arange(len(nns10))
        corres10_idx0 = nns10

        mutual_filter = corres10_idx0[corres01_idx1] == corres01_idx0
        corres_idx0 = corres01_idx0[mutual_filter]
        corres_idx1 = corres01_idx1[mutual_filter]

        return corres_idx0, corres_idx1


    def find_knn_cpu(self, feat0, feat1, knn=1, return_distance=False):
        from scipy.spatial import cKDTree

        feat1tree = cKDTree(feat1)
        dists, nn_inds = feat1tree.query(feat0, k=knn)
        if return_distance:
            return nn_inds, dists
        else:
            return nn_inds

    def get_fitness(
        self, movingMeshPoints, fixedMeshPoints, distanceThrehold, transform=None
    ):
        import itk

        movingPointSet = itk.Mesh.F3.New()
        movingPointSet.SetPoints(
            itk.vector_container_from_array(
                movingMeshPoints.flatten().astype("float32")
            )
        )

        fixedPointSet = itk.Mesh.F3.New()
        fixedPointSet.SetPoints(
            itk.vector_container_from_array(fixedMeshPoints.flatten().astype("float32"))
        )

        if transform is not None:
            movingPointSet = itk.transform_mesh_filter(
                movingPointSet, transform=transform
            )

        PointType = itk.Point[itk.F, 3]
        PointsContainerType = itk.VectorContainer[itk.IT, PointType]
        pointsLocator = itk.PointsLocator[PointsContainerType].New()
        pointsLocator.SetPoints(fixedPointSet.GetPoints())
        pointsLocator.Initialize()

        fitness = 0
        inlier_rmse = 0
        for i in range(movingPointSet.GetNumberOfPoints()):
            closestPoint = pointsLocator.FindClosestPoint(movingPointSet.GetPoint(i))
            distance = (
                fixedPointSet.GetPoint(closestPoint) - movingPointSet.GetPoint(i)
            ).GetNorm()
            if distance < distanceThrehold:
                fitness = fitness + 1
                inlier_rmse = inlier_rmse + distance

        return fitness / movingPointSet.GetNumberOfPoints(), inlier_rmse / fitness


    def ransac_using_package(
        self,
        movingMeshPoints,
        fixedMeshPoints,
        movingMeshFeaturePoints,
        fixedMeshFeaturePoints,
        number_of_iterations,
        number_of_ransac_points,
        inlier_value,
        scalingOption,
        check_edge_length,
        correspondence_distance,
    ):
        # This function is reused from the ALPACA module of SlicerMorph (https://github.com/SlicerMorph/SlicerMorph/tree/master)
        import itk

        def GenerateData(data, agreeData):
            """
            In current implementation the agreedata contains two corresponding
            points from moving and fixed mesh. However, after the subsampling step the
            number of points need not be equal in those meshes. So we randomly sample
            the points from larger mesh.
            """
            data.reserve(movingMeshFeaturePoints.shape[0])
            for i in range(movingMeshFeaturePoints.shape[0]):
                point1 = movingMeshFeaturePoints[i]
                point2 = fixedMeshFeaturePoints[i]
                input_data = [
                    point1[0],
                    point1[1],
                    point1[2],
                    point2[0],
                    point2[1],
                    point2[2],
                ]
                input_data = [float(x) for x in input_data]
                data.push_back(input_data)

            count_min = int(
                np.min([movingMeshPoints.shape[0], fixedMeshPoints.shape[0]])
            )

            mesh1_points = copy.deepcopy(movingMeshPoints)
            mesh2_points = copy.deepcopy(fixedMeshPoints)

            np.random.seed(0)
            np.random.shuffle(mesh1_points)
            np.random.seed(0)
            np.random.shuffle(mesh2_points)

            agreeData.reserve(count_min)
            for i in range(count_min):
                point1 = mesh1_points[i]
                point2 = mesh2_points[i]
                input_data = [
                    point1[0],
                    point1[1],
                    point1[2],
                    point2[0],
                    point2[1],
                    point2[2],
                ]
                input_data = [float(x) for x in input_data]
                agreeData.push_back(input_data)
            return

        data = itk.vector[itk.Point[itk.D, 6]]()
        agreeData = itk.vector[itk.Point[itk.D, 6]]()
        GenerateData(data, agreeData)

        transformParameters = itk.vector.D()
        bestTransformParameters = itk.vector.D()

        itk.MultiThreaderBase.SetGlobalDefaultThreader(
            itk.MultiThreaderBase.ThreaderTypeFromString("POOL")
        )
        maximumDistance = inlier_value
        if not scalingOption:
            print("Rigid Reg, no scaling")
            TransformType = itk.VersorRigid3DTransform[itk.D]
            RegistrationEstimatorType = itk.Ransac.LandmarkRegistrationEstimator[
                6, TransformType
            ]
        else:
            print("NonRigid Reg, with scaling")
            TransformType = itk.Similarity3DTransform[itk.D]
            RegistrationEstimatorType = itk.Ransac.LandmarkRegistrationEstimator[
                6, TransformType
            ]
        registrationEstimator = RegistrationEstimatorType.New()
        registrationEstimator.SetMinimalForEstimate(number_of_ransac_points)
        registrationEstimator.SetAgreeData(agreeData)
        registrationEstimator.SetDelta(maximumDistance)
        registrationEstimator.LeastSquaresEstimate(data, transformParameters)

        maxThreadCount = int(
            itk.MultiThreaderBase.New().GetMaximumNumberOfThreads() / 2
        )

        desiredProbabilityForNoOutliers = 0.99
        RANSACType = itk.RANSAC[itk.Point[itk.D, 6], itk.D, TransformType]
        ransacEstimator = RANSACType.New()
        ransacEstimator.SetData(data)
        ransacEstimator.SetAgreeData(agreeData)
        ransacEstimator.SetCheckCorresspondenceDistance(check_edge_length)
        if correspondence_distance > 0:
            ransacEstimator.SetCheckCorrespondenceEdgeLength(correspondence_distance)
        ransacEstimator.SetMaxIteration(int(number_of_iterations / maxThreadCount))
        ransacEstimator.SetNumberOfThreads(maxThreadCount)
        ransacEstimator.SetParametersEstimator(registrationEstimator)

        percentageOfDataUsed = ransacEstimator.Compute(
            transformParameters, desiredProbabilityForNoOutliers
        )

        transform = TransformType.New()
        p = transform.GetParameters()
        f = transform.GetFixedParameters()
        for i in range(p.GetSize()):
            p.SetElement(i, transformParameters[i])
        counter = 0
        totalParameters = p.GetSize() + f.GetSize()
        for i in range(p.GetSize(), totalParameters):
            f.SetElement(counter, transformParameters[i])
            counter = counter + 1
        transform.SetParameters(p)
        transform.SetFixedParameters(f)
        return (
            itk.dict_from_transform(transform),
            percentageOfDataUsed[0],
            percentageOfDataUsed[1],
        )


    def itkToVTKTransform(self, itkTransform, similarityFlag=False):
        matrix = itkTransform.GetMatrix()
        offset = itkTransform.GetOffset()

        matrix_vtk = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                matrix_vtk.SetElement(i, j, matrix(i, j))
        for i in range(3):
            matrix_vtk.SetElement(i, 3, offset[i])

        transform = vtk.vtkTransform()
        transform.SetMatrix(matrix_vtk)
        return transform


    def transform_numpy_points(self, points_np, transform):
        import itk

        mesh = itk.Mesh[itk.F, 3].New()
        mesh.SetPoints(
            itk.vector_container_from_array(points_np.flatten().astype("float32"))
        )
        transformed_mesh = itk.transform_mesh_filter(mesh, transform=transform)
        points_tranformed = itk.array_from_vector_container(
            transformed_mesh.GetPoints()
        )
        points_tranformed = np.reshape(points_tranformed, [-1, 3])
        return points_tranformed


    def final_iteration_icp(
        self, fixedPoints, movingPoints, distanceThreshold, normalSearchRadius
    ):
        import itk
        fixedPointsNormal = self.extract_pca_normal_scikit(
            fixedPoints, normalSearchRadius
        )
        movingPointsNormal = self.extract_pca_normal_scikit(
            movingPoints, normalSearchRadius
        )

        _, (T, R, t) = self.point_to_plane_icp(
            movingPoints,
            fixedPoints,
            movingPointsNormal,
            fixedPointsNormal,
            distanceThreshold,
        )

        transform = itk.Rigid3DTransform.D.New()
        transform.SetMatrix(itk.matrix_from_array(R), 0.000001)
        transform.SetTranslation([t[0], t[1], t[2]])
        return movingPoints, transform

    def point_to_plane_icp(
        self,
        src_pts,
        dst_pts,
        src_pt_normals,
        dst_pt_normals,
        dist_threshold=np.inf,
        max_iterations=30,
        tolerance=0.000001,
    ):
        """
            The Iterative Closest Point method: finds best-fit transform that
                maps points A on to points B
            Input:
                A: Nxm numpy array of source mD points
                B: Nxm numpy array of destination mD point
                max_iterations: exit algorithm after max_iterations
                tolerance: convergence criteria
            Output:
                T: final homogeneous transformation that maps A on to B
                MeanError: list, report each iteration's distance mean error
        """
        A = src_pts
        A_normals = src_pt_normals
        B = dst_pts
        B_normals = dst_pt_normals

        # get number of dimensions
        m = A.shape[1]

        # make points homogeneous, copy them to maintain the originals
        src = np.ones((m + 1, A.shape[0]))
        dst = np.ones((m + 1, B.shape[0]))
        src[:m, :] = np.copy(A.T)
        dst[:m, :] = np.copy(B.T)

        prev_error = 0
        MeanError = []

        finalT = np.identity(4)

        for i in range(max_iterations):
            # find the nearest neighbors between the current source and destination points
            distances, indices = self.nearest_neighbor(src[:m, :].T, dst[:m, :].T)

            # match each point of source-set to closest point of destination-set,
            matched_src_pts = src[:m, :].T.copy()
            matched_dst_pts = dst[:m, indices].T

            # compute angle between 2 matched vertexs' normals
            matched_src_pt_normals = A_normals.copy()
            matched_dst_pt_normals = B_normals[indices, :]
            angles = np.zeros(matched_src_pt_normals.shape[0])
            for k in range(matched_src_pt_normals.shape[0]):
                v1 = matched_src_pt_normals[k, :]
                v2 = matched_dst_pt_normals[k, :]
                cos_angle = v1.dot(v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                angles[k] = np.arccos(cos_angle) / np.pi * 180

            # and reject the bad corresponding
            # dist_threshold = np.inf
            dist_bool_flag = distances < dist_threshold
            angle_threshold = 20
            angle_bool_flag = angles < angle_threshold
            reject_part_flag = dist_bool_flag  # * angle_bool_flag

            # get matched vertices and dst_vertexes' normals
            matched_src_pts = matched_src_pts[reject_part_flag, :]
            matched_dst_pts = matched_dst_pts[reject_part_flag, :]
            matched_dst_pt_normals = matched_dst_pt_normals[reject_part_flag, :]

            # compute the transformation between the current source and nearest destination points
            T, _, _ = self.best_fit_transform_point2plane(
                matched_src_pts, matched_dst_pts, matched_dst_pt_normals
            )

            finalT = np.dot(T, finalT)

            # update the current source
            src = np.dot(T, src)

            # print iteration
            # print('\ricp iteration: %d/%d ...' % (i+1, max_iterations), end='', flush=True)

            # check error
            mean_error = np.mean(distances[reject_part_flag])
            MeanError.append(mean_error)
            if tolerance is not None:
                if np.abs(prev_error - mean_error) < tolerance:
                    break
            prev_error = mean_error
        print("Refinement took ", i, " iterations")
        # calculate final transformation
        # T, R, t = self.best_fit_transform_point2point(A, src[:m, :].T)
        # return MeanError, (T, R, t)
        return MeanError, (finalT, finalT[:3, :3], finalT[:, 3])


    def nearest_neighbor(self, src, dst):
        """
        Find the nearest (Euclidean) neighbor in dst for each point in src
        Input:
            src: Nxm array of points
            dst: Nxm array of points
        Output:
            distances: Euclidean distances of the nearest neighbor
            indices: dst indices of the nearest neighbor
        """
            # assert src.shape == dst.shape
        from sklearn.neighbors import NearestNeighbors
        neigh = NearestNeighbors(n_neighbors=1, algorithm="kd_tree")
        neigh.fit(dst)
        distances, indices = neigh.kneighbors(src, return_distance=True)
        return distances.ravel(), indices.ravel()


    def best_fit_transform_point2plane(self, A, B, normals):
        """
            reference: https://www.comp.nus.edu.sg/~lowkl/publications/lowk_point-to-plane_icp_techrep.pdf
            Input:
            A: Nx3 numpy array of corresponding points
            B: Nx3 numpy array of corresponding points
            normals: Nx3 numpy array of B's normal vectors
            Returns:
            T: (m+1)x(m+1) homogeneous transformation matrix that maps A on to B
            R: mxm rotation matrix
            t: mx1 translation vector
        """
        assert A.shape == B.shape
        assert A.shape == normals.shape

        H = []
        b = []
        for i in range(A.shape[0]):
            dx = B[i, 0]
            dy = B[i, 1]
            dz = B[i, 2]
            nx = normals[i, 0]
            ny = normals[i, 1]
            nz = normals[i, 2]
            sx = A[i, 0]
            sy = A[i, 1]
            sz = A[i, 2]

            _a1 = (nz * sy) - (ny * sz)
            _a2 = (nx * sz) - (nz * sx)
            _a3 = (ny * sx) - (nx * sy)

            _a = np.array([_a1, _a2, _a3, nx, ny, nz])
            _b = (nx * dx) + (ny * dy) + (nz * dz) - (nx * sx) - (ny * sy) - (nz * sz)

            H.append(_a)
            b.append(_b)

        H = np.array(H)
        b = np.array(b)

        tr = np.dot(np.linalg.pinv(H), b)
        T = self.euler_matrix(tr[0], tr[1], tr[2])
        T[0, 3] = tr[3]
        T[1, 3] = tr[4]
        T[2, 3] = tr[5]

        R = T[:3, :3]
        t = T[:3, 3]

        return T, R, t


    def euler_matrix(self, ai, aj, ak):
        """Return homogeneous rotation matrix from Euler angles and axis sequence.
        ai, aj, ak : Euler's roll, pitch and yaw angles
        axes : One of 24 axis sequences as string or encoded tuple
        >>> R = euler_matrix(1, 2, 3, 'syxz')
        >>> numpy.allclose(numpy.sum(R[0]), -1.34786452)
        True
        >>> R = euler_matrix(1, 2, 3, (0, 1, 0, 1))
        """

        firstaxis, parity, repetition, frame = (0, 0, 0, 0)
        _NEXT_AXIS = [1, 2, 0, 1]

        i = firstaxis
        j = _NEXT_AXIS[i + parity]
        k = _NEXT_AXIS[i - parity + 1]

        if frame:
            ai, ak = ak, ai
        if parity:
            ai, aj, ak = -ai, -aj, -ak

        si, sj, sk = math.sin(ai), math.sin(aj), math.sin(ak)
        ci, cj, ck = math.cos(ai), math.cos(aj), math.cos(ak)
        cc, cs = ci * ck, ci * sk
        sc, ss = si * ck, si * sk

        M = np.identity(4)
        if repetition:
            M[i, i] = cj
            M[i, j] = sj * si
            M[i, k] = sj * ci
            M[j, i] = sj * sk
            M[j, j] = -cj * ss + cc
            M[j, k] = -cj * cs - sc
            M[k, i] = -sj * ck
            M[k, j] = cj * sc + cs
            M[k, k] = cj * cc - ss
        else:
            M[i, i] = cj * ck
            M[i, j] = sj * sc - cs
            M[i, k] = sj * cc + ss
            M[j, i] = cj * sk
            M[j, j] = sj * ss + cc
            M[j, k] = sj * cs - sc
            M[k, i] = -sj
            M[k, j] = cj * si
            M[k, k] = cj * ci
        return M


    def extract_pca_normal_scikit(self, inputPoints, searchRadius):
        from sklearn.neighbors import KDTree
        from sklearn.decomposition import PCA

        data = inputPoints
        tree = KDTree(data, metric="minkowski")  # minkowki is p2 (euclidean)

        # Get indices and distances:
        ind, dist = tree.query_radius(data, r=searchRadius, return_distance=True)

        def PCA_unit_vector(array, pca=PCA(n_components=3)):
            pca.fit(array)
            eigenvalues = pca.explained_variance_
            return pca.components_[np.argmin(eigenvalues)]

        def calc_angle_with_xy(vectors):
            l = np.sum(vectors[:, :2] ** 2, axis=1) ** 0.5
            return np.arctan2(vectors[:, 2], l)

        normals2 = []
        for i in range(data.shape[0]):
            if len(ind[i]) < 3:
                normal_vector = np.identity(3)
            else:
                normal_vector = data[ind[i]]
            normals2.append(PCA_unit_vector(normal_vector))

        n = np.array(normals2)
        n[calc_angle_with_xy(n) < 0] *= -1
        return n


    def convertMatrixToTransformNode(self, vtkTransform, transformName):
        transformNode = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLTransformNode", transformName
        )
        transformNode.SetAndObserveTransformToParent(vtkTransform)
        return transformNode


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
# MirrorOrbitReconTest
#


class MirrorOrbitReconTest(ScriptedLoadableModuleTest):
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
        self.test_MirrorOrbitRecon1()

    def test_MirrorOrbitRecon1(self):
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
        inputVolume = SampleData.downloadSample("MirrorOrbitRecon1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = MirrorOrbitReconLogic()

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
