"""Chapter 13: boost_stress."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('boost_stress')


def storyboard():
    return power_signal_scenes.storyboard('boost_stress')


META = power_signal_scenes.metadata('boost_stress')
