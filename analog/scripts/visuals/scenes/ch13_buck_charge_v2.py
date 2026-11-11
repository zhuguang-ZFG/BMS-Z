"""Chapter 13: buck_charge."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('buck_charge')


def storyboard():
    return power_signal_scenes.storyboard('buck_charge')


META = power_signal_scenes.metadata('buck_charge')
