"""Chapter 9: load_transient."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('load_transient')


def storyboard():
    return regulator_scenes.storyboard('load_transient')


META = regulator_scenes.metadata('load_transient')
