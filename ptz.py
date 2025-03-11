#*****************************************************************************
#IP Camera control
#Control methods:
#   rtsp video streaming via OpenCV for frame capture
#   ONVIF for PTZ control
#   ONVIF for setup selections
#
# Starting point for this code was from:
# https://github.com/quatanium/python-onvif
#*****************************************************************************

from onvif import ONVIFCamera
from time import sleep
import logging
import os
from dotenv import load_dotenv
import signal

# Define a timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Connection timed out")

class ptzcam():
    def __init__(self, verbose=False, timeout=5):
        self.verbose = verbose
        if(self.verbose):
            logging.basicConfig(level=logging.DEBUG)
        
        logging.debug('IP camera initialization')

        load_dotenv()
        
        # Set up the timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)  # Set a timeout
        
        try:
            self.mycam = ONVIFCamera(os.getenv('CAMERA_IP'), int(os.getenv('CAMERA_PORT')), os.getenv('CAMERA_USERNAME'), os.getenv('CAMERA_PASSWORD'))
            logging.debug('Connected to ONVIF camera')
            # Create media service object
            self.media = self.mycam.create_media_service()
            logging.debug('Created media service object')
            # Get target profile
            self.media_profile = self.media.GetProfiles()[0]
            # Use the first profile and Profiles have at least one
            token = self.media_profile.token

            #PTZ controls  -------------------------------------------------------------
            logging.debug('Creating PTZ object')
            self.ptz = self.mycam.create_ptz_service()
            logging.debug('Created PTZ service object')


            #Get available PTZ services
            request = self.ptz.create_type('GetServiceCapabilities')
            Service_Capabilities = self.ptz.GetServiceCapabilities(request)
            logging.debug('PTZ service capabilities:')
            logging.debug(Service_Capabilities)

            #Get PTZ status
            status = self.ptz.GetStatus({'ProfileToken':token})
            logging.debug('PTZ status:')
            logging.debug(status)
            logging.debug('Pan position:', status.Position.PanTilt.x)
            logging.debug('Tilt position:', status.Position.PanTilt.y)
            logging.debug('Zoom position:', status.Position.Zoom.x)
            logging.debug('Pan/Tilt Moving?:', status.MoveStatus.PanTilt)

            # Get PTZ configuration options for getting option ranges
            request = self.ptz.create_type('GetConfigurationOptions')
            request.ConfigurationToken = self.media_profile.PTZConfiguration.token
            ptz_configuration_options = self.ptz.GetConfigurationOptions(request)
            logging.debug('PTZ configuration options:')
            logging.debug(ptz_configuration_options)

            self.requestc = self.ptz.create_type('ContinuousMove')
            self.requestc.ProfileToken = self.media_profile.token
            self.requestc.Velocity = {}

            self.requesta = self.ptz.create_type('AbsoluteMove')
            self.requesta.ProfileToken = self.media_profile.token
            logging.debug('Absolute move options')
            logging.debug(self.requesta)

            self.requestr = self.ptz.create_type('RelativeMove')
            self.requestr.ProfileToken = self.media_profile.token
            logging.debug('Relative move options')
            logging.debug(self.requestr)

            self.requests = self.ptz.create_type('Stop')
            self.requests.ProfileToken = self.media_profile.token

            self.requestp = self.ptz.create_type('SetPreset')
            self.requestp.ProfileToken = self.media_profile.token

            self.requestg = self.ptz.create_type('GotoPreset')
            self.requestg.ProfileToken = self.media_profile.token

            logging.debug('Initial PTZ stop')
            self.stop()

            # Cancel the alarm if everything went well
            signal.alarm(0)
            
        except TimeoutError as e:
            logging.error(f"Camera connection timed out: {e}")
            signal.alarm(0)  # Cancel the alarm
            raise
        except Exception as e:
            logging.error(f"Failed to initialize camera: {e}")
            signal.alarm(0)  # Cancel the alarm
            raise

#Stop pan, tilt and zoom
    def stop(self):
        self.requests.PanTilt = True
        self.requests.Zoom = True
        logging.debug('Stop:')
        #logging.debug(self.requests)
        self.ptz.Stop(self.requests)
        logging.debug('Stopped')

#Continuous move functions
    def perform_move(self, timeout):
        # Start continuous move
        # self.requestc.ProfileToken = self.media_profile.token
        ret = self.ptz.ContinuousMove(self.requestc)
        logging.debug('Continuous move completed', ret)
        # Wait a certain time
        sleep(timeout)
        # Stop continuous move
        self.stop()
        sleep(2)

    def move_tilt(self, velocity, timeout):
        logging.debug('Move tilt...', velocity)
        self.requestc.Velocity = {
            "PanTilt": {
                "x": 0.0,
                "y": velocity
            }
        }
        self.perform_move(timeout)

    def move_pan(self, velocity, timeout):
        logging.debug('Move pan...', velocity)
        self.requestc.Velocity = {
            "PanTilt": {
                "x": velocity,
                "y": 0.0
            }
        }
        self.perform_move(timeout)

    def zoom(self, velocity, timeout=0):
        logging.debug('Zoom...', velocity)
        self.requestc.Velocity = {
            "Zoom": {
                "x": velocity
            }
        }
        self.perform_move(timeout)

#Absolute move functions --NO ERRORS BUT CAMERA DOES NOT MOVE
    def move_abspantilt(self, pan, tilt, velocity):
        self.requesta.Position = {
            "PanTilt": {
                "x": pan,
                "y": tilt
            }
        }
        self.requesta.Speed = {
            "PanTilt": {
                "x": velocity,
                "y": velocity
            }
        }
        logging.debug('Absolute move to:', self.requesta.Position)
        logging.debug('Absolute speed:',self.requesta.Speed)
        ret = self.ptz.AbsoluteMove(self.requesta)
        logging.debug('Absolute move pan-tilt requested:', pan, tilt, velocity)
        logging.debug('Absolute move completed', ret)


#Relative move functions --NO ERRORS BUT CAMERA DOES NOT MOVE
    def move_relative(self, pan, tilt, velocity):
        self.requestr.Translation = {
            "PanTilt": {
                "x": pan,
                "y": tilt
            }
        }
        self.requestr.Speed = {
            "PanTilt": {
                "x": velocity,
                "y": velocity
            }
        }
        self.ptz.RelativeMove(self.requestr)
        logging.debug('Relative move pan-tilt', pan, tilt, velocity)
        sleep(2.0)
        logging.debug('Relative move completed')

#Sets preset set, query and and go to
    def set_preset(self, name):
        self.requestp.PresetName = name
        self.requestp.PresetToken = '1'
        self.preset = self.ptz.SetPreset(self.requestp)  #returns the PresetToken
        logging.debug('Set Preset:')
        logging.debug(self.preset)

    def get_preset(self):
        self.ptzPresetsList = self.ptz.GetPresets({'ProfileToken': self.media_profile.token})
        logging.debug('Got preset:')
        logging.debug(self.ptzPresetsList[0])

    def goto_preset(self, name):
        self.requestg.PresetToken = '1'
        self.ptz.GotoPreset(self.requestg)
        logging.debug('Going to Preset:')
        logging.debug(name)
