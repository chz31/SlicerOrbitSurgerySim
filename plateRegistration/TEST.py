def onProjectPtsBatchScene(self):
    logic = plateRegistrationLogic()
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    plateMarginInputRootDir = self.ui.platePtsBatchPathLineEdit.currentPath
    rootDir = os.path.dirname(plateMarginInputRootDir)
    plateRegDir = os.path.join(rootDir, 'plate_registration_results')
    outputRootDir = os.path.join(rootDir, "fit_output", "fit_metrics")
    os.makedirs(outputRootDir, exist_ok=True)
    #
    plateBaseNames = [
        name
        for name in os.listdir(plateMarginInputRootDir)
        if os.path.isdir(os.path.join(plateMarginInputRootDir, name))
    ]
    print(f"base names for point projection are {plateBaseNames}\n")
    # print(f'plate base names from the raw margin pts folder are {plateBaseNames}')
    # registeredPlateInfoDict = json.loads(self._parameterNode.registeredPlateInfoJSON)
    plateRegFolders = [folder for folder in os.listdir(plateRegDir) if os.path.isdir(os.path.join(plateRegDir, folder))]
    for currentPlateFolderName in plateRegFolders:
        for baseName in plateBaseNames:
            if not currentPlateFolderName.startswith(baseName):
                continue
            else:
                print(f"current plate folder for point projection is {currentPlateFolderName}\n")
                rawPlateMarginCurveDir = os.path.join(plateMarginInputRootDir, baseName)
                # finalPlateModelNodeId = registeredPlateInfoDict[currentPlateFolderName]['finalPlateModelNodeID']
                # finalPlateModelNode = slicer.mrmlScene.GetNodeByID(finalPlateModelNodeId)
                # fullTransformNodeID = registeredPlateInfoDict[currentPlateFolderName]["fullTransformNodeID"]
                # fullTransformNode = slicer.mrmlScene.GetNodeByID(fullTransformNodeID)
                logfile = "plate_registration.log"
                logfilepath = os.path.join(plateRegDir, currentPlateFolderName, logfile)
                with open(logfilepath, "r") as f:
                    lines = [L.strip() for L in f]
                finalPlateFile = lines[0].split(":", 1)[1].strip()
                finalPlatePath = os.path.join(plateRegDir, currentPlateFolderName, finalPlateFile)
                finalPlateModelNode = slicer.util.loadModel(finalPlatePath)
                fullTransformFile = lines[2].split(":", 1)[1].strip()
                fullTransformPath = os.path.join(plateRegDir, currentPlateFolderName, fullTransformFile)
                print(f"current full transform path for point proj is {fullTransformPath} and {finalPlatePath}\n")
                fullTransformNode = slicer.util.loadTransform(fullTransformPath)

                for file in os.listdir(rawPlateMarginCurveDir):
                    if file.endswith((".json", ".fcsv")):
                        #
                        plateMarginCurveNode = slicer.util.loadMarkups(os.path.join(rawPlateMarginCurveDir, file))
                        plateMarginCurveNode.SetName(file.split('.')[0])
                        plateMarginCurveNode.SetAndObserveTransformNodeID(fullTransformNode.GetID())
                        slicer.vtkSlicerTransformLogic().hardenTransform(plateMarginCurveNode)
                        plateMarginPtsNode = logic.curveToFiducialMarkups(plateMarginCurveNode)
                        plateMarginPtsNode.SetName(plateMarginCurveNode.GetName())
                        #
                        for i in range(plateMarginPtsNode.GetNumberOfControlPoints()):
                            newLabel = str(i + 1)
                            plateMarginPtsNode.SetNthControlPointLabel(i, newLabel)
                        plateMarginPtsNode.GetDisplayNode().SetSelectedColor(0, 0, 1)
                        #
                        # curve to fiducial markups
                        projectedPlateLMNode = logic.projectPoints(
                            sourceLMNode=plateMarginPtsNode,
                            sourceModel=finalPlateModelNode,
                            targetModel=self._parameterNode.orbitModelRecon
                        )
                        for i in range(projectedPlateLMNode.GetNumberOfControlPoints()):
                            newLabel = str(i + 1)
                            projectedPlateLMNode.SetNthControlPointLabel(i, newLabel)
                        #
                        projectedPlateLMNode.GetDisplayNode().SetSelectedColor(1, 0, 0)
                        #
                        outputFolderPath = os.path.join(outputRootDir, currentPlateFolderName)
                        #
                        outputFolderOnPlate = os.path.join(outputFolderPath, "points_on_the_plate")
                        os.makedirs(outputFolderOnPlate, exist_ok=True)
                        outputFileOnPlate = os.path.join(outputFolderOnPlate,
                                                         plateMarginPtsNode.GetName() + "_onPlate.mrk.json")
                        slicer.util.saveNode(plateMarginPtsNode, outputFileOnPlate)
                        #
                        outputFolderProj = os.path.join(outputFolderPath, "points_projected_to_orbit")
                        os.makedirs(outputFolderProj, exist_ok=True)
                        projectedOutputFile = os.path.join(outputFolderProj,
                                                           plateMarginPtsNode.GetName() + "_projected.mrk.json")
                        slicer.util.saveNode(projectedPlateLMNode, projectedOutputFile)
                        #
                        slicer.mrmlScene.RemoveNode(plateMarginCurveNode)
                        slicer.mrmlScene.RemoveNode(plateMarginPtsNode)
                        slicer.mrmlScene.RemoveNode(projectedPlateLMNode)
                    slicer.mrmlScene.RemoveNode(finalPlateModelNode)
                    slicer.mrmlScene.RemoveNode(fullTransformNode)
    self.ui.compareFitPathLineEdit.currentPath = outputRootDir
    self.ui.compareMarginDistsCheckBox.checked = 1