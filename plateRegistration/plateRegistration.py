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

import numpy as np

import qt

from datetime import datetime

from slicer import vtkMRMLModelNode, vtkMRMLTransformNode, vtkMRMLMarkupsFiducialNode
import json

#
# plateRegistration
#


class plateRegistration(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("plateRegistration")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Chi Zhang (Texas A&M University School of Dentistry)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#plateRegistration">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
Will update soon
""")

        # Additional initialization step after application startup is complete
        # slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


# def registerSampleData():
#     """Add data sets to Sample Data module."""
#     # It is always recommended to provide sample data for users to make it easy to try the module,
#     # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.
# 
#     import SampleData
# 
#     iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")
# 
#     # To ensure that the source code repository remains small (can be downloaded and installed quickly)
#     # it is recommended to store data sets that are larger than a few MB in a Github release.
# 
#     # plateRegistration1
#     SampleData.SampleDataLogic.registerCustomSampleDataSource(
#         # Category and sample name displayed in Sample Data module
#         category="plateRegistration",
#         sampleName="plateRegistration1",
#         # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
#         # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
#         thumbnailFileName=os.path.join(iconsPath, "plateRegistration1.png"),
#         # Download URL and target file name
#         uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
#         fileNames="plateRegistration1.nrrd",
#         # Checksum to ensure file integrity. Can be computed by this command:
#         #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
#         checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
#         # This node name will be used when the data set is loaded
#         nodeNames="plateRegistration1",
#     )
# 
#     # plateRegistration2
#     SampleData.SampleDataLogic.registerCustomSampleDataSource(
#         # Category and sample name displayed in Sample Data module
#         category="plateRegistration",
#         sampleName="plateRegistration2",
#         thumbnailFileName=os.path.join(iconsPath, "plateRegistration2.png"),
#         # Download URL and target file name
#         uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
#         fileNames="plateRegistration2.nrrd",
#         checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
#         # This node name will be used when the data set is loaded
#         nodeNames="plateRegistration2",
#     )


@parameterNodeWrapper
class plateRegistrationParameterNode:
    """
    The parameters needed by module.

    rigidRegisteredPlateModel - rigid registered plate model node
    originalPlateLm - unregistered plate lm node
    registeredPlateModel - A fully registered plate node
    orbitLm - orbit lm for initial registration
    fractureOrbitModel - model with orbital fracture
    initialTransform - Initial fiducial rigid registration and aligning at the posterior stop
    interactionTransform - interaction transform matrix after initial transform
    allTransformNode - A transformation matrix record the full transformation matrix for the plate in its original position
    ioRootDir - A folder dir containing input and output sub-folders for plate fit metrics and comparison
    reconstructOrbitModel - reconstructed orbit using mirror image

    """

    originalPlateModel: vtkMRMLModelNode
    rigidRegisteredPlateModel: vtkMRMLModelNode
    originalPlateLm: vtkMRMLMarkupsFiducialNode
    registeredPlateLm: vtkMRMLMarkupsFiducialNode
    orbitLm: vtkMRMLMarkupsFiducialNode
    fractureOrbitModel: vtkMRMLModelNode
    interactionPlateModel: vtkMRMLModelNode
    initialRigidTransform: vtkMRMLTransformNode
    alignPosteriorStopTransform: vtkMRMLTransformNode
    interactionTransformRecorder: vtkMRMLTransformNode
    allTransformNode: vtkMRMLTransformNode
    plateRegFolderName: str
    ioRootDir: str
    repairedOrbitModel: vtkMRMLModelNode
    registeredPlateInforJSON: str
    # registeredPlateInfoDict: dict[str, tuple[vtkMRMLModelNode, vtkMRMLTransformNode]]



#
# plateRegistrationWidget
#


class plateRegistrationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/plateRegistration.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = plateRegistrationLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        #plateRegistrationSubjectHierarchyTreeView
        self.ui.plateRegistrationSubjectHierarchyTreeView.setMRMLScene(slicer.mrmlScene)

        #Input connections
        self.ui.inputOrbitModelSelector.connect("currentItemChanged(vtkIdType)", self.onSelectOrbitModelNode)
        self.ui.inputOrbitModelSelector.connect("currentItemChanged(vtkIdType)", self.enableInitalRegistration)
        self.ui.inputOrbitModelSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.inputOrbitModelSelector.setNodeTypes(['vtkMRMLModelNode'])
        #
        self.ui.orbitFiducialSelector.connect("currentItemChanged(vtkIdType)", self.onSelectOrbitLmNode)
        self.ui.orbitFiducialSelector.connect("currentItemChanged(vtkIdType)", self.enableInitalRegistration)
        self.ui.orbitFiducialSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.orbitFiducialSelector.setNodeTypes(['vtkMRMLMarkupsFiducialNode'])
        #
        self.ui.plateModelSelector.connect("currentItemChanged(vtkIdType)", self.onSelectPlateModelNode)
        self.ui.plateModelSelector.connect("currentItemChanged(vtkIdType)", self.enableInitalRegistration)
        self.ui.plateModelSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.plateModelSelector.setNodeTypes(['vtkMRMLModelNode'])
        #
        self.ui.plateFiducialSelector.connect("currentItemChanged(vtkIdType)", self.onSelectPlateLmNode)
        self.ui.plateFiducialSelector.connect("currentItemChanged(vtkIdType)", self.enableInitalRegistration)
        self.ui.plateFiducialSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.plateFiducialSelector.setNodeTypes(['vtkMRMLMarkupsFiducialNode'])

        self.ui.placeOrbitLmPushButton.connect('clicked(bool)', self.onPlaceOrbitLmPushButton)

        self.ui.placePlateLmPushButton.connect('clicked(bool)', self.onPlacePlateLmPushButton)

        #Initial registration connections
        self.ui.initialRegistrationPushButton.connect('clicked(bool)', self.onInitialRegistrationPushButton)
        self.ui.posteriorStopRegistrationPushButton.connect('clicked(bool)', self.onRotation_p_stop_pushButton)
        
        #Intersection model
        self.ui.createIntersectButton.connect('clicked(bool)', self.onCreateIntersectButton)

        #Instant heatmap during plate registration
        self.ui.instantHeatMapPushButton.connect('clicked(bool)', self.onInstantHeatMap)

        #interaction transform
        self.ui.interactionTransformCheckbox.connect("toggled(bool)", self.onInteractionTransform)
        self.ui.realignHandleToPStopButton.connect('clicked(bool)', self.onRealignHandleToPStopButton)
        self.ui.resetToLastStepButton.connect('clicked(bool)', self.onResetToLastStepButton)
        self.ui.resetAllPushButton.connect('clicked(bool)', self.onResetAllPushButton)
        self.ui.finalizePlateRegistrationPushButton.connect('clicked(bool)', self.onFinalizePlateRegistrationPushButton)

        self.ui.currentRegResultsPathLineEdit.connect("currentPathChanged(QString)", self.onCurrentRegResultsPathLineEdit)
        self.ui.saveCurrentRegPushButton.connect('clicked(bool)', self.onSaveCurrentRegPushButton)

        #Plate fit tab connections
        self.ui.plateModelSelector2.setMRMLScene(slicer.mrmlScene)
        self.ui.orbitModelSelector2.setMRMLScene(slicer.mrmlScene)
        self.ui.plateTransformSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.computeHeatmapPushButton.connect('clicked(bool)', self.onPlateHeatmap)
        self.ui.projectPointsButton.connect('clicked(bool)', self.onProjectPoints)
        self.ui.compareFitnessButton.connect('clicked(bool)', self.onCompareFitness)

        
        self.timer = qt.QTimer()
        self.timer.setInterval(500) #ms
        self.timer.setSingleShot(True)
        self.timer.connect("timeout()", self.timeout)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()


    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)


    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        # if not self._parameterNode.inputVolume:
        #     firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        #     if firstVolumeNode:
        #         self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[plateRegistrationParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            # self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            # self._checkCanApply()

    def onSelectOrbitModelNode(self):
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        try:
            self._parameterNode.fractureOrbitModel.GetDisplayNode().SetVisibility(False)
        except:
            pass
        try:
            fracturedOrbitModelId = self.ui.inputOrbitModelSelector.currentItem()
            self._parameterNode.fractureOrbitModel = shNode.GetItemDataNode(fracturedOrbitModelId)
            self._parameterNode.fractureOrbitModel.GetDisplayNode().SetVisibility(True)
        except:
            pass
        self.ui.placeOrbitLmPushButton.enabled = bool(self.ui.inputOrbitModelSelector.currentItem())

    def onSelectOrbitLmNode(self):
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        try:
            self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(False)
        except:
            pass
        try:
            orbitLmId = self.ui.orbitFiducialSelector.currentItem()
            self._parameterNode.orbitLm = shNode.GetItemDataNode(orbitLmId)
            self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(True)
        except:
            pass

    def onSelectPlateModelNode(self):
        try:
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetVisibility(False)
        except:
            pass
        try:
            self._parameterNode.rigidRegisteredPlateModel.GetDisplayNode().SetVisibility(False)
        except:
            pass
        try:
            self._parameterNode.originalPlateModel.GetDisplayNode().SetVisibility(False)
        except:
            pass
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        try:
            originalPlateModelId = self.ui.plateModelSelector.currentItem()
            self._parameterNode.originalPlateModel = shNode.GetItemDataNode(originalPlateModelId)
            self._parameterNode.originalPlateModel.GetDisplayNode().SetVisibility(True)
        except:
            pass

    def onSelectPlateLmNode(self):
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        try:
            self._parameterNode.originalPlateLm.GetDisplayNode().SetVisibility(False)
        except:
            pass
        try:
            originalPlateLmId = self.ui.plateFiducialSelector.currentItem()
            self._parameterNode.originalPlateLm = shNode.GetItemDataNode(originalPlateLmId)
            self._parameterNode.originalPlateLm.GetDisplayNode().SetVisibility(True)
        except:
            pass
        self.ui.placePlateLmPushButton.enabled = bool(self.ui.plateModelSelector.currentItem())

    def enableInitalRegistration(self):
        self.ui.initialRegistrationPushButton.enabled = bool(self.ui.inputOrbitModelSelector.currentItem() and self.ui.orbitFiducialSelector.currentItem()
            and self.ui.plateModelSelector.currentItem() and self.ui.plateFiducialSelector.currentItem())


    def onCurrentRegResultsPathLineEdit(self):
        if self.ui.currentRegResultsPathLineEdit.currentPath:
            self.ui.saveCurrentRegPushButton.enabled = True
        else:
            self.ui.saveCurrentRegPushButton.enabled = False


    def onPlaceOrbitLmPushButton(self):
        logic = plateRegistrationLogic()
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        # Create a point list
        self._parameterNode.orbitLm = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self._parameterNode.orbitLm.SetName(self._parameterNode.fractureOrbitModel.GetName() + "_lm")
        self._parameterNode.orbitLm.SetMaximumNumberOfControlPoints(3)
        orbitLmNodeId = shNode.GetItemByDataNode(self._parameterNode.orbitLm)
        self.ui.orbitFiducialSelector.setCurrentItem(orbitLmNodeId)
        logic.placeLm(self._parameterNode.orbitLm)


    def onPlacePlateLmPushButton(self):
        logic = plateRegistrationLogic()
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        # Create a point list
        self._parameterNode.originalPlateLm = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self._parameterNode.originalPlateLm.SetName(self._parameterNode.originalPlateModel.GetName() + "_lm")
        self._parameterNode.originalPlateLm.SetMaximumNumberOfControlPoints(3)
        originalPlateLmNodeId = shNode.GetItemByDataNode(self._parameterNode.originalPlateLm)
        self.ui.plateFiducialSelector.setCurrentItem(originalPlateLmNodeId)
        logic.placeLm(self._parameterNode.originalPlateLm)


    def onInitialRegistrationPushButton(self):
        logic = plateRegistrationLogic()
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        #
        initial_transform = logic.rigid_transform(self._parameterNode.originalPlateLm, self._parameterNode.orbitLm)
        self._parameterNode.initialRigidTransform =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "initial_fiducial_rigid_transform")
        self._parameterNode.initialRigidTransform.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(initial_transform))
        #
        itemIDToClone = shNode.GetItemByDataNode(self._parameterNode.originalPlateLm)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        self._parameterNode.registeredPlateLm = shNode.GetItemDataNode(clonedItemID)
        self._parameterNode.registeredPlateLm.SetName(self._parameterNode.originalPlateLm.GetName() + '_rigid_registered')
        #
        self._parameterNode.registeredPlateLm.SetAndObserveTransformNodeID(self._parameterNode.initialRigidTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.registeredPlateLm)
        #
        itemIDToClone = shNode.GetItemByDataNode(self._parameterNode.originalPlateModel)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        self._parameterNode.rigidRegisteredPlateModel = shNode.GetItemDataNode(clonedItemID)
        self._parameterNode.rigidRegisteredPlateModel.SetName(self._parameterNode.originalPlateModel.GetName() + '_rigid_registered')
        #
        self._parameterNode.rigidRegisteredPlateModel.SetAndObserveTransformNodeID(self._parameterNode.initialRigidTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.rigidRegisteredPlateModel)
        #
        self.ui.inputOrbitModelSelector.enabled = False
        self.ui.orbitFiducialSelector.enabled = False
        self.ui.plateModelSelector.enabled = False
        self.ui.plateFiducialSelector.enabled = False
        self.ui.posteriorStopRegistrationPushButton.enabled = True
        self.ui.resetAllPushButton.enabled = True
        self.ui.finalizePlateRegistrationPushButton.enabled = True
        #
        self._parameterNode.fractureOrbitModel.GetDisplayNode().SetVisibility(True)
        self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(True)
        self._parameterNode.originalPlateLm.GetDisplayNode().SetVisibility(False)
        self._parameterNode.registeredPlateLm.GetDisplayNode().SetVisibility(True)
        self._parameterNode.originalPlateModel.GetDisplayNode().SetVisibility(False)
        self._parameterNode.rigidRegisteredPlateModel.GetDisplayNode().SetVisibility(True)
        #
        #Creat a folder to store results
        dateTimeStamp = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        self.folderNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        sceneItemID = self.folderNode.GetSceneItemID()
        self._parameterNode.plateRegFolderName = self._parameterNode.originalPlateModel.GetName() + "_" + dateTimeStamp
        self.plateRegistrationFolder = self.folderNode.CreateFolderItem(
            sceneItemID, self._parameterNode.plateRegFolderName
        )
        plateModelItem = self.folderNode.GetItemByDataNode(self._parameterNode.rigidRegisteredPlateModel)
        self.folderNode.SetItemParent(plateModelItem, self.plateRegistrationFolder)
        initialTransformItem = self.folderNode.GetItemByDataNode(self._parameterNode.initialRigidTransform)
        self.folderNode.SetItemParent(initialTransformItem, self.plateRegistrationFolder)
        rigidPlateLmItem = self.folderNode.GetItemByDataNode(self._parameterNode.registeredPlateLm)
        self.folderNode.SetItemParent(rigidPlateLmItem, self.plateRegistrationFolder)
        #
        self.ui.initialRegistrationPushButton.enabled = False
        self.ui.placeOrbitLmPushButton.enabled = False
        self.ui.placePlateLmPushButton.enabled = False


    def onRotation_p_stop_pushButton(self):
        logic = plateRegistrationLogic()
        align_p_stop_transform = logic.align_p_stop(self._parameterNode.registeredPlateLm, self._parameterNode.orbitLm)
        print(align_p_stop_transform)
        self._parameterNode.alignPosteriorStopTransform =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "align_p_stop_transform")
        self._parameterNode.alignPosteriorStopTransform.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(align_p_stop_transform))
        # Align at P stop
        self._parameterNode.registeredPlateLm.SetAndObserveTransformNodeID(self._parameterNode.alignPosteriorStopTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.registeredPlateLm)
        self._parameterNode.rigidRegisteredPlateModel .SetAndObserveTransformNodeID(self._parameterNode.alignPosteriorStopTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.rigidRegisteredPlateModel )
        # One more rigid registration rotating around aligned P stop
        p_stop_rotation = logic.rotation_p_stop(self._parameterNode.registeredPlateLm, self._parameterNode.orbitLm)
        print(p_stop_rotation)
        self._parameterNode.pStopRotationTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "p_stop_rotation")
        self._parameterNode.pStopRotationTransform.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(p_stop_rotation))
        #
        self._parameterNode.registeredPlateLm.SetAndObserveTransformNodeID(self._parameterNode.pStopRotationTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.registeredPlateLm)
        self._parameterNode.rigidRegisteredPlateModel.SetAndObserveTransformNodeID(self._parameterNode.pStopRotationTransform.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.rigidRegisteredPlateModel )
        #
        self.ui.interactionTransformCheckbox.enabled = True
        # self.ui.createIntersectButton.enabled = True
        #
        alignPStopTransformItem = self.folderNode.GetItemByDataNode(self._parameterNode.alignPosteriorStopTransform)
        self.folderNode.SetItemParent(alignPStopTransformItem, self.plateRegistrationFolder)
        pstopRotationItem = self.folderNode.GetItemByDataNode(self._parameterNode.pStopRotationTransform)
        self.folderNode.SetItemParent(pstopRotationItem, self.plateRegistrationFolder)
        #
        self.ui.posteriorStopRegistrationPushButton.enabled = False
        #
        self._parameterNode.orbitLm.SetNthControlPointLocked(1, True)        #


    def onInteractionTransform(self):
        if self.ui.interactionTransformCheckbox.isChecked():
            self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(True)
            self._parameterNode.orbitLm.SetNthControlPointVisibility(0, False)
            self._parameterNode.orbitLm.SetNthControlPointVisibility(2, False)
            self._parameterNode.registeredPlateLm.GetDisplayNode().SetVisibility(False)
            #
            self.ui.interactionTransformCheckbox.enabled = False
            self.interactionTransformNode =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "interaction_transform")
            self.interactionTransformNode.CreateDefaultDisplayNodes()
            #
            self.interactionTransformNode.GetDisplayNode().SetEditorVisibility(True) #visualize in 3D and 2D
            #Set center to posterior stop, which is the second lm in the orbit Lm; change it to user input later
            self.interactionTransformNode.SetCenterOfTransformation(self._parameterNode.orbitLm.GetNthControlPointPosition(1))
            #
            self._parameterNode.interactionTransformRecorder = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "interactionTransformRecorder") # record the interaction transform node

            self._parameterNode.interactionTransformRecorder.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
            self.ui.realignHandleToPStopButton.enabled = True
            self.ui.resetToLastStepButton.enabled = True
            self.ui.createIntersectButton.enabled = True
            self.ui.instantHeatMapPushButton.enabled = True
            self.ui.resetAllPushButton.enabled = True
            self.ui.instantCollisionDetectionCheckBox.enabled = True
            self.ui.instantIntersectionMarkerCheckBox.enabled = True
            self.ui.finalizePlateRegistrationPushButton.enabled = True
    
            #remesh plate model to 10k points
            import SurfaceToolbox
            surfaceToolboxLogic = SurfaceToolbox.SurfaceToolboxLogic()
            plateRemeshNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            plateRemeshNode.CreateDefaultDisplayNodes()
            plateRemeshNode.AddDefaultStorageNode()
            surfaceToolboxLogic.remesh(inputModel = self._parameterNode.rigidRegisteredPlateModel, outputModel=plateRemeshNode, subdivide=0, clusters=10000)
            self._parameterNode.interactionPlateModel = plateRemeshNode
            self._parameterNode.interactionPlateModel.SetName(self._parameterNode.originalPlateModel.GetName() + "_interactive_transformed")
            self._parameterNode.rigidRegisteredPlateModel.GetDisplayNode().SetVisibility(False)
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetVisibility(True)
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetVisibility2D(True)
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetColor([0, 0, 1])
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetSliceIntersectionThickness(3)
            self._parameterNode.interactionPlateModel.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())

            #Turn remeshed plate to labelmap and create an ROI fit to it
            segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            segmentationNode.CreateDefaultDisplayNodes()
            segmentationNode.SetName('segmentation_plate_down')
            slicer.modules.segmentations.logic().ImportModelToSegmentationNode(self._parameterNode.interactionPlateModel, segmentationNode)
            segmentationNode.CreateBinaryLabelmapRepresentation()
            outputLabelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
            slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, outputLabelmapVolumeNode)
            self.plateRoiNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
            self.plateRoiNode.CreateDefaultDisplayNodes()
            cropVolumeParameters = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLCropVolumeParametersNode")
            cropVolumeParameters.SetInputVolumeNodeID(outputLabelmapVolumeNode.GetID())
            cropVolumeParameters.SetROINodeID(self.plateRoiNode.GetID())
            slicer.modules.cropvolume.logic().SnapROIToVoxelGrid(cropVolumeParameters)  # optional (rotates the ROI to match the volume axis directions)
            slicer.modules.cropvolume.logic().FitROIToInputVolume(cropVolumeParameters)
            slicer.mrmlScene.RemoveNode(cropVolumeParameters)
            slicer.mrmlScene.RemoveNode(segmentationNode)
            slicer.mrmlScene.RemoveNode(outputLabelmapVolumeNode)
            self.plateRoiNode.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
            self.plateRoiNode.GetDisplayNode().SetVisibility(False)  
            #Add to output folder
            plateRemeshItem = self.folderNode.GetItemByDataNode(self._parameterNode.interactionPlateModel)
            self.folderNode.SetItemParent(plateRemeshItem, self.plateRegistrationFolder)
            interactionTransformItem = self.folderNode.GetItemByDataNode(self.interactionTransformNode)
            self.folderNode.SetItemParent(interactionTransformItem, self.plateRegistrationFolder)
            fullTransformItem = self.folderNode.GetItemByDataNode(self._parameterNode.interactionTransformRecorder)
            self.folderNode.SetItemParent(fullTransformItem, self.plateRegistrationFolder)
            plateRoiItem = self.folderNode.GetItemByDataNode(self.plateRoiNode)
            self.folderNode.SetItemParent(plateRoiItem, self.plateRegistrationFolder)
            #
            #Connect to the timer
            try:
                self.interactionTransformNode.RemoveObserver(observerTag1)
            except:
                pass
            observerTag1 = self.interactionTransformNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.executeTimer)
        else:
            pass

    def timerFunction(self):
        self.timer.start()

    def executeTimer(self, caller, eventid):
        # print("found event")
        self.timerFunction()
        #When modifier the transform, update timer

    def timeout(self):
        self._parameterNode.interactionPlateModel.GetDisplayNode().SetScalarVisibility(False)
        try:
            slicer.mrmlScene.RemoveNode(self.orbitModelCropped)
        except:
            pass
        try:
            slicer.mrmlScene.RemoveNode(self.intersectionModel)
        except:
            pass
        logic = plateRegistrationLogic()
        print("timeout")
        if self.ui.instantCollisionDetectionCheckBox.isChecked():
            # Computer instant collision number of points
            self.ui.collisionInfoBox.clear
            collisionFlag, numberOfCollisions = logic.collision_detection(self._parameterNode.interactionPlateModel, self._parameterNode.fractureOrbitModel)
            if collisionFlag == False:
                self.ui.collisionInfoBox.insertPlainText(
                  f":: No collision detected. \n"
                )
            else:
                self.ui.collisionInfoBox.insertPlainText(f"{numberOfCollisions} collision points detected. This is approximately {numberOfCollisions/100} % of all points in the plate. \n")
                print(f"{numberOfCollisions} collision points detected. This is approximately {numberOfCollisions/10000}% of points in the plate.")
        
        elif self.ui.instantIntersectionMarkerCheckBox.isChecked():
            #
            #Instant probe model by volume for marking intersection
            try:
                slicer.mrmlScene.RemoveNode(self.orbitModelCropped)
            except:
                pass
            #Crop volume with ROI
            #clone the self.plateRoiNode, add to interaction transform & harden the transform
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            itemIDToClone = shNode.GetItemByDataNode(self.plateRoiNode)
            clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
            plateRoiNode_clone = shNode.GetItemDataNode(clonedItemID)
            plateRoiNode_clone.SetName('plateRoiNode_clone')
            plateRoiNode_clone.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(plateRoiNode_clone)

            #Create ROI cut from Dynamic Modeler
            roiCutTool = slicer.vtkSlicerDynamicModelerROICutTool()
        
            self.orbitModelCropped = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            self.orbitModelCropped.SetName("orbit_cropped")
            self.orbitModelCropped.CreateDefaultDisplayNodes()
            self._parameterNode.interactionPlateModel.AddDefaultStorageNode()
        
            dynamicModelerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLDynamicModelerNode")
            dynamicModelerNode.SetToolName("ROI cut")
            self._parameterNode.fractureOrbitModel.GetDisplayNode().SetOpacity(0.6)
            dynamicModelerNode.SetNodeReferenceID("ROICut.InputModel", self._parameterNode.fractureOrbitModel.GetID())
            dynamicModelerNode.SetNodeReferenceID("ROICut.InputROI", plateRoiNode_clone.GetID())
            dynamicModelerNode.SetNodeReferenceID("ROICut.OutputPositiveModel", self.orbitModelCropped.GetID())
            slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
            plateRoiNode_clone.GetDisplayNode().SetVisibility(False)
            slicer.mrmlScene.RemoveNode(dynamicModelerNode)
            slicer.mrmlScene.RemoveNode(plateRoiNode_clone)
        
            #remesh cropped orbit
            self.orbitModelCropped.GetDisplayNode().SetVisibility(True)
            orbitModelCroppedItem = self.folderNode.GetItemByDataNode(self.orbitModelCropped)
            self.folderNode.SetItemParent(orbitModelCroppedItem, self.plateRegistrationFolder)

            #create plate color marker using probe volume from model
            #Harden plate remesh node
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionPlateModel)
            #Turn the hardened plate into segmentation node
            plateSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            plateSegmentationNode.CreateDefaultDisplayNodes()
            slicer.modules.segmentations.logic().ImportModelToSegmentationNode(self._parameterNode.interactionPlateModel, plateSegmentationNode)

            orbitSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            orbitSegmentationNode.CreateDefaultDisplayNodes()
            slicer.modules.segmentations.logic().ImportModelToSegmentationNode(self._parameterNode.fractureOrbitModel,orbitSegmentationNode)
            
            #First paint the plate by setting the cropped orbit segmentaton as the master volume
            logic.paint_model_by_volume(orbitSegmentationNode, self._parameterNode.interactionPlateModel, self._parameterNode.interactionPlateModel)

            d = self._parameterNode.interactionPlateModel.GetDisplayNode()
            d.SetScalarVisibility(True)
            d.SetActiveScalarName('NRRDImage')
            colorTableNode = slicer.util.getNode('Plasma')
            d.SetAndObserveColorNodeID(colorTableNode.GetID())
            
            #Clone current interaction transform and inverse it (hardened in paint_model_by_volume)
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            itemIDToClone = shNode.GetItemByDataNode(self.interactionTransformNode)
            clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
            interactionTransform_inverse = shNode.GetItemDataNode(clonedItemID)
            interactionTransform_inverse.SetName('interactionTransform_inverse')
            interactionTransform_inverse.Inverse()
            #
            #Inverse transform the plateRemesh node and add back to interaction transform
            self._parameterNode.interactionPlateModel.SetAndObserveTransformNodeID(interactionTransform_inverse.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionPlateModel)
            self._parameterNode.interactionPlateModel.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
            slicer.mrmlScene.RemoveNode(interactionTransform_inverse)
            #remove plateRemeshNode
            #
            #Paint cropped orbit model node by plate segmentation node
            #First grow the margin of the plate segmentation by 0.75mm
            #
            #Create segment editor to get access to effects
            segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
            segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
            segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
            segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
            segmentEditorWidget.setSegmentationNode(plateSegmentationNode)
            #
            plateSegID = plateSegmentationNode.GetSegmentation().GetSegmentIDs()[0]
            segmentEditorWidget.setActiveEffectByName("Margin")
            effect = segmentEditorWidget.activeEffect()
            effect.setParameter("MarginSizeMm", 0.75)
            segmentEditorNode.SetSelectedSegmentID(plateSegID)
            effect.self().onApply()
            #
            logic.paint_model_by_volume(plateSegmentationNode, self.orbitModelCropped, self.orbitModelCropped)
            d = self.orbitModelCropped.GetDisplayNode()
            d.SetScalarVisibility(True)
            d.SetActiveScalarName('NRRDImage')
            colorTableNode = slicer.util.getNode('Viridis')
            d.SetAndObserveColorNodeID(colorTableNode.GetID())
            d.SetScalarRangeFlagFromString('Manual')
            d.SetThresholdEnabled(True)
            d.SetThresholdRange(0.01, 1)
            #
            #Remove segmentation node
            slicer.mrmlScene.RemoveNode(plateSegmentationNode)
            slicer.mrmlScene.RemoveNode(orbitSegmentationNode)
        else:
            pass

    def onCreateIntersectButton(self):
        self.ui.interactionTransformCheckbox.enabled = False
        logic = plateRegistrationLogic()
        try:
            slicer.mrmlScene.RemoveNode(self.intersectionModel)
        except:
            pass
        # clone plate remesh
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self._parameterNode.interactionPlateModel)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        plateRemeshNode_clone = shNode.GetItemDataNode(clonedItemID)

        # Add to interaction transform and harden it
        plateRemeshNode_clone.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(plateRemeshNode_clone)
        #
        collisionFlag, numberOfCollisions = logic.collision_detection(plateRemeshNode_clone, self._parameterNode.fractureOrbitModel)
        # output information
        self.ui.collisionInfoBox.clear
        if collisionFlag == True:
            self.ui.collisionInfoBox.insertPlainText(
                f":: Collision between model and plate detected. There are {numberOfCollisions} collision points. This is approximately {numberOfCollisions/100} % of points in the plate. \n"
            )
            intersector = logic.intersection_marker(plateRemeshNode_clone, self._parameterNode.fractureOrbitModel)
            self.intersectionModel = slicer.modules.models.logic().AddModel(intersector.GetOutputDataObject(0))
            self.intersectionModel.SetName("intersectionModel_0")
            yellow = [1.0, 1.0, 0]
            self.intersectionModel.GetDisplayNode().SetColor(yellow)
            self.intersectionModel.GetDisplayNode().SetVisibility2D(True)
            self.intersectionModel.GetDisplayNode().SetSliceIntersectionThickness(7)
            intersectionModelItem = self.folderNode.GetItemByDataNode(self.intersectionModel)
            self.folderNode.SetItemParent(intersectionModelItem, self.plateRegistrationFolder)
        else:
            self.ui.collisionInfoBox.insertPlainText(
                f":: No collision detected. \n"
            )
        # Remove nodes
        slicer.mrmlScene.RemoveNode(plateRemeshNode_clone)



    def onInstantHeatMap(self):
        logic = plateRegistrationLogic()
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionPlateModel)
        plate_distanceMap2, self._parameterNode.interactionPlateModel = logic.heatmap(templateMesh=self._parameterNode.interactionPlateModel,
                                                                 currentMesh=self._parameterNode.fractureOrbitModel)
        d = self._parameterNode.interactionPlateModel.GetDisplayNode()
        d.SetScalarVisibility(True)
        d.SetActiveScalarName('Distance')
        colorTableNode = slicer.util.getNode('RedGreenBlue')
        d.SetAndObserveColorNodeID(colorTableNode.GetID())
        d.SetScalarRangeFlagFromString('Manual')
        d.SetScalarRange(0, 5)

        # Clone current interaction transform and inverse it (hardened in paint_model_by_volume)
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self.interactionTransformNode)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        interactionTransform_inverse = shNode.GetItemDataNode(clonedItemID)
        interactionTransform_inverse.SetName('interactionTransform_inverse')
        interactionTransform_inverse.Inverse()
        #
        # Inverse transform the plateRemesh node and add back to interaction transform
        self._parameterNode.interactionPlateModel.SetAndObserveTransformNodeID(interactionTransform_inverse.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionPlateModel)
        self._parameterNode.interactionPlateModel.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
        slicer.mrmlScene.RemoveNode(interactionTransform_inverse)




    def onRealignHandleToPStopButton(self):
        # Clone orbit lm
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        itemIDToClone = shNode.GetItemByDataNode(self._parameterNode.orbitLm)
        clonedItemID = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(shNode, itemIDToClone)
        orbitLmCloneNode = shNode.GetItemDataNode(clonedItemID)
        orbitLmCloneNode.SetName('orbit_lm_cloned')
        orbitLmCloneNode.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(orbitLmCloneNode)
        
        p_stop_source = [0, 0, 0]
        orbitLmCloneNode.GetNthControlPointPosition(1, p_stop_source)
        
        p_stop_target = [0, 0, 0 ]
        self._parameterNode.orbitLm.GetNthControlPointPosition(1, p_stop_target)
        
        translation = np.subtract(p_stop_target, p_stop_source)
        
        # homogeneous transformation
        realignPStopTransform = np.identity(4)
        realignPStopTransform[:3, 3] = translation
        
        realignPStopTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "realignPStopTransform")
        realignPStopTransformNode.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(realignPStopTransform))

        self.interactionTransformNode.SetAndObserveTransformNodeID(realignPStopTransformNode.GetID())
        slicer.vtkSlicerTransformLogic().hardenTransform(self.interactionTransformNode)
        
        slicer.mrmlScene.RemoveNode(realignPStopTransformNode)
        slicer.mrmlScene.RemoveNode(orbitLmCloneNode)



    def onResetToLastStepButton(self):
        transformMatrix = vtk.vtkMatrix4x4() #identiy matrix
        self.interactionTransformNode.SetMatrixTransformToParent(transformMatrix)



    def onResetAllPushButton(self):
        #
        self.ui.inputOrbitModelSelector.enabled=True
        self.ui.orbitFiducialSelector.enabled=True
        self.ui.plateModelSelector.enabled=True
        self.ui.plateFiducialSelector.enabled=True
        #
        self.ui.interactionTransformCheckbox.checked=0
        self.ui.interactionTransformCheckbox.enabled=False
        self.ui.instantCollisionDetectionCheckBox.checked=0
        self.ui.instantCollisionDetectionCheckBox.enabled=False
        self.ui.instantIntersectionMarkerCheckBox.checked=0
        self.ui.instantIntersectionMarkerCheckBox.enabled=False
        self.ui.createIntersectButton.enabled=False
        self.ui.instantHeatMapPushButton.enabled=False
        self.ui.realignHandleToPStopButton.enabled=False
        self.ui.resetToLastStepButton.enabled=False
        self.ui.resetAllPushButton.enabled=False
        self.ui.finalizePlateRegistrationPushButton.enabled = False
        self.ui.placeOrbitLmPushButton.enabled = False
        #
        self._parameterNode.orbitLm.SetNthControlPointVisibility(0, True)
        self._parameterNode.orbitLm.SetNthControlPointVisibility(1, True)
        self._parameterNode.orbitLm.SetNthControlPointVisibility(2, True)
        self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(True)
        self._parameterNode.orbitLm.SetNthControlPointLocked(1, False)
        self._parameterNode.fractureOrbitModel.GetDisplayNode().SetVisibility(True)
        self._parameterNode.originalPlateLm.GetDisplayNode().SetVisibility(True)
        self._parameterNode.originalPlateModel.GetDisplayNode().SetVisibility(True)
        # # Loop through children and remove each data node
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        children = vtk.vtkIdList()
        shNode.GetItemChildren(self.plateRegistrationFolder, children)
        for i in range(children.GetNumberOfIds()):
            childItemID = children.GetId(i)
            dataNode = shNode.GetItemDataNode(childItemID)
            if dataNode:
                slicer.mrmlScene.RemoveNode(dataNode)
        # Remove the empty folder
        shNode.RemoveItem(self.plateRegistrationFolder)
        #
        # self._parameterNode.rigidRegisteredPlateModel.GetDisplayNode().SetVisibility(False)
        self.ui.inputOrbitModelSelector.clearSelection()
        self.ui.orbitFiducialSelector.clearSelection()
        self.ui.plateModelSelector.clearSelection()
        self.ui.plateFiducialSelector.clearSelection()
        #
        self.ui.currentRegResultsPathLineEdit.setCurrentPath("")
        self.ui.currentRegResultsPathLineEdit.enabled = False
        self.onCurrentRegResultsPathLineEdit()



    def onFinalizePlateRegistrationPushButton(self):
        # Get display node IDs
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        interactionFlag = self.ui.interactionTransformCheckbox.checked
        if interactionFlag == 1:
            self.interactionTransformNode.GetDisplayNode().SetEditorVisibility(False)
            interactionPlateId = shNode.GetItemByDataNode(self._parameterNode.interactionPlateModel)
        else:
            rigidPlateModelId = shNode.GetItemByDataNode(self._parameterNode.rigidRegisteredPlateModel)
            print("no interaction transform performed")
        orbitModelId = shNode.GetItemByDataNode(self._parameterNode.fractureOrbitModel)
        #
        slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionPlateModel)
        allTransformNodeName = "allTransform_" + self._parameterNode.originalPlateModel.GetName()
        self._parameterNode.allTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', allTransformNodeName)
        try:
            self._parameterNode.allTransformNode.SetAndObserveTransformNodeID(self._parameterNode.initialRigidTransform.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.allTransformNode)
            self._parameterNode.allTransformNode.SetAndObserveTransformNodeID(self._parameterNode.alignPosteriorStopTransform.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.allTransformNode)
            self._parameterNode.allTransformNode.SetAndObserveTransformNodeID(self._parameterNode.pStopRotationTransform.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.allTransformNode)
            self._parameterNode.allTransformNode.SetAndObserveTransformNodeID(self.interactionTransformNode.GetID())
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.allTransformNode)
        except (AttributeError, ValueError, TypeError):
            pass
        allTransformNodeItem = self.folderNode.GetItemByDataNode(self._parameterNode.allTransformNode)
        self.folderNode.SetItemParent(allTransformNodeItem, self.plateRegistrationFolder)
        #
        if self._parameterNode.interactionTransformRecorder:
            slicer.vtkSlicerTransformLogic().hardenTransform(self._parameterNode.interactionTransformRecorder)
        else:
            pass
        #
        print(f"Registration data stored in the folder {self._parameterNode.plateRegFolderName}.")
        #
        try:
            registeredPlateInfoDict = json.loads(self._parameterNode.registeredPlateInfoJSON)
        except (AttributeError, ValueError, TypeError):
            registeredPlateInfoDict = {}
        #
        if interactionFlag == 1:
            registeredPlateInfoDict[self._parameterNode.plateRegFolderName] = {
                "finalPlateModelNodeID": self._parameterNode.interactionPlateModel.GetID(),
                "fullTransformNodeID": self._parameterNode.allTransformNode.GetID(),
                "folderItemID": self._parameterNode.plateRegFolderName
            }
        else:
            registeredPlateInfoDict[self._parameterNode.plateRegFolderName] = {
                "finalPlateModelNodeID": self._parameterNode.rigidRegisteredPlateModel.GetID(),
                "fullTransformNodeID": self._parameterNode.allTransformNode.GetID(),
                "folderItemID": self._parameterNode.plateRegFolderName
            }
        self._parameterNode.registeredPlateInfoJSON = json.dumps(registeredPlateInfoDict) #flatten into JSON
        #
        dict_keys = registeredPlateInfoDict.keys()
        print(f"registered plate keys are {dict_keys}")
        #
        self.ui.interactionTransformCheckbox.checked=0
        self.ui.interactionTransformCheckbox.enabled=False
        self.ui.instantCollisionDetectionCheckBox.checked=0
        self.ui.instantCollisionDetectionCheckBox.enabled=False        
        self.ui.instantIntersectionMarkerCheckBox.checked=0
        self.ui.instantIntersectionMarkerCheckBox.enabled=False
        self.ui.createIntersectButton.enabled=False
        self.ui.instantHeatMapPushButton.enabled=False
        self.ui.realignHandleToPStopButton.enabled=False
        self.ui.resetToLastStepButton.enabled=False
        self.ui.resetAllPushButton.enabled=False
        self.ui.finalizePlateRegistrationPushButton.enabled = False
        self.ui.currentRegResultsPathLineEdit.enabled = True
        #
        #
        self.ui.inputOrbitModelSelector.enabled = True
        self.ui.orbitFiducialSelector.enabled = True
        self.ui.plateModelSelector.enabled = True
        self.ui.plateFiducialSelector.enabled = True
        #
        self._parameterNode.orbitLm.SetNthControlPointVisibility(0, True)
        self._parameterNode.orbitLm.SetNthControlPointVisibility(1, True)
        self._parameterNode.orbitLm.SetNthControlPointVisibility(2, True)
        self._parameterNode.orbitLm.GetDisplayNode().SetVisibility(False)
        self._parameterNode.orbitLm.SetNthControlPointLocked(1, False)
        self._parameterNode.registeredPlateLm.GetDisplayNode().SetVisibility(False)
        #
        try:
            slicer.mrmlScene.RemoveNode(self.orbitModelCropped)
        except (AttributeError, ValueError, TypeError):
            pass
        try:
            slicer.mrmlScene.RemoveNode(self.intersectionModel)
        except (AttributeError, ValueError, TypeError):
            pass

        self.ui.inputOrbitModelSelector.clearSelection()
        self.ui.orbitFiducialSelector.clearSelection()
        self.ui.plateModelSelector.clearSelection()
        self.ui.plateFiducialSelector.clearSelection()

        self._parameterNode.fractureOrbitModel = shNode.GetItemDataNode(orbitModelId)
        self._parameterNode.fractureOrbitModel.GetDisplayNode().SetVisibility(True)
        if interactionFlag == 1:
            self._parameterNode.interactionPlateModel = shNode.GetItemDataNode(interactionPlateId)
            self._parameterNode.interactionPlateModel.GetDisplayNode().SetVisibility(True)
        else:
            self._parameterNode.rigidRegisteredPlateModel = shNode.GetItemDataNode(rigidPlateModelId)
            self._parameterNode.rigidRegisteredPlateModel.GetDisplayNode().SetVisibility(True)

    def onSaveCurrentRegPushButton(self):
        import os
        logic = plateRegistrationLogic()
        resultsFolderName = self._parameterNode.plateRegFolderName
        outputPath = self.ui.currentRegResultsPathLineEdit.currentPath
        outputFolder = os.path.join(outputPath, resultsFolderName)
        slicer.app.ioManager().addDefaultStorageNodes()
        logic.exportCurrentFolder(self.plateRegistrationFolder, outputFolder)
        self.ui.currentRegResultsPathLineEdit.setCurrentPath("")
        self.onCurrentRegResultsPathLineEdit()
        self.ui.currentRegResultsPathLineEdit.enabled = False


    def onPlateHeatmap(self):
        self.plateModelNode2 = self.ui.plateModelSelector2.currentNode()
        self.orbitReconModelNode = self.ui.orbitModelSelector2.currentNode()
        logic = plateRegistrationLogic()
        plate_distanceMap2, self.plateModelNode2=logic.heatmap(templateMesh = self.plateModelNode2, currentMesh = self.orbitReconModelNode)

        d = self.plateModelNode2.GetDisplayNode()
        d.SetScalarVisibility(True)
        d.SetActiveScalarName('Distance')
        colorTableNode = slicer.util.getNode('RedGreenBlue')
        d.SetAndObserveColorNodeID(colorTableNode.GetID())
        d.SetScalarRangeFlagFromString('Manual')
        d.SetScalarRange(0, 5)
        
        scalarArray = slicer.util.arrayFromModelPointData(self.plateModelNode2, 'Distance')
        scalarArray = np.abs(scalarArray)
        outputDir = self.ui.fitnessOutoutDir.currentPath
        logic.plotScalarHistogram(scalarArray, outputDir)
        

    def onProjectPoints(self):
        #
        logic = plateRegistrationLogic()
        import os
        plateLMDir = self.ui.fitnessInputDir.currentPath
        alignedPlateModelNode = self.ui.plateModelSelector2.currentNode()
        orbitReconModelNode = self.ui.orbitModelSelector2.currentNode()
        allTransformNode = self.ui.plateTransformSelector.currentNode()
        #
        #Create folder to store results
        self.fitfolderNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        sceneItemID = self.fitfolderNode.GetSceneItemID()
        self.plateFitFolder = self.fitfolderNode.CreateFolderItem(
            sceneItemID, self.ui.plateModelSelector2.currentNode().GetName() + "_projected_lm"
        )
        #
        # for dir in plateLMSubdir:
        #     if os.path.isdir(os.path.join(plateLMRootPath, dir)):
        #         outputRoot = slicer.ui.fitnessOutoutDir.currentPath()
        #         subDirName = dir + "_projected_lm"
        #Set up output folder name
        outputRoot = self.ui.fitnessOutoutDir.currentPath
        subDirName = os.path.basename(plateLMDir) + "_projected_lm"
        outputSubDir = os.path.join(outputRoot, subDirName)
        os.mkdir(outputSubDir)
        
        for file in os.listdir(plateLMDir):
            if file.endswith((".json", ".fcsv")):
                self.plateBoundaryLMNode = slicer.util.loadMarkups(os.path.join(plateLMDir, file))
                self.plateBoundaryLMNode.SetAndObserveTransformNodeID(allTransformNode.GetID())
                slicer.vtkSlicerTransformLogic().hardenTransform(self.plateBoundaryLMNode)
                self.projectedPlateLMNode = logic.projectPoints(
                    sourceLMNode = self.plateBoundaryLMNode, 
                    sourceModel=alignedPlateModelNode, 
                    targetModel=orbitReconModelNode
                )
                self.projectedPlateLMNode.SetName(self.plateBoundaryLMNode.GetName()+"_projected_to_orbit")
                #Put original and projected lm in a folder
                plateBoundaryLMItem = self.fitfolderNode.GetItemByDataNode(self.plateBoundaryLMNode)
                self.fitfolderNode.SetItemParent(plateBoundaryLMItem, self.plateFitFolder)
                projectedPlateLMItem = self.fitfolderNode.GetItemByDataNode(self.projectedPlateLMNode)
                self.fitfolderNode.SetItemParent(projectedPlateLMItem, self.plateFitFolder)                        
                #
                #Save node
                outputFilePath = os.path.join(outputSubDir, self.plateBoundaryLMNode.GetName()+"_aligned.mrk.json")
                slicer.util.saveNode(self.plateBoundaryLMNode, outputFilePath)
                outputFilePath = os.path.join(outputSubDir, self.plateBoundaryLMNode.GetName()+"_projected_to_orbit.mrk.json")
                slicer.util.saveNode(self.projectedPlateLMNode, outputFilePath)
        return



    
    def onCompareFitness(self):
        #Retrieve files from the output root
        import os
        projectLMOutputRoot = self.ui.fitnessOutoutDir.currentPath
        print("projectLMOutputRoot")
        # dirList = os.listdir(projectLMOutputRoot)
        dirList = [item for item in os.listdir(projectLMOutputRoot) if os.path.isdir(os.path.join(projectLMOutputRoot, item))]
        print(f"dirlist is {dirList}")
        if len(dirList) < 1:
            logging.error('No folders for computing plate fitness. Project the landmarks first')
            return
        allLMData = []
        allLMNames = []
        for folder in dirList:
            #store each metric in a list of fidual array
            subfolderPath = os.path.join(projectLMOutputRoot, folder)
            for file in os.listdir(subfolderPath):
                if file.endswith((".fscv", ".json")):
                    lmNode = slicer.util.loadMarkups(os.path.join(subfolderPath, file))
                    lm = np.zeros(shape=(lmNode.GetNumberOfControlPoints(), 3))
                    point = [0, 0, 0]
                    for i in range(lmNode.GetNumberOfControlPoints()):
                        lmNode.GetNthControlPointPosition(i, point)
                        lm[i, :] = point
                    allLMData.append(lm)
                    allLMNames.append(os.path.basename(file))
                    slicer.mrmlScene.RemoveNode(lmNode)
        allEdgeDists = []
        meanEdgeDistsList = []
        counters = [x for x in range(len(allLMData)-1) if x % 2 == 0]
        for i in counters:
            edgeLm = allLMData[i]
            edgeLmProj = allLMData[i+1]
            edgeLm_dist = np.sqrt(np.sum(np.square(edgeLm-edgeLmProj), axis = 1))
            allEdgeDists.append(edgeLm_dist)
            meanEdgeDistsList.append(np.mean(edgeLm_dist))
        #
        setsNum = len(dirList)
        print(f"allLMNames are {allLMNames}")
        print(f"setsNum is {setsNum}")
        variableNum = int(len(allEdgeDists)/setsNum)
        print(f"variableNum is {variableNum}")
        allEdgeDistsArr = np.reshape(allEdgeDists, (setsNum, variableNum, edgeLm.shape[0]))
        print(allEdgeDistsArr)
        meanEdgeDistsArr = np.reshape(meanEdgeDistsList, (setsNum, variableNum))
        print(meanEdgeDistsArr)
        #ranking
        rankArray = np.zeros(shape = meanEdgeDistsArr.shape)
        for i in range(meanEdgeDistsArr.shape[1]):
            rankArray[:, i] = [sorted(meanEdgeDistsArr[:, i]).index(j) for j in meanEdgeDistsArr[:, i]]
        #Overall ranking
        rankScoreSum = np.sum(rankArray, axis = 1)
        plateRanks = [sorted(rankScoreSum).index(j) for j in rankScoreSum]
        print(rankArray)
        print(rankScoreSum)
        print(plateRanks)
        
        self.ui.fitnessRankInfoBox.clear
        self.ui.fitnessRankInfoBox.insertPlainText(
          f":: The ranks of plate fitness are. \n"
        )
        # self.ui.fitnessRankInfoBox.insertPlainText(
        #   f":: {}The ranks of plate fitness are. \n"
        # )
        for i in range(len(dirList)):
            self.ui.fitnessRankInfoBox.insertPlainText(
              f":: {dirList[i]}: rank {plateRanks[i]+1}. \n"
            )
        
        #plot mean distance
        # makeScatterPlotWithFactors(
        # self, dataArray, factors, title, xAxisName, yAxisName, subjectID
        # ):
        
        logic = plateRegistrationLogic()
        namesCounter = [x for x in range(len(allLMNames)-1) if x % 2 == 0]
        measurementNames = [allLMNames[i] for i in namesCounter]
        measurementNames = np.array_split(measurementNames, setsNum)
        meanPlotTitle = "Mean distances plot"
        
        #Matplot lib
        xLabel = "Plate margins"
        logic.matplotlibScatterPlot(meanEdgeDistsArr, dirList, meanPlotTitle, xLabel, projectLMOutputRoot)

        #Plot mean distances in Slicer
        meanDistsScatterPlot = logic.makeScatterPlotWithFactors(
            meanEdgeDistsArr, dirList, meanPlotTitle, "Measurements", "Distances(mm)", measurementNames
            )
        
        # Switch to a Slicer layout that contains a plot view for plotwidget
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(503)
        
        slicer.modules.plots.logic().ShowChartInLayout(meanDistsScatterPlot)

        plotWidget = layoutManager.plotWidget(0)
        plotViewNode = plotWidget.mrmlPlotViewNode()
        plotViewNode.SetPlotChartNodeID(meanDistsScatterPlot.GetID())
        

        #Plot each plate margin distance in allEdgeDistsArr
        #The shape is (setsNum, variableNum, edgeLm.shape[0])
        for i in range(variableNum):
            marginDistsArray = np.zeros(shape = (setsNum, edgeLm.shape[0]))
            for j in range(setsNum):
                marginDistsArray[j, :] = allEdgeDistsArr[j, i, :]

                marginPlotTilte = "plate_margin_" + str(i+1) + "_dists_to_orbit"
                xLabel = "Points"
                logic.matplotlibScatterPlot(marginDistsArray, dirList, marginPlotTilte, xLabel, projectLMOutputRoot)

        return


#
# plateRegistrationLogic
#


class plateRegistrationLogic(ScriptedLoadableModuleLogic):
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
        return plateRegistrationParameterNode(super().getParameterNode())

    def placeLm(self, lmNode):
        lmNodeId = lmNode.GetID()
        #
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeID(lmNodeId)
        interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        placeModePersistence = 0
        #
        interactionNode.SetPlaceModePersistence(placeModePersistence)
        # mode 1 is Place, can also be accessed via slicer.vtkMRMLInteractionNode().Place
        interactionNode.SetCurrentInteractionMode(1)



    def rigid_transform(self, source_lm_node, target_lm_node):
        source_points = np.zeros(shape=(source_lm_node.GetNumberOfControlPoints(), 3))
        target_points = np.zeros(shape=(target_lm_node.GetNumberOfControlPoints(), 3))
        
        m = source_points.shape[1]
        
        point = [0, 0, 0]
        
        for i in range(source_lm_node.GetNumberOfControlPoints()):
            source_lm_node.GetNthControlPointPosition(i, point)
            source_points[i, :] = point
            # subjectFiducial.SetNthControlPointLocked(i, 1)
            target_lm_node.GetNthControlPointPosition(i, point)
            target_points[i, :] = point

        
        points_number = source_points.shape[1]
        
        #translate points to centroids
        source_centroid = np.mean(source_points, axis = 0)
        target_centroid = np.mean(target_points, axis = 0)
        source_centered_points = source_points - source_centroid
        target_centered_points = target_points - target_centroid
        
        #transformation matrix
        # Perform singular value decomposition (SVD)
        U, _, Vt = np.linalg.svd(source_centered_points.T @ target_centered_points, full_matrices=False)
        
        # Calculate the optimal rotation matrix
        rotation_matrix = Vt.T @ U.T
        
        # special reflection case
        if np.linalg.det(rotation_matrix) < 0:
            Vt[m - 1, :] *= -1
        rotation_matrix = np.dot(Vt.T, U.T)
        
        #translation
        t = target_centroid.T - np.dot(rotation_matrix, source_centroid.T)
        
        # homogeneous transformation matrix
        T = np.identity(4)
        T[:3, :3] = rotation_matrix
        T[:3, 3] = t
        
        # rotationTransformNode =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "svd_rotation_transform")
        # rotationTransformNode.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(T))
        
        return T

    
    def align_p_stop(self, source_node, target_node):
        p_stop_source = [0, 0, 0]
        source_node.GetNthControlPointPosition(1, p_stop_source)
        
        p_stop_target = [0, 0, 0 ]
        target_node.GetNthControlPointPosition(1, p_stop_target)
        
        translation = np.subtract(p_stop_target, p_stop_source)
        
        # homogeneous transformation
        T = np.identity(4)
        T[:3, 3] = translation
        
        print(T)
        
        return T

    
    
    def rotation_p_stop(self, source_node, target_node):

        source_points = np.zeros(shape=(source_node.GetNumberOfControlPoints(), 3))
        target_points = np.zeros(shape=(target_node.GetNumberOfControlPoints(), 3))
        
        m = source_points.shape[1]
        
        point = [0, 0, 0]
        
        for i in range(source_node.GetNumberOfControlPoints()):
          source_node.GetNthControlPointPosition(i, point)
          source_points[i, :] = point
          # subjectFiducial.SetNthControlPointLocked(i, 1)
          target_node.GetNthControlPointPosition(i, point)
          target_points[i, :] = point
        
        # Define the point around which you want to rotate
        rotation_center = target_points[1, :] # Specify the center point as the posterior stop
        
        # Calculate the translation to bring the rotation center to the origin
        translation = -rotation_center
        
        # Translate both the source and target point sets
        translated_source_points = source_points + translation
        translated_target_points = target_points + translation
        
        # Perform singular value decomposition (SVD)
        U, _, Vt = np.linalg.svd(translated_source_points.T @ translated_target_points, full_matrices=False)
        
        
        # Calculate the optimal rotation matrix
        rotation_matrix = Vt.T @ U.T
        
        # special reflection case
        m = translated_source_points.shape[1]
        if np.linalg.det(rotation_matrix) < 0:
            Vt[m - 1, :] *= -1
        rotation_matrix = np.dot(Vt.T, U.T)
        
        #translation
        t = rotation_center.T - np.dot(rotation_matrix, rotation_center.T)
        
        # homogeneous transformation
        T = np.identity(4)
        T[:3, :3] = rotation_matrix
        T[:3, 3] = t
        
        # rotationTransformNode =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode', "svd_rotation_transform")
        # rotationTransformNode.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(T))
        
        return T

    
    def collision_detection(self, modelNode1, modelNode2):
        # Variables
        collisionDetection = vtk.vtkCollisionDetectionFilter()
        numberOfCollisions = 0
        collisionFlag = False
        # Collision Detection
        node1ToWorldTransformMatrix = vtk.vtkMatrix4x4()
        node2ToWorldTransformMatrix = vtk.vtkMatrix4x4()
        node1ParentTransformNode = modelNode1.GetParentTransformNode()
        node2ParentTransformNode = modelNode2.GetParentTransformNode()
        if node1ParentTransformNode != None:
            node1ParentTransformNode.GetMatrixTransformToWorld(node1ToWorldTransformMatrix)
        if node2ParentTransformNode != None:
            node2ParentTransformNode.GetMatrixTransformToWorld(node2ToWorldTransformMatrix)
        #
        collisionDetection.SetInputData( 0, modelNode1.GetPolyData() )
        collisionDetection.SetInputData( 1, modelNode2.GetPolyData() )
        collisionDetection.SetMatrix( 0, node1ToWorldTransformMatrix )
        collisionDetection.SetMatrix( 1, node2ToWorldTransformMatrix )
        collisionDetection.SetBoxTolerance( 0.0 )
        collisionDetection.SetCellTolerance( 0.0 )
        collisionDetection.SetNumberOfCellsPerNode( 2 )
        collisionDetection.Update()
        #
        numberOfCollisions      = collisionDetection.GetNumberOfContacts()
        if numberOfCollisions > 0:
            collisionFlag       = True
        else:
            collisionFlag       = False
        return collisionFlag, numberOfCollisions
      

    def heatmap(self, templateMesh, currentMesh):
        distanceFilter = vtk.vtkDistancePolyDataFilter()
        distanceFilter.SetInputData(0,templateMesh.GetPolyData())
        distanceFilter.SetInputData(1,currentMesh.GetPolyData())
        # distanceFilter.SetSignedDistance(signedDistanceOption)
        distanceFilter.SignedDistanceOn()
        # distanceFilter.SignedDistanceOn()
        distanceFilter.Update()
        
        distanceMap = distanceFilter.GetOutput()
        distanceArray = distanceMap.GetPointData().GetArray('Distance')
        #meanDistance = np.average(distanceArray)
        # meanDistance = self.rmse(distanceArray)
        # outputNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode","ouputDistanceMap")
        templateMesh.SetAndObservePolyData(distanceMap)
        return distanceMap, templateMesh



    def intersection_marker(self, plate_model_node, orbit_model_node):
        intersector = vtk.vtkIntersectionPolyDataFilter()
        intersector.SetInputConnection(0,plate_model_node.GetPolyDataConnection())
        intersector.SetInputConnection(1, orbit_model_node.GetPolyDataConnection())
        intersector.Update()

        # intersectionModel = slicer.modules.models.logic().AddModel(intersector.GetOutputDataObject(0))
        # intersectionModel.SetName("intersectionModel_0")
        # intersectionModel.GetDisplayNode().SetColor(0.0, 0.0, 1.0)
        
        return intersector


    def paint_model_by_volume(self, masterVolumeNode, InputModelNode, outputModelNode):
        #segmentationNode contains plate and orbit segments
        #Use Probe Volume with Model
        # outputModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        parameters = {}
        parameters['InputVolume'] = masterVolumeNode.GetID()
        parameters['InputModel'] = InputModelNode.GetID()
        parameters['OutputModel'] = outputModelNode.GetID()
        probe = slicer.modules.probevolumewithmodel
        slicer.cli.run(probe, None, parameters, wait_for_completion=True)
        return

    def exportCurrentFolder(self, shFolderItemId, outputFolder):
        # Get items in the folder
        childIds = vtk.vtkIdList()
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        shNode.GetItemChildren(shFolderItemId, childIds)
        if childIds.GetNumberOfIds() == 0:
            return
        # Create output folder
        import os
        os.makedirs(outputFolder, exist_ok=True)
        # Write each child item to file
        for itemIdIndex in range(childIds.GetNumberOfIds()):
            shItemId = childIds.GetId(itemIdIndex)
            # Write node to file (if storable)
            dataNode = shNode.GetItemDataNode(shItemId)
            if dataNode and dataNode.IsA("vtkMRMLStorableNode") and dataNode.GetStorageNode():
                # storageNode = dataNode.GetStorageNode()
                # filename = os.path.basename(storageNode.GetFileName())
                fileBaseName = dataNode.GetName()
                print(fileBaseName)
                if dataNode.IsA("vtkMRMLModelNode"):
                    ext = ".ply"
                elif dataNode.IsA("vtkMRMLTransformNode"):
                    ext = ".h5"
                elif dataNode.IsA("vtkMRMLMarkupsFiducialNode"):
                    ext = ".mrk.json"
                elif dataNode.IsA("vtkMRMLMarkupsROINode"):
                    ext = ".mark.json"
                else:
                    ext = ".vtk"
                filename = fileBaseName + ext
                filepath = outputFolder + "/" + filename
                slicer.util.exportNode(dataNode, filepath)
            # Write all children of this child item
            grandChildIds = vtk.vtkIdList()
            shNode.GetItemChildren(shItemId, grandChildIds)
            if grandChildIds.GetNumberOfIds() > 0:
                exportNodes(shItemId, outputFolder + "/" + shNode.GetItemName(shItemId))



    def plotScalarHistogram(self, scalarArray, outputDir):
        try:
          import matplotlib
        except ModuleNotFoundError:
          slicer.util.pip_install("matplotlib")
        import matplotlib.pyplot as plt
        matplotlib.use("Agg")
          # from pylab import *
        import numpy as np
        import os
        import pandas
        # Set the last bin edge to np.inf so that all values >= 5 go into the last bin.
        bins = np.array(list(np.arange(0, 6, 1)) + [np.inf])
        counts, _ = np.histogram(scalarArray, bins=bins)
        percentage = counts / counts.sum() * 100
        # Set the bar positions will be at 0,1,2,3,4,5 with an extra tick label for the last bin.
        plot_bins = np.arange(0, 7)
        # Create the bar plot
        fig, ax = plt.subplots()
        ax.bar(plot_bins[:-1], percentage, width=1, align='edge', edgecolor='black', facecolor='white')
        
        # Label the axes and add a title
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel('Percentage (%)')
        ax.set_title("1072 large plate distances")
        
        # Set custom x-axis tick labels:
        # Labels 0 through 5 and then the maximum distance value as the last label.
        xtick_labels = [str(x) for x in np.arange(0, 6)]
        maxScalar = np.round(scalarArray.max(), decimals = 3)
        xtick_labels.append(str(maxScalar))
        ax.set_xticks(plot_bins)
        ax.set_xticklabels(xtick_labels)
        
        imageFileName = "plate_dists.png"
        imageFilePath = os.path.join(outputDir, imageFileName)

        if os.path.exists(imageFilePath):
            os.remove(imageFilePath)
        plt.savefig(imageFilePath, dpi=300)
        plt.close()
        # pm = qt.QPixmap(imageFilePath)
        # imageWidget = qt.QLabel()
        # imageWidget.setPixmap(pm)
        # imageWidget.setScaledContents(True)
        # imageWidget.show()
        csvFileName = "plate_heatmap_dists.csv"
        csvFilePath = os.path.join(outputDir, csvFileName)
        pandas.DataFrame(scalarArray).to_csv(csvFilePath, index=False)
        return

    def makeScatterPlotWithFactors(
        self, dataArray, factors, title, xAxisName, yAxisName, subjectID
        ):
        #Create a folder to store results
        #Creat a folder to store results
        plotFolderNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        sceneItemID = plotFolderNode.GetSceneItemID()
        newFolder = plotFolderNode.CreateFolderItem(
            sceneItemID, "compare_fitness_results"
        )
        #
        # create two tables for the first two factors and then check for a third
        # check if there is a table node has been created
        # numPoints = len(data)
        # uniqueFactors, factorCounts = np.unique(factors, return_counts=True)
        factorNumber = len(factors)

        # Set up chart
        plotChartNode = slicer.mrmlScene.GetFirstNodeByName(
            "Chart_scatterplot" + title + xAxisName + "v" + yAxisName
        )
        if plotChartNode is None:
            plotChartNode = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLPlotChartNode",
                "Chart_scatterplot" + title + xAxisName + "v" + yAxisName,
            )
        else:
            plotChartNode.RemoveAllPlotSeriesNodeIDs()

        #Save plotChartNode in the folder
        plotChartNodeItem = plotFolderNode.GetItemByDataNode(plotChartNode)
        plotFolderNode.SetItemParent(plotChartNodeItem, newFolder)
        #
        # Plot all series
        for i in range(dataArray.shape[0]):
            factor = factors[i]
            tableNode = slicer.mrmlScene.GetFirstNodeByName(
                "Table for the scatterplot " + title + factor
            )
            if tableNode is None:
                tableNode = slicer.mrmlScene.AddNewNodeByClass(
                    "vtkMRMLTableNode", 
                    "Table for the scatterplot " + title + factor
                )
            else:
                tableNode.RemoveAllColumns()  # clear previous data from columns

            #Save tableNode in the folder
            tableNodeItem = plotFolderNode.GetItemByDataNode(tableNode)
            plotFolderNode.SetItemParent(tableNodeItem, newFolder)

            # Set up columns for X,Y, and labels
            labels = tableNode.AddColumn()
            labels.SetName("Subject ID")
            tableNode.SetColumnType("Subject ID", vtk.VTK_STRING)

            # axisNum = 2
            # for i in range(axisNum):
            #     pc = tableNode.AddColumn()
            #     colName = "PC" + str(i + 1)
            #     pc.SetName(colName)
            #     tableNode.SetColumnType(colName, vtk.VTK_FLOAT)

            xAxisCol = tableNode.AddColumn()
            colName = xAxisName
            xAxisCol.SetName(colName)
            tableNode.SetColumnType(colName, vtk.VTK_INT)
            # #
            yAxisCol = tableNode.AddColumn()
            colName = yAxisName
            yAxisCol.SetName(colName)
            tableNode.SetColumnType(colName, vtk.VTK_FLOAT)
            #
            #
            # factorCounter = 0
            table = tableNode.GetTable()
            # table.SetNumberOfRows(factorCounts[factorIndex])
            table.SetNumberOfRows(dataArray.shape[1])

            #X = 1:len(dataArray.shape[1])
            #Y = actual value of each row of the dataArray
            # for i in range(numPoints):
            #     if factors[i] == factor:
            #         table.SetValue(factorCounter, 0, files[i])
            #         for j in range(pcNumber):
            #             table.SetValue(factorCounter, j + 1, data[i, j])
            #         factorCounter += 1
            for j in range(dataArray.shape[1]):
                table.SetValue(j, 0, subjectID[i][j])
                table.SetValue(j, 1, j+1)
                table.SetValue(j, 2, dataArray[i, j])
            

            plotSeriesNode = slicer.mrmlScene.GetFirstNodeByName(factor)
            if plotSeriesNode is None:
                plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass(
                    "vtkMRMLPlotSeriesNode", factor
                )
                # GPANodeCollection.AddItem(plotSeriesNode)
            # Create data series from table
            plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            plotSeriesNode.SetXColumnName(xAxisName)
            plotSeriesNode.SetYColumnName(yAxisName)
            plotSeriesNode.SetLabelColumnName("Subject ID")
            plotSeriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
            plotSeriesNode.SetLineStyle(slicer.vtkMRMLPlotSeriesNode.LineStyleNone)
            plotSeriesNode.SetMarkerStyle(
                slicer.vtkMRMLPlotSeriesNode.MarkerStyleSquare
            )
            plotSeriesNode.SetUniqueColor()
            # Add data series to chart
            plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())

            #Save plotSeriesNode in the folder
            plotSeriesNodeItem = plotFolderNode.GetItemByDataNode(plotSeriesNode)
            plotFolderNode.SetItemParent(plotSeriesNodeItem, newFolder)

        # Set up view options for chart
        plotChartNode.SetTitle(title)
        plotChartNode.SetXAxisTitle(xAxisName)
        plotChartNode.SetYAxisTitle(yAxisName)
        
        return plotChartNode


    def matplotlibScatterPlot(self, dataArray, groups, title, xLabel, exportDir):
        try:
          import matplotlib
        except ModuleNotFoundError:
          slicer.util.pip_install("matplotlib")
        import matplotlib.pyplot as plt
        matplotlib.use("Agg")
          # from pylab import *
        import numpy as np
        import os
        import pandas    
        
        # Get the number of groups
        groupNum = dataArray.shape[0]
        # Use a colormap (e.g., viridis) to generate n_groups distinct colors
        cmap = plt.cm.get_cmap('viridis', groupNum)
        
        # Plot each group with a unique color from the colormap
        # for idx, (group_name, (x, y)) in enumerate(groups.items()):
        #     plt.scatter(x, y, label=group_name, color=cmap(idx))
        plt.figure(figsize=(10, 5))
        x_values = np.arange(1, dataArray.shape[1]+1)
        for i in range(groupNum):
            plt.scatter(x_values, dataArray[i, ], label = groups[i], color = cmap(i)) 
        
        # Add title, axis labels, and legend
        plotTitle = "distances_plot_" + title
        plt.title(plotTitle)
        plt.xlabel(xLabel)
        plt.ylabel("Distances")
        plt.legend()
        
        imageFileName = title + ".png"
        imageFilePath = os.path.join(exportDir, imageFileName)

        if os.path.exists(imageFilePath):
            os.remove(imageFilePath)
        plt.savefig(imageFilePath, dpi=300)
        plt.close()
        
        csvFileName = title + ".csv"
        csvFilePath = os.path.join(exportDir, csvFileName)
        pandas.DataFrame(dataArray).to_csv(csvFilePath, index=False)



    def projectPoints(self, sourceLMNode, sourceModel, targetModel):
        #get points from a fiducial node
        sourcePoints = vtk.vtkPoints()
        for i in range(sourceLMNode.GetNumberOfControlPoints()):
            point = sourceLMNode.GetNthControlPointPosition(i)
            sourcePoints.InsertNextPoint(point)

        maxProjectionFactor = 0.005
        maxProjection = (targetModel.GetPolyData().GetLength()) * maxProjectionFactor
        print("Max projection: ", maxProjection)
        # sourcePoints = self.getFiducialPoints(sourceLMNode)

        # project landmarks from source to target model
        projectedPoints = self.projectPointsPolydata(
            sourceModel.GetPolyData(), targetModel.GetPolyData(), sourcePoints, maxProjection
        )
        projectedLMNode = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLMarkupsFiducialNode", sourceLMNode.GetName() + "_projected Landmarks"
        )
        for i in range(projectedPoints.GetNumberOfPoints()):
            point = projectedPoints.GetPoint(i)
            projectedLMNode.AddControlPoint(point)
        projectedLMNode.SetLocked(True)
        projectedLMNode.SetFixedNumberOfControlPoints(True)
        return projectedLMNode

    def projectPointsPolydata(self, sourcePolydata, targetPolydata, originalPoints, rayLength):
        #vtk ray casting composed in SlicerMorph ALPACA
        import vtk

        print("original points: ", originalPoints.GetNumberOfPoints())
        # set up polydata for projected points to return
        projectedPointData = vtk.vtkPolyData()
        projectedPoints = vtk.vtkPoints()
        projectedPointData.SetPoints(projectedPoints)

        # set up locater for intersection with normal vector rays
        obbTree = vtk.vtkOBBTree()
        obbTree.SetDataSet(targetPolydata)
        obbTree.BuildLocator()

        # set up point locator for finding surface normals and closest point
        pointLocator = vtk.vtkPointLocator()
        pointLocator.SetDataSet(sourcePolydata)
        pointLocator.BuildLocator()

        targetPointLocator = vtk.vtkPointLocator()
        targetPointLocator.SetDataSet(targetPolydata)
        targetPointLocator.BuildLocator()

        # get surface normal from each landmark point
        rayDirection = [0, 0, 0]
        normalArray = sourcePolydata.GetPointData().GetArray("Normals")
        if not normalArray:
            print("no normal array, calculating....")
            normalFilter = vtk.vtkPolyDataNormals()
            normalFilter.ComputePointNormalsOn()
            normalFilter.SetInputData(sourcePolydata)
            normalFilter.Update()
            normalArray = normalFilter.GetOutput().GetPointData().GetArray("Normals")
            if not normalArray:
                print("Error: no normal array")
                return projectedPointData
        for index in range(originalPoints.GetNumberOfPoints()):
            originalPoint = originalPoints.GetPoint(index)
            # get ray direction from closest normal
            closestPointId = pointLocator.FindClosestPoint(originalPoint)
            rayDirection = normalArray.GetTuple(closestPointId)
            rayEndPoint = [0, 0, 0]
            for dim in range(len(rayEndPoint)):
                rayEndPoint[dim] = originalPoint[dim] + rayDirection[dim] * rayLength
            intersectionIds = vtk.vtkIdList()
            intersectionPoints = vtk.vtkPoints()
            obbTree.IntersectWithLine(
                originalPoint, rayEndPoint, intersectionPoints, intersectionIds
            )
            # if there are intersections, update the point to most external one.
            if intersectionPoints.GetNumberOfPoints() > 0:
                exteriorPoint = intersectionPoints.GetPoint(
                    intersectionPoints.GetNumberOfPoints() - 1
                )
                projectedPoints.InsertNextPoint(exteriorPoint)
            # if there are no intersections, reverse the normal vector
            else:
                for dim in range(len(rayEndPoint)):
                    rayEndPoint[dim] = (
                        originalPoint[dim] + rayDirection[dim] * -rayLength
                    )
                obbTree.IntersectWithLine(
                    originalPoint, rayEndPoint, intersectionPoints, intersectionIds
                )
                if intersectionPoints.GetNumberOfPoints() > 0:
                    exteriorPoint = intersectionPoints.GetPoint(0)
                    projectedPoints.InsertNextPoint(exteriorPoint)
                # if none in reverse direction, use closest mesh point
                else:
                    closestPointId = targetPointLocator.FindClosestPoint(originalPoint)
                    rayOrigin = targetPolydata.GetPoint(closestPointId)
                    projectedPoints.InsertNextPoint(rayOrigin)
        return projectedPointData



    # def process(self,
    #             inputVolume: vtkMRMLScalarVolumeNode,
    #             outputVolume: vtkMRMLScalarVolumeNode,
    #             imageThreshold: float,
    #             invert: bool = False,
    #             showResult: bool = True) -> None:
    #     """
    #     Run the processing algorithm.
    #     Can be used without GUI widget.
    #     :param inputVolume: volume to be thresholded
    #     :param outputVolume: thresholding result
    #     :param imageThreshold: values above/below this threshold will be set to 0
    #     :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    #     :param showResult: show output volume in slice viewers
    #     """
    #
    #     if not inputVolume or not outputVolume:
    #         raise ValueError("Input or output volume is invalid")
    #
    #     import time
    #
    #     startTime = time.time()
    #     logging.info("Processing started")
    #
    #     # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    #     cliParams = {
    #         "InputVolume": inputVolume.GetID(),
    #         "OutputVolume": outputVolume.GetID(),
    #         "ThresholdValue": imageThreshold,
    #         "ThresholdType": "Above" if invert else "Below",
    #     }
    #     cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    #     # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    #     slicer.mrmlScene.RemoveNode(cliNode)
    #
    #     stopTime = time.time()
    #     logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


#
# plateRegistrationTest
#


# class plateRegistrationTest(ScriptedLoadableModuleTest):
#     """
#     This is the test case for your scripted module.
#     Uses ScriptedLoadableModuleTest base class, available at:
#     https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
#     """
# 
#     def setUp(self):
#         """Do whatever is needed to reset the state - typically a scene clear will be enough."""
#         slicer.mrmlScene.Clear()
# 
#     def runTest(self):
#         """Run as few or as many tests as needed here."""
#         self.setUp()
#         self.test_plateRegistration1()
# 
#     def test_plateRegistration1(self):
#         """Ideally you should have several levels of tests.  At the lowest level
#         tests should exercise the functionality of the logic with different inputs
#         (both valid and invalid).  At higher levels your tests should emulate the
#         way the user would interact with your code and confirm that it still works
#         the way you intended.
#         One of the most important features of the tests is that it should alert other
#         developers when their changes will have an impact on the behavior of your
#         module.  For example, if a developer removes a feature that you depend on,
#         your test should break so they know that the feature is needed.
#         """
# 
#         self.delayDisplay("Starting the test")
# 
#         # Get/create input data
# 
#         import SampleData
# 
#         registerSampleData()
#         inputVolume = SampleData.downloadSample("plateRegistration1")
#         self.delayDisplay("Loaded test data set")
# 
#         inputScalarRange = inputVolume.GetImageData().GetScalarRange()
#         self.assertEqual(inputScalarRange[0], 0)
#         self.assertEqual(inputScalarRange[1], 695)
# 
#         outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
#         threshold = 100
# 
#         # Test the module logic
# 
#         logic = plateRegistrationLogic()
# 
#         # Test algorithm with non-inverted threshold
#         logic.process(inputVolume, outputVolume, threshold, True)
#         outputScalarRange = outputVolume.GetImageData().GetScalarRange()
#         self.assertEqual(outputScalarRange[0], inputScalarRange[0])
#         self.assertEqual(outputScalarRange[1], threshold)
# 
#         # Test algorithm with inverted threshold
#         logic.process(inputVolume, outputVolume, threshold, False)
#         outputScalarRange = outputVolume.GetImageData().GetScalarRange()
#         self.assertEqual(outputScalarRange[0], inputScalarRange[0])
#         self.assertEqual(outputScalarRange[1], inputScalarRange[1])
# 
#         self.delayDisplay("Test passed")
