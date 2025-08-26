cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(orbitSurgerySim)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/chz31/SlicerOrbitSurgerySim")
set(EXTENSION_CONTRIBUTORS "Chi Zhang (Texas A&M Dentistry), Kyle Sunderland (Perk Lab, Queens), Andrew Read-Fuller (Texas A&M Dentistry)")
set(EXTENSION_DESCRIPTION "orbitSurgerySim is for interactively registering and comparing the fit of surgical plates for orbital fracture repair.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/orbitSurgerySim.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/orbitSurgerySim/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(plateRegistration)
add_subdirectory(mirrorOrbitRecon)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
