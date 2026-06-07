"""Engine-agnostic procedural tree generation."""
from src.trees.forest_placer import ForestPlacement, place_forest, place_forest_multi
from src.trees.generate import generate_morphology
from src.trees.instance import TreeInstanceSpec, roll_tree_instance, roll_tree_instance_by_patch_id
from src.trees.lifecycle import growth_factor, mature_height_m, resolve_stage
from src.trees.loader import (
    load_forest_patch,
    load_forest_patches,
    load_palette,
    load_species,
    load_species_catalog,
)
from src.trees.morphology import TreeLifeStage, TreeMorphology
from src.trees.species import ForestPatchDef, TreeSpeciesDef

__all__ = [
    "ForestPatchDef",
    "ForestPlacement",
    "TreeInstanceSpec",
    "TreeLifeStage",
    "TreeMorphology",
    "TreeSpeciesDef",
    "generate_morphology",
    "growth_factor",
    "load_forest_patch",
    "load_forest_patches",
    "load_palette",
    "load_species",
    "load_species_catalog",
    "mature_height_m",
    "place_forest",
    "place_forest_multi",
    "resolve_stage",
    "roll_tree_instance",
    "roll_tree_instance_by_patch_id",
]
