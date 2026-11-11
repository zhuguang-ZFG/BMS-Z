"""Chapter 9: tl431_bias."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('tl431_bias')


def storyboard():
    return regulator_scenes.storyboard('tl431_bias')


META = regulator_scenes.metadata('tl431_bias')
