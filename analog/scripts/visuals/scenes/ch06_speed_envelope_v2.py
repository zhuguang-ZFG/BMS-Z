"""Chapter 6: speed envelope."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('speed_envelope')


def storyboard():
    return opamp_scenes.storyboard('speed_envelope')


META = opamp_scenes.metadata('speed_envelope')
