"""Chapter 10: control_sweep."""
from scripts.visuals import timer_scenes


def scene():
    return timer_scenes.scene('control_sweep')


def storyboard():
    return timer_scenes.storyboard('control_sweep')


META = timer_scenes.metadata('control_sweep')
