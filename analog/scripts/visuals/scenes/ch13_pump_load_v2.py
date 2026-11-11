"""Chapter 13: pump_load."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('pump_load')


def storyboard():
    return power_signal_scenes.storyboard('pump_load')


META = power_signal_scenes.metadata('pump_load')
