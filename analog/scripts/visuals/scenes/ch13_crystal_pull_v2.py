"""Chapter 13: crystal_pull."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('crystal_pull')


def storyboard():
    return power_signal_scenes.storyboard('crystal_pull')


META = power_signal_scenes.metadata('crystal_pull')
