"""Chapter 9: reference_pulses."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('reference_pulses')


def storyboard():
    return regulator_scenes.storyboard('reference_pulses')


META = regulator_scenes.metadata('reference_pulses')
