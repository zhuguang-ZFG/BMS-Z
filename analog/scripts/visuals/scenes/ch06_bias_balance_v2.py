"""Chapter 6: bias balance."""
from scripts.visuals import opamp_scenes


def scene():
    return opamp_scenes.scene('bias_balance')


def storyboard():
    return opamp_scenes.storyboard('bias_balance')


META = opamp_scenes.metadata('bias_balance')
