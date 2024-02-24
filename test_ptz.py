#!/usr/bin/python

#-------------------------------------------------------------------------------
#Test of Python and Quatanium Python-ONVIF with NETCAT camera PT-PTZ2087
#ONVIF Client implementation is in Python
#For IP control of PTZ, the camera should be compliant with ONVIF Profile S
#The PTZ2087 reports it is ONVIF 2.04 but is actually 2.4 (Netcat said text not changed after upgrade)
#------------------------------------------------------------------------------

import ptz

if __name__ == '__main__':

    #Do all setup initializations
    ptz = ptz.ptzcam()

#*****************************************************************************
# IP camera motion tests
#*****************************************************************************
    print('Starting tests...')

    #Set preset
    # ptz.move_pan(1.0, 1)  #move to a new home position
    # ptz.set_preset('home')

    # # move right -- (velocity, duration of move)
    # ptz.move_pan(1.0, 2)

    # # move left
    # ptz.move_pan(-1.0, 2)

    # # move down
    # ptz.move_tilt(-1.0, 2)

    # # Move up
    # ptz.move_tilt(1.0, 2)

    # zoom in
    # ptz.zoom(4.0, 2)

    # # zoom out
    # ptz.zoom(-8.0, 2)

    # #Absolute pan-tilt (pan position, tilt position, velocity)
    # #DOES NOT RESULT IN CAMERA MOVEMENT
    ptz.move_abspantilt(-0.5, 0.5, 0.5)
    ptz.zoom(1.0)
    # ptz.move_abspantilt(1.0, -1.0, 1.0)
    # ptz.move_abspantilt(1.0, -1.0, 1.0)

    # #Relative move (pan increment, tilt increment, velocity)
    # #DOES NOT RESULT IN CAMERA MOVEMENT
    # ptz.move_relative(0.5, 0.5, 8.0)

    #Get presets
    # ptz.set_preset('Hello')
    # ptz.get_preset()
    #Go back to preset
    # ptz.goto_preset('home')

    exit()