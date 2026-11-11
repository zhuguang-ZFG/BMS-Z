"""Chapter 6: rejection."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('rejection')


def storyboard():
    return opamp_scenes.storyboard('rejection')


META = opamp_scenes.metadata('rejection')
