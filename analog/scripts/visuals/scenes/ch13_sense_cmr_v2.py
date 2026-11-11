"""Chapter 13: sense_cmr."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('sense_cmr')


def storyboard():
    return power_signal_scenes.storyboard('sense_cmr')


META = power_signal_scenes.metadata('sense_cmr')
