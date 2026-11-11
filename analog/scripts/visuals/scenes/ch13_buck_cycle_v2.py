"""Chapter 13: buck_cycle."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('buck_cycle')


def storyboard():
    return power_signal_scenes.storyboard('buck_cycle')


META = power_signal_scenes.metadata('buck_cycle')
