"""Chapter 6: compensation."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('compensation')


def storyboard():
    return opamp_scenes.storyboard('compensation')


META = opamp_scenes.metadata('compensation')
