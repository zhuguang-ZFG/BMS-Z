"""Chapter 6: settling."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('settling')


def storyboard():
    return opamp_scenes.storyboard('settling')


META = opamp_scenes.metadata('settling')
