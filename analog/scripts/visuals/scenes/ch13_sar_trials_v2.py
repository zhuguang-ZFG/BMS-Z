"""Chapter 13: sar_trials."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('sar_trials')


def storyboard():
    return power_signal_scenes.storyboard('sar_trials')


META = power_signal_scenes.metadata('sar_trials')
