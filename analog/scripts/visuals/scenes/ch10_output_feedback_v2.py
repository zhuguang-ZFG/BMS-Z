"""Chapter 10: output_feedback."""
from scripts.visuals import timer_scenes


def scene():
    return timer_scenes.scene('output_feedback')


def storyboard():
    return timer_scenes.storyboard('output_feedback')


META = timer_scenes.metadata('output_feedback')
