"""Chapter 11: active_load."""
from scripts.visuals import topology_scenes


def scene():
    return topology_scenes.scene('active_load')


def storyboard():
    return topology_scenes.storyboard('active_load')


META = topology_scenes.metadata('active_load')
