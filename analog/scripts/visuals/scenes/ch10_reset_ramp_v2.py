"""Chapter 10: reset_ramp."""
from scripts.visuals import timer_scenes


def scene():
    return timer_scenes.scene('reset_ramp')


def storyboard():
    return timer_scenes.storyboard('reset_ramp')


META = timer_scenes.metadata('reset_ramp')
