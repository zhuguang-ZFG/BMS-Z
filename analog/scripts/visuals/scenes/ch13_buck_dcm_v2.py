"""Chapter 13: buck_dcm."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('buck_dcm')


def storyboard():
    return power_signal_scenes.storyboard('buck_dcm')


META = power_signal_scenes.metadata('buck_dcm')
