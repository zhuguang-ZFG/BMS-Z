"""Chapter 9: light_load_efficiency."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('light_load_efficiency')


def storyboard():
    return regulator_scenes.storyboard('light_load_efficiency')


META = regulator_scenes.metadata('light_load_efficiency')
