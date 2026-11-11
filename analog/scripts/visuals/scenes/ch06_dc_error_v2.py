"""Chapter 6: dc error."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('dc_error')


def storyboard():
    return opamp_scenes.storyboard('dc_error')


META = opamp_scenes.metadata('dc_error')
