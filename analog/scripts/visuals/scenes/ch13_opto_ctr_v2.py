"""Chapter 13: opto_ctr."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('opto_ctr')


def storyboard():
    return power_signal_scenes.storyboard('opto_ctr')


META = power_signal_scenes.metadata('opto_ctr')
