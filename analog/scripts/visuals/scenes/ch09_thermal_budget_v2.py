"""Chapter 9: thermal_budget."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('thermal_budget')


def storyboard():
    return regulator_scenes.storyboard('thermal_budget')


META = regulator_scenes.metadata('thermal_budget')
