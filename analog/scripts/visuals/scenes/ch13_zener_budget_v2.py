"""Chapter 13: zener_budget."""
from scripts.visuals import power_signal_scenes


def scene():
    return power_signal_scenes.scene('zener_budget')


def storyboard():
    return power_signal_scenes.storyboard('zener_budget')


META = power_signal_scenes.metadata('zener_budget')
