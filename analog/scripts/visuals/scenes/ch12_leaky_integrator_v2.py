"""Chapter 12: leaky_integrator."""
from scripts.visuals import application_scenes


def scene():
    return application_scenes.scene('leaky_integrator')


def storyboard():
    return application_scenes.storyboard('leaky_integrator')


META = application_scenes.metadata('leaky_integrator')
