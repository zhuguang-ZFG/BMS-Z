"""Chapter 6: noise bandwidth."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('noise_bandwidth')


def storyboard():
    return opamp_scenes.storyboard('noise_bandwidth')


META = opamp_scenes.metadata('noise_bandwidth')
