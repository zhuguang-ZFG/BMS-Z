"""Chapter 13: current_compliance."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('current_compliance')


def storyboard():
    return power_signal_scenes.storyboard('current_compliance')


META = power_signal_scenes.metadata('current_compliance')
