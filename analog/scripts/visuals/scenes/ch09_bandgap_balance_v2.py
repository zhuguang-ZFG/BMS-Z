"""Chapter 9: bandgap_balance."""
from scripts.visuals import regulator_scenes


def scene():
    return regulator_scenes.scene('bandgap_balance')


def storyboard():
    return regulator_scenes.storyboard('bandgap_balance')


META = regulator_scenes.metadata('bandgap_balance')
