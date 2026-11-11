"""Chapter 9: shunt_corners."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('shunt_corners')


def storyboard():
    return regulator_scenes.storyboard('shunt_corners')


META = regulator_scenes.metadata('shunt_corners')
