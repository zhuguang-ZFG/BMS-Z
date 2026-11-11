"""Chapter 13: acquisition."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('acquisition')


def storyboard():
    return power_signal_scenes.storyboard('acquisition')


META = power_signal_scenes.metadata('acquisition')
