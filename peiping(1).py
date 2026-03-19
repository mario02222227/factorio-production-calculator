"""
异星工厂产线计算工具 v4 — Tkinter GUI
原版 1.1 全配方覆盖
改进:
  - 字体更清晰（更大、更鲜明）
  - 组装机台数汇总行
  - 双击物品直接添加到列表（默认1个/分）
  - 每行独立单位下拉框
  - 行内可直接编辑产量
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox

# ═══════════════════════════════════════════════════════════
#  机器速度常量
# ═══════════════════════════════════════════════════════════
ASSEMBLING_SPEED: dict[int, float] = {1: 0.5, 2: 0.75, 3: 1.25}
FURNACE_SPEED    = 2.0
CHEM_PLANT_SPEED = 1.0
OIL_REFINERY_SPEED = 1.0
ROCKET_SILO_SPEED  = 1.0
CENTRIFUGE_SPEED   = 0.75
MINING_SPEED       = 1.0

# ═══════════════════════════════════════════════════════════
#  配方数据结构
# ═══════════════════════════════════════════════════════════
@dataclass
class Recipe:
    time: float
    output: float
    inputs: dict[str, float]
    category: str

# ═══════════════════════════════════════════════════════════
#  原版 1.1 完整配方表
# ═══════════════════════════════════════════════════════════
RECIPES: dict[str, Recipe] = {
    "iron_plate":           Recipe(3.2,  1,  {"iron_ore": 1},             "furnace"),
    "copper_plate":         Recipe(3.2,  1,  {"copper_ore": 1},           "furnace"),
    "steel_plate":          Recipe(16.0, 1,  {"iron_plate": 5},           "furnace"),
    "stone_brick":          Recipe(3.2,  1,  {"stone": 2},                "furnace"),
    "copper_cable":         Recipe(0.5,  2,  {"copper_plate": 1},                    "assembling"),
    "iron_gear_wheel":      Recipe(0.5,  1,  {"iron_plate": 2},                      "assembling"),
    "iron_stick":           Recipe(0.5,  2,  {"iron_plate": 1},                      "assembling"),
    "pipe":                 Recipe(0.5,  1,  {"iron_plate": 1},                      "assembling"),
    "empty_barrel":         Recipe(1.0,  1,  {"steel_plate": 1},                     "assembling"),
    "stone_wall":           Recipe(0.5,  1,  {"stone_brick": 5},                     "assembling"),
    "gate":                 Recipe(0.5,  1,  {"stone_wall": 1, "steel_plate": 2, "green_circuit": 2}, "assembling"),
    "green_circuit":        Recipe(0.5,  1,  {"iron_plate": 1, "copper_cable": 3},   "assembling"),
    "advanced_circuit":     Recipe(6.0,  1,  {"green_circuit": 2, "plastic_bar": 2, "copper_cable": 4}, "assembling"),
    "processing_unit":      Recipe(10.0, 1,  {"green_circuit": 20, "advanced_circuit": 2, "sulfuric_acid": 5}, "chemical"),
    "plastic_bar":          Recipe(1.0,  2,  {"coal": 1, "petroleum_gas": 20},       "chemical"),
    "sulfur":               Recipe(1.0,  2,  {"petroleum_gas": 30, "water": 30},     "chemical"),
    "sulfuric_acid":        Recipe(1.0,  50, {"sulfur": 5, "water": 100, "iron_plate": 1}, "chemical"),
    "battery":              Recipe(4.0,  1,  {"sulfuric_acid": 20, "copper_plate": 1, "iron_plate": 1}, "chemical"),
    "explosives":           Recipe(4.0,  2,  {"coal": 1, "sulfur": 1, "water": 10},  "chemical"),
    "lubricant":            Recipe(1.0,  10, {"heavy_oil": 10},                      "chemical"),
    "solid_fuel_from_light_oil":    Recipe(1.0, 1, {"light_oil": 10},               "chemical"),
    "solid_fuel_from_heavy_oil":    Recipe(1.0, 1, {"heavy_oil": 20},               "chemical"),
    "solid_fuel_from_petroleum_gas":Recipe(1.0, 1, {"petroleum_gas": 20},           "chemical"),
    "rocket_fuel":          Recipe(15.0, 1,  {"light_oil": 10, "solid_fuel": 10},   "chemical"),
    "nuclear_fuel":         Recipe(90.0, 1,  {"rocket_fuel": 1, "uranium_235": 1},  "centrifuge"),
    "petroleum_gas_basic":  Recipe(5.0,  45, {"crude_oil": 100},                    "refinery"),
    "advanced_oil_processing": Recipe(5.0, 1, {"crude_oil": 100, "water": 50},      "refinery"),
    "heavy_oil_cracking":   Recipe(2.0,  30, {"heavy_oil": 40, "water": 30},        "chemical"),
    "light_oil_cracking":   Recipe(2.0,  20, {"light_oil": 30, "water": 30},        "chemical"),
    "coal_liquefaction":    Recipe(5.0,  90, {"coal": 10, "heavy_oil": 25, "steam": 50}, "refinery"),
    "flamethrower_ammo":    Recipe(6.0,  1,  {"crude_oil": 100, "steel_plate": 5},  "chemical"),
    "automation_science_pack":  Recipe(5.0,  1,  {"copper_plate": 1, "iron_gear_wheel": 1},                         "assembling"),
    "logistic_science_pack":    Recipe(6.0,  1,  {"inserter": 1, "transport_belt": 1},                              "assembling"),
    "military_science_pack":    Recipe(10.0, 2,  {"stone_wall": 2, "grenade": 1, "piercing_rounds_magazine": 1},    "assembling"),
    "chemical_science_pack":    Recipe(24.0, 2,  {"advanced_circuit": 3, "engine_unit": 2, "sulfur": 1},            "assembling"),
    "production_science_pack":  Recipe(21.0, 3,  {"electric_furnace": 1, "productivity_module": 1, "rail": 30},     "assembling"),
    "utility_science_pack":     Recipe(21.0, 3,  {"flying_robot_frame": 1, "low_density_structure": 3, "processing_unit": 2}, "assembling"),
    "space_science_pack":       Recipe(40.57, 1000, {"rocket_part": 100, "satellite": 1},                           "rocket"),
    "transport_belt":           Recipe(0.5,  2,  {"iron_gear_wheel": 1, "iron_plate": 1},                    "assembling"),
    "fast_transport_belt":      Recipe(0.5,  1,  {"iron_gear_wheel": 5, "transport_belt": 1},                "assembling"),
    "express_transport_belt":   Recipe(0.5,  1,  {"iron_gear_wheel": 10, "fast_transport_belt": 1, "lubricant": 20}, "chemical"),
    "underground_belt":         Recipe(1.0,  2,  {"iron_plate": 10, "transport_belt": 5},                    "assembling"),
    "fast_underground_belt":    Recipe(2.0,  2,  {"iron_gear_wheel": 40, "underground_belt": 2},             "assembling"),
    "express_underground_belt": Recipe(2.0,  2,  {"iron_gear_wheel": 80, "fast_underground_belt": 2, "lubricant": 40}, "chemical"),
    "splitter":                 Recipe(1.0,  1,  {"green_circuit": 5, "iron_plate": 5, "transport_belt": 4}, "assembling"),
    "fast_splitter":            Recipe(2.0,  1,  {"green_circuit": 10, "iron_gear_wheel": 10, "splitter": 1},"assembling"),
    "express_splitter":         Recipe(2.0,  1,  {"advanced_circuit": 10, "iron_gear_wheel": 10, "fast_splitter": 1, "lubricant": 80}, "chemical"),
    "inserter":                 Recipe(0.5,  1,  {"green_circuit": 1, "iron_gear_wheel": 1, "iron_plate": 1}, "assembling"),
    "burner_inserter":          Recipe(0.5,  1,  {"iron_gear_wheel": 1, "iron_plate": 1},                    "assembling"),
    "long_handed_inserter":     Recipe(0.5,  1,  {"inserter": 1, "iron_gear_wheel": 1, "iron_plate": 1},     "assembling"),
    "fast_inserter":            Recipe(0.5,  1,  {"green_circuit": 2, "iron_plate": 2, "inserter": 1},       "assembling"),
    "filter_inserter":          Recipe(0.5,  1,  {"fast_inserter": 1, "green_circuit": 4},                   "assembling"),
    "bulk_inserter":            Recipe(0.5,  1,  {"advanced_circuit": 1, "fast_inserter": 1, "green_circuit": 15, "iron_gear_wheel": 15}, "assembling"),
    "logistic_robot":           Recipe(0.5,  1,  {"advanced_circuit": 2, "flying_robot_frame": 1},           "assembling"),
    "construction_robot":       Recipe(0.5,  1,  {"green_circuit": 2, "flying_robot_frame": 1},              "assembling"),
    "roboport":                 Recipe(5.0,  1,  {"advanced_circuit": 45, "iron_gear_wheel": 45, "steel_plate": 45}, "assembling"),
    "iron_chest":               Recipe(0.5,  1,  {"iron_plate": 8},                                          "assembling"),
    "steel_chest":              Recipe(0.5,  1,  {"steel_plate": 8},                                         "assembling"),
    "active_provider_chest":    Recipe(0.5,  1,  {"green_circuit": 3, "advanced_circuit": 1, "steel_chest": 1}, "assembling"),
    "passive_provider_chest":   Recipe(0.5,  1,  {"green_circuit": 3, "advanced_circuit": 1, "steel_chest": 1}, "assembling"),
    "requester_chest":          Recipe(0.5,  1,  {"green_circuit": 3, "advanced_circuit": 1, "steel_chest": 1}, "assembling"),
    "storage_chest":            Recipe(0.5,  1,  {"green_circuit": 3, "advanced_circuit": 1, "steel_chest": 1}, "assembling"),
    "buffer_chest":             Recipe(0.5,  1,  {"green_circuit": 3, "advanced_circuit": 1, "steel_chest": 1}, "assembling"),
    "engine_unit":              Recipe(10.0, 1,  {"iron_gear_wheel": 1, "pipe": 2, "steel_plate": 1},        "assembling"),
    "electric_engine_unit":     Recipe(10.0, 1,  {"green_circuit": 2, "engine_unit": 1, "lubricant": 15},    "chemical"),
    "flying_robot_frame":       Recipe(20.0, 1,  {"battery": 2, "electric_engine_unit": 1, "green_circuit": 3, "steel_plate": 1}, "assembling"),
    "stone_furnace":            Recipe(0.5,  1,  {"stone": 5},                                               "assembling"),
    "steel_furnace":            Recipe(3.0,  1,  {"steel_plate": 6, "stone_brick": 10},                      "assembling"),
    "electric_furnace":         Recipe(5.0,  1,  {"advanced_circuit": 5, "steel_plate": 10, "stone_brick": 10}, "assembling"),
    "assembling_machine_1":     Recipe(0.5,  1,  {"green_circuit": 3, "iron_gear_wheel": 5, "iron_plate": 9},"assembling"),
    "assembling_machine_2":     Recipe(0.5,  1,  {"assembling_machine_1": 1, "green_circuit": 3, "iron_gear_wheel": 5, "steel_plate": 2}, "assembling"),
    "assembling_machine_3":     Recipe(0.5,  1,  {"assembling_machine_2": 2, "speed_module": 4},             "assembling"),
    "chemical_plant":           Recipe(5.0,  1,  {"green_circuit": 5, "iron_gear_wheel": 5, "pipe": 5, "steel_plate": 5}, "assembling"),
    "oil_refinery":             Recipe(8.0,  1,  {"green_circuit": 10, "iron_gear_wheel": 10, "pipe": 10, "steel_plate": 15, "stone_brick": 10}, "assembling"),
    "centrifuge":               Recipe(4.0,  1,  {"advanced_circuit": 100, "concrete": 100, "iron_gear_wheel": 100, "steel_plate": 50}, "assembling"),
    "lab":                      Recipe(2.0,  1,  {"green_circuit": 10, "iron_gear_wheel": 10, "transport_belt": 4}, "assembling"),
    "beacon":                   Recipe(15.0, 1,  {"advanced_circuit": 20, "copper_cable": 10, "green_circuit": 20, "steel_plate": 10}, "assembling"),
    "pump":                     Recipe(2.0,  1,  {"engine_unit": 1, "pipe": 1, "steel_plate": 1},            "assembling"),
    "offshore_pump":            Recipe(0.5,  1,  {"iron_gear_wheel": 2, "pipe": 3},                          "assembling"),
    "pumpjack":                 Recipe(5.0,  1,  {"green_circuit": 5, "iron_gear_wheel": 10, "pipe": 10, "steel_plate": 5}, "assembling"),
    "burner_mining_drill":      Recipe(2.0,  1,  {"iron_gear_wheel": 3, "iron_plate": 3, "stone_furnace": 1},"assembling"),
    "electric_mining_drill":    Recipe(2.0,  1,  {"green_circuit": 3, "iron_gear_wheel": 5, "iron_plate": 10}, "assembling"),
    "small_electric_pole":      Recipe(0.5,  2,  {"copper_cable": 2, "wood": 1},                             "assembling"),
    "medium_electric_pole":     Recipe(0.5,  1,  {"copper_cable": 2, "iron_stick": 4, "steel_plate": 2},     "assembling"),
    "big_electric_pole":        Recipe(0.5,  1,  {"copper_cable": 4, "iron_stick": 8, "steel_plate": 5},     "assembling"),
    "substation":               Recipe(0.5,  1,  {"advanced_circuit": 5, "copper_cable": 6, "steel_plate": 10}, "assembling"),
    "power_switch":             Recipe(2.0,  1,  {"copper_cable": 5, "green_circuit": 2, "iron_plate": 5},   "assembling"),
    "boiler":                   Recipe(0.5,  1,  {"pipe": 4, "stone_furnace": 1},                            "assembling"),
    "steam_engine":             Recipe(0.5,  1,  {"iron_gear_wheel": 8, "iron_plate": 10, "pipe": 5},        "assembling"),
    "steam_turbine":            Recipe(3.0,  1,  {"copper_plate": 50, "iron_gear_wheel": 50, "pipe": 20},    "assembling"),
    "solar_panel":              Recipe(10.0, 1,  {"copper_plate": 5, "green_circuit": 15, "steel_plate": 5}, "assembling"),
    "accumulator":              Recipe(10.0, 1,  {"battery": 5, "iron_plate": 2},                            "assembling"),
    "nuclear_reactor":          Recipe(8.0,  1,  {"advanced_circuit": 500, "concrete": 500, "copper_plate": 500, "steel_plate": 500}, "assembling"),
    "heat_exchanger":           Recipe(3.0,  1,  {"copper_plate": 100, "pipe": 10, "steel_plate": 10},       "assembling"),
    "heat_pipe":                Recipe(1.0,  1,  {"copper_plate": 20, "steel_plate": 10},                    "assembling"),
    "lamp":                     Recipe(0.5,  1,  {"copper_cable": 3, "green_circuit": 1, "iron_plate": 1},   "assembling"),
    "pipe_to_ground":           Recipe(0.5,  2,  {"iron_plate": 5, "pipe": 10},                              "assembling"),
    "storage_tank":             Recipe(3.0,  1,  {"iron_plate": 20, "steel_plate": 5},                       "assembling"),
    "rail":                     Recipe(0.5,  2,  {"iron_stick": 1, "steel_plate": 1, "stone": 1},            "assembling"),
    "locomotive":               Recipe(4.0,  1,  {"engine_unit": 20, "green_circuit": 10, "steel_plate": 30}, "assembling"),
    "cargo_wagon":              Recipe(1.0,  1,  {"iron_gear_wheel": 10, "iron_plate": 20, "steel_plate": 20}, "assembling"),
    "fluid_wagon":              Recipe(1.5,  1,  {"iron_gear_wheel": 10, "pipe": 8, "steel_plate": 16, "storage_tank": 1}, "assembling"),
    "artillery_wagon":          Recipe(4.0,  1,  {"advanced_circuit": 20, "engine_unit": 64, "iron_gear_wheel": 10, "pipe": 16, "steel_plate": 40}, "assembling"),
    "train_stop":               Recipe(0.5,  1,  {"green_circuit": 5, "iron_plate": 6, "iron_stick": 6, "steel_plate": 3}, "assembling"),
    "rail_signal":              Recipe(0.5,  1,  {"green_circuit": 1, "iron_plate": 5},                      "assembling"),
    "rail_chain_signal":        Recipe(0.5,  1,  {"green_circuit": 1, "iron_plate": 5},                      "assembling"),
    "speed_module":             Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "speed_module_2":           Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "speed_module": 4}, "assembling"),
    "speed_module_3":           Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "speed_module_2": 4}, "assembling"),
    "productivity_module":      Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "productivity_module_2":    Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "productivity_module": 4}, "assembling"),
    "productivity_module_3":    Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "productivity_module_2": 4}, "assembling"),
    "efficiency_module":        Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "efficiency_module_2":      Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "efficiency_module": 4}, "assembling"),
    "efficiency_module_3":      Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "efficiency_module_2": 4}, "assembling"),
    "pistol":                   Recipe(5.0,  1,  {"copper_plate": 5, "iron_plate": 5},                       "assembling"),
    "submachine_gun":           Recipe(10.0, 1,  {"copper_plate": 5, "iron_gear_wheel": 10, "iron_plate": 10}, "assembling"),
    "shotgun":                  Recipe(10.0, 1,  {"copper_plate": 10, "iron_gear_wheel": 5, "iron_plate": 15, "wood": 5}, "assembling"),
    "combat_shotgun":           Recipe(10.0, 1,  {"copper_plate": 10, "iron_gear_wheel": 5, "steel_plate": 15, "wood": 10}, "assembling"),
    "rocket_launcher":          Recipe(10.0, 1,  {"green_circuit": 5, "iron_gear_wheel": 5, "iron_plate": 5}, "assembling"),
    "flamethrower":             Recipe(10.0, 1,  {"iron_gear_wheel": 10, "steel_plate": 5},                  "assembling"),
    "firearm_magazine":         Recipe(1.0,  1,  {"iron_plate": 4},                                          "assembling"),
    "piercing_rounds_magazine": Recipe(3.0,  1,  {"copper_plate": 5, "firearm_magazine": 1, "steel_plate": 1}, "assembling"),
    "uranium_rounds_magazine":  Recipe(10.0, 1,  {"piercing_rounds_magazine": 1, "uranium_238": 1},          "assembling"),
    "shotgun_shells":           Recipe(3.0,  1,  {"copper_plate": 2, "iron_plate": 2},                       "assembling"),
    "piercing_shotgun_shells":  Recipe(8.0,  1,  {"copper_plate": 5, "shotgun_shells": 2, "steel_plate": 2}, "assembling"),
    "cannon_shell":             Recipe(8.0,  1,  {"explosives": 1, "plastic_bar": 2, "steel_plate": 2},      "assembling"),
    "explosive_cannon_shell":   Recipe(8.0,  1,  {"cannon_shell": 1, "explosives": 2},                       "assembling"),
    "uranium_cannon_shell":     Recipe(12.0, 1,  {"cannon_shell": 1, "uranium_238": 1},                      "assembling"),
    "explosive_uranium_cannon_shell": Recipe(12.0,1,{"explosive_cannon_shell":1,"uranium_238":1},             "assembling"),
    "artillery_shell":          Recipe(15.0, 1,  {"explosive_cannon_shell": 4, "explosives": 8, "radar": 1}, "assembling"),
    "rocket":                   Recipe(4.0,  1,  {"explosives": 1, "iron_plate": 2},                         "assembling"),
    "explosive_rocket":         Recipe(8.0,  1,  {"explosives": 2, "rocket": 1},                             "assembling"),
    "atomic_bomb":              Recipe(50.0, 1,  {"explosives": 10, "processing_unit": 10, "uranium_235": 30}, "assembling"),
    "grenade":                  Recipe(8.0,  1,  {"coal": 10, "iron_plate": 5},                              "assembling"),
    "cluster_grenade":          Recipe(8.0,  1,  {"explosives": 5, "grenade": 7, "steel_plate": 5},          "assembling"),
    "cliff_explosives":         Recipe(8.0,  1,  {"empty_barrel": 1, "explosives": 10, "grenade": 1},        "assembling"),
    "land_mine":                Recipe(5.0,  4,  {"explosives": 2, "steel_plate": 1},                        "assembling"),
    "poison_capsule":           Recipe(8.0,  1,  {"coal": 10, "green_circuit": 3, "steel_plate": 3},         "assembling"),
    "slowdown_capsule":         Recipe(8.0,  1,  {"coal": 5, "green_circuit": 2, "steel_plate": 2},          "assembling"),
    "defender_capsule":         Recipe(8.0,  1,  {"green_circuit": 3, "iron_gear_wheel": 3, "piercing_rounds_magazine": 3}, "assembling"),
    "distractor_capsule":       Recipe(15.0, 1,  {"advanced_circuit": 3, "defender_capsule": 4},             "assembling"),
    "destroyer_capsule":        Recipe(15.0, 1,  {"distractor_capsule": 4, "speed_module": 1},               "assembling"),
    "gun_turret":               Recipe(8.0,  1,  {"copper_plate": 10, "iron_gear_wheel": 10, "iron_plate": 20}, "assembling"),
    "laser_turret":             Recipe(20.0, 1,  {"battery": 12, "green_circuit": 20, "steel_plate": 20},    "assembling"),
    "flamethrower_turret":      Recipe(20.0, 1,  {"engine_unit": 5, "iron_gear_wheel": 15, "pipe": 10, "steel_plate": 30}, "assembling"),
    "artillery_turret":         Recipe(40.0, 1,  {"advanced_circuit": 20, "concrete": 60, "iron_gear_wheel": 40, "steel_plate": 60}, "assembling"),
    "radar":                    Recipe(0.5,  1,  {"green_circuit": 5, "iron_gear_wheel": 5, "iron_plate": 10}, "assembling"),
    "light_armor":              Recipe(3.0,  1,  {"iron_plate": 40},                                         "assembling"),
    "heavy_armor":              Recipe(8.0,  1,  {"copper_plate": 100, "steel_plate": 50},                   "assembling"),
    "modular_armor":            Recipe(15.0, 1,  {"advanced_circuit": 30, "steel_plate": 50},                "assembling"),
    "power_armor":              Recipe(20.0, 1,  {"electric_engine_unit": 20, "processing_unit": 40, "steel_plate": 40}, "assembling"),
    "power_armor_mk2":          Recipe(25.0, 1,  {"electric_engine_unit": 40, "efficiency_module_2": 25, "low_density_structure": 30, "processing_unit": 60, "speed_module_2": 25}, "assembling"),
    "energy_shield":            Recipe(10.0, 1,  {"advanced_circuit": 5, "steel_plate": 10},                 "assembling"),
    "energy_shield_mk2":        Recipe(10.0, 1,  {"energy_shield": 10, "low_density_structure": 5, "processing_unit": 5}, "assembling"),
    "personal_battery":         Recipe(10.0, 1,  {"battery": 5, "steel_plate": 10},                         "assembling"),
    "personal_battery_mk2":     Recipe(10.0, 1,  {"low_density_structure": 5, "personal_battery": 10, "processing_unit": 15}, "assembling"),
    "belt_immunity_equipment":  Recipe(10.0, 1,  {"advanced_circuit": 5, "steel_plate": 10},                 "assembling"),
    "exoskeleton":              Recipe(10.0, 1,  {"electric_engine_unit": 30, "processing_unit": 10, "steel_plate": 20}, "assembling"),
    "personal_roboport":        Recipe(10.0, 1,  {"advanced_circuit": 10, "battery": 45, "iron_gear_wheel": 40, "steel_plate": 20}, "assembling"),
    "personal_roboport_mk2":    Recipe(20.0, 1,  {"low_density_structure": 20, "personal_roboport": 5, "processing_unit": 100}, "assembling"),
    "nightvision":              Recipe(10.0, 1,  {"advanced_circuit": 5, "steel_plate": 10},                 "assembling"),
    "personal_laser_defense":   Recipe(10.0, 1,  {"laser_turret": 5, "low_density_structure": 5, "processing_unit": 20}, "assembling"),
    "discharge_defense":        Recipe(10.0, 1,  {"laser_turret": 10, "processing_unit": 5, "steel_plate": 20}, "assembling"),
    "portable_solar_panel":     Recipe(10.0, 1,  {"advanced_circuit": 2, "solar_panel": 1, "steel_plate": 5}, "assembling"),
    "portable_fission_reactor": Recipe(10.0, 1,  {"low_density_structure": 50, "processing_unit": 200, "uranium_fuel_cell": 4}, "assembling"),
    "uranium_fuel_cell":        Recipe(10.0, 10, {"iron_plate": 10, "uranium_235": 1, "uranium_238": 19},    "assembling"),
    "uranium_processing":       Recipe(12.0, 1,  {"uranium_ore": 10},                                        "centrifuge"),
    "kovarex_enrichment":       Recipe(60.0, 41, {"uranium_235": 40, "uranium_238": 5},                      "centrifuge"),
    "concrete":                 Recipe(10.0, 10, {"iron_ore": 1, "stone_brick": 5, "water": 100},            "chemical"),
    "hazard_concrete":          Recipe(0.25, 10, {"concrete": 10},                                           "assembling"),
    "refined_concrete":         Recipe(15.0, 10, {"concrete": 20, "iron_stick": 8, "steel_plate": 1, "water": 100}, "chemical"),
    "refined_hazard_concrete":  Recipe(0.25, 10, {"refined_concrete": 10},                                   "assembling"),
    "landfill":                 Recipe(0.5,  1,  {"stone": 50},                                              "assembling"),
    "rocket_silo":              Recipe(30.0, 1,  {"concrete": 1000, "electric_engine_unit": 200, "pipe": 100, "processing_unit": 200, "steel_plate": 1000}, "assembling"),
    "low_density_structure":    Recipe(15.0, 1,  {"copper_plate": 20, "plastic_bar": 5, "steel_plate": 2},  "assembling"),
    "rocket_part":              Recipe(3.0,  1,  {"low_density_structure": 10, "processing_unit": 10, "rocket_fuel": 10}, "rocket"),
    "satellite":                Recipe(5.0,  1,  {"accumulator": 100, "low_density_structure": 100, "processing_unit": 100, "radar": 5, "rocket_fuel": 50, "solar_panel": 100}, "assembling"),
    "arithmetic_combinator":    Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 5},                   "assembling"),
    "decider_combinator":       Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 5},                   "assembling"),
    "selector_combinator":      Recipe(0.5,  1,  {"advanced_circuit": 2, "decider_combinator": 5},          "assembling"),
    "constant_combinator":      Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 2},                   "assembling"),
    "programmable_speaker":     Recipe(2.0,  1,  {"copper_cable": 5, "green_circuit": 4, "iron_plate": 3, "iron_stick": 4}, "assembling"),
    "car":                      Recipe(2.0,  1,  {"engine_unit": 8, "iron_plate": 20, "steel_plate": 5},    "assembling"),
    "tank":                     Recipe(5.0,  1,  {"advanced_circuit": 10, "engine_unit": 32, "iron_gear_wheel": 15, "steel_plate": 50}, "assembling"),
    "spidertron":               Recipe(10.0, 1,  {"efficiency_module_3": 2, "exoskeleton": 4, "low_density_structure": 150, "portable_fission_reactor": 2, "processing_unit": 16, "radar": 2, "raw_fish": 1, "rocket_launcher": 4}, "assembling"),
    "repair_pack":              Recipe(0.5,  1,  {"green_circuit": 2, "iron_gear_wheel": 2},                 "assembling"),
    "wooden_chest":             Recipe(0.5,  1,  {"wood": 2},                                                "assembling"),
    "wall":                     Recipe(0.5,  1,  {"stone_brick": 5},                                         "assembling"),
}

RAW_ITEMS = frozenset({
    "iron_ore", "copper_ore", "coal", "stone", "wood",
    "crude_oil", "water", "petroleum_gas", "heavy_oil", "light_oil",
    "steam", "uranium_ore", "uranium_235", "uranium_238",
    "raw_fish", "solid_fuel",
})

ITEM_DISPLAY_NAME: dict[str, str] = {
    "iron_ore": "铁矿石", "copper_ore": "铜矿石", "coal": "煤",
    "stone": "石头", "wood": "木材", "crude_oil": "原油",
    "water": "水", "petroleum_gas": "石油气", "heavy_oil": "重油",
    "light_oil": "轻油", "steam": "蒸汽", "uranium_ore": "铀矿石",
    "uranium_235": "铀-235", "uranium_238": "铀-238",
    "raw_fish": "鱼", "solid_fuel": "固体燃料（外购）",
    "iron_plate": "铁板", "copper_plate": "铜板",
    "steel_plate": "钢板", "stone_brick": "石砖",
    "copper_cable": "铜线", "iron_gear_wheel": "铁齿轮",
    "iron_stick": "铁棍", "pipe": "管道", "empty_barrel": "空桶",
    "stone_wall": "石墙", "gate": "大门",
    "green_circuit": "绿电路（电子电路）",
    "advanced_circuit": "高级电路（红电路）",
    "processing_unit": "处理器（蓝电路）",
    "plastic_bar": "塑料条", "sulfur": "硫磺",
    "sulfuric_acid": "硫酸", "battery": "电池",
    "explosives": "炸药",
    "solid_fuel_from_light_oil": "固体燃料(轻油)",
    "solid_fuel_from_petroleum_gas": "固体燃料(石油气)",
    "solid_fuel_from_heavy_oil": "固体燃料(重油)",
    "lubricant": "润滑剂", "rocket_fuel": "火箭燃料",
    "nuclear_fuel": "核燃料",
    "petroleum_gas_basic": "基础炼油",
    "advanced_oil_processing": "高级炼油",
    "heavy_oil_cracking": "重油裂解",
    "light_oil_cracking": "轻油裂解",
    "coal_liquefaction": "煤液化",
    "automation_science_pack": "自动化科研包（红瓶）",
    "logistic_science_pack": "物流科研包（绿瓶）",
    "military_science_pack": "军事科研包（灰瓶）",
    "chemical_science_pack": "化学科研包（蓝瓶）",
    "production_science_pack": "生产科研包（紫瓶）",
    "utility_science_pack": "实用科研包（黄瓶）",
    "space_science_pack": "太空科研包（白瓶）",
    "transport_belt": "传送带", "fast_transport_belt": "快速传送带",
    "express_transport_belt": "极速传送带",
    "underground_belt": "地下传送带", "fast_underground_belt": "快速地下传送带",
    "express_underground_belt": "极速地下传送带",
    "splitter": "分配器", "fast_splitter": "快速分配器",
    "express_splitter": "极速分配器",
    "inserter": "插入臂", "burner_inserter": "燃料插入臂",
    "long_handed_inserter": "长臂插入臂",
    "fast_inserter": "快速插入臂", "filter_inserter": "过滤插入臂",
    "bulk_inserter": "堆叠插入臂",
    "logistic_robot": "物流机器人", "construction_robot": "建造机器人",
    "roboport": "机器人港口",
    "active_provider_chest": "主动提供箱", "passive_provider_chest": "被动提供箱",
    "requester_chest": "请求箱", "storage_chest": "存储箱",
    "buffer_chest": "缓冲箱", "steel_chest": "钢箱", "iron_chest": "铁箱",
    "engine_unit": "发动机组件", "electric_engine_unit": "电动发动机",
    "flying_robot_frame": "飞行机器人机架",
    "assembling_machine_1": "组装机1", "assembling_machine_2": "组装机2",
    "assembling_machine_3": "组装机3",
    "electric_furnace": "电炉", "steel_furnace": "钢炉",
    "stone_furnace": "石炉", "chemical_plant": "化工厂",
    "oil_refinery": "炼油厂", "pump": "泵", "offshore_pump": "近海泵",
    "pumpjack": "抽油机",
    "electric_mining_drill": "电动矿机", "burner_mining_drill": "燃料矿机",
    "small_electric_pole": "小型电杆",
    "medium_electric_pole": "中型电杆",
    "big_electric_pole": "大型电杆", "substation": "变电站",
    "power_switch": "电源开关",
    "boiler": "锅炉", "steam_engine": "蒸汽机", "steam_turbine": "蒸汽轮机",
    "solar_panel": "太阳能板", "accumulator": "蓄电器",
    "nuclear_reactor": "核反应堆", "heat_exchanger": "热交换器",
    "heat_pipe": "热管", "centrifuge": "离心机",
    "lamp": "灯",
    "pipe_to_ground": "地下管道", "storage_tank": "储液罐",
    "rail": "铁轨", "locomotive": "机车", "cargo_wagon": "货运车厢",
    "fluid_wagon": "液体车厢", "artillery_wagon": "榴弹炮车厢",
    "train_stop": "车站", "rail_signal": "轨道信号", "rail_chain_signal": "轨道链信号",
    "speed_module": "速度模块1", "speed_module_2": "速度模块2",
    "speed_module_3": "速度模块3",
    "productivity_module": "产能模块1", "productivity_module_2": "产能模块2",
    "productivity_module_3": "产能模块3",
    "efficiency_module": "效率模块1", "efficiency_module_2": "效率模块2",
    "efficiency_module_3": "效率模块3",
    "firearm_magazine": "弹匣", "piercing_rounds_magazine": "穿甲弹匣",
    "uranium_rounds_magazine": "铀弹匣",
    "shotgun_shells": "霰弹", "piercing_shotgun_shells": "穿甲霰弹",
    "cannon_shell": "炮弹", "explosive_cannon_shell": "爆炸炮弹",
    "uranium_cannon_shell": "铀炮弹",
    "explosive_uranium_cannon_shell": "爆炸铀炮弹",
    "artillery_shell": "榴弹炮炮弹",
    "rocket": "火箭弹", "explosive_rocket": "爆炸火箭弹",
    "atomic_bomb": "原子弹",
    "grenade": "手雷", "cluster_grenade": "集束手雷",
    "cliff_explosives": "悬崖炸药", "land_mine": "地雷",
    "poison_capsule": "毒气胶囊", "slowdown_capsule": "减速胶囊",
    "defender_capsule": "防卫胶囊", "distractor_capsule": "干扰胶囊",
    "destroyer_capsule": "毁灭胶囊",
    "pistol": "手枪", "submachine_gun": "冲锋枪",
    "shotgun": "霰弹枪", "combat_shotgun": "战斗霰弹枪",
    "rocket_launcher": "火箭筒", "flamethrower": "火焰喷射器",
    "flamethrower_ammo": "火焰喷射器弹药",
    "gun_turret": "枪炮塔", "laser_turret": "激光炮塔",
    "flamethrower_turret": "火焰炮塔", "artillery_turret": "榴弹炮塔",
    "radar": "雷达",
    "light_armor": "轻甲", "heavy_armor": "重甲",
    "modular_armor": "模块甲", "power_armor": "动力甲",
    "power_armor_mk2": "动力甲MK2",
    "energy_shield": "能量护盾", "energy_shield_mk2": "能量护盾MK2",
    "personal_battery": "个人电池", "personal_battery_mk2": "个人电池MK2",
    "belt_immunity_equipment": "传送带免疫",
    "exoskeleton": "外骨骼",
    "personal_roboport": "个人机器人港口",
    "personal_roboport_mk2": "个人机器人港口MK2",
    "nightvision": "夜视仪",
    "personal_laser_defense": "个人激光防御",
    "discharge_defense": "放电防御",
    "portable_solar_panel": "便携太阳能板",
    "portable_fission_reactor": "便携裂变反应堆",
    "uranium_fuel_cell": "铀燃料棒",
    "uranium_processing": "铀处理",
    "kovarex_enrichment": "科瓦雷克浓缩",
    "concrete": "混凝土", "hazard_concrete": "警示混凝土",
    "refined_concrete": "精炼混凝土", "refined_hazard_concrete": "精炼警示混凝土",
    "landfill": "填海石",
    "rocket_silo": "火箭发射井",
    "low_density_structure": "低密度结构",
    "rocket_part": "火箭零件", "satellite": "卫星",
    "arithmetic_combinator": "算术组合器", "decider_combinator": "判定组合器",
    "selector_combinator": "选择器组合器",
    "constant_combinator": "常量组合器", "programmable_speaker": "可编程扬声器",
    "car": "汽车", "tank": "坦克", "spidertron": "蜘蛛机器人",
    "repair_pack": "维修包", "wooden_chest": "木箱", "wall": "石墙（wall）",
    "lab": "实验室", "beacon": "信标",
}

MACHINE_NAME: dict[str, str] = {
    "assembling": "组装机",
    "furnace":    "熔炉",
    "chemical":   "化工厂",
    "refinery":   "炼油厂",
    "centrifuge": "离心机",
    "rocket":     "火箭发射井",
    "mining":     "矿机",
}

MACHINE_SPEED_MAP: dict[str, float] = {
    "assembling": -1,
    "furnace":    FURNACE_SPEED,
    "chemical":   CHEM_PLANT_SPEED,
    "refinery":   OIL_REFINERY_SPEED,
    "centrifuge": CENTRIFUGE_SPEED,
    "rocket":     ROCKET_SILO_SPEED,
    "mining":     MINING_SPEED,
}

ITEM_CATEGORIES: dict[str, list[str]] = {
    "⚗️  科研包":       ["automation_science_pack","logistic_science_pack","military_science_pack",
                        "chemical_science_pack","production_science_pack","utility_science_pack","space_science_pack"],
    "🔌  电路板":        ["green_circuit","advanced_circuit","processing_unit"],
    "🏭  冶炼品":        ["iron_plate","copper_plate","steel_plate","stone_brick"],
    "🔧  基础零件":      ["copper_cable","iron_gear_wheel","iron_stick","pipe","empty_barrel","stone_wall","gate"],
    "🧪  化工品":        ["plastic_bar","sulfur","sulfuric_acid","battery","explosives",
                        "lubricant","rocket_fuel","nuclear_fuel","solid_fuel_from_light_oil",
                        "solid_fuel_from_heavy_oil","solid_fuel_from_petroleum_gas"],
    "🛢️  炼油":          ["petroleum_gas_basic","advanced_oil_processing","heavy_oil_cracking","light_oil_cracking","coal_liquefaction"],
    "🚛  传送带 & 物流":  ["transport_belt","fast_transport_belt","express_transport_belt",
                        "underground_belt","fast_underground_belt","express_underground_belt",
                        "splitter","fast_splitter","express_splitter"],
    "🤖  机器人":        ["logistic_robot","construction_robot","roboport",
                        "active_provider_chest","passive_provider_chest","requester_chest",
                        "storage_chest","buffer_chest","steel_chest","iron_chest"],
    "🔌  电力设备":      ["small_electric_pole","medium_electric_pole","big_electric_pole","substation",
                        "power_switch","boiler","steam_engine","steam_turbine","solar_panel",
                        "accumulator","nuclear_reactor","heat_exchanger","heat_pipe","centrifuge","lamp"],
    "⚙️  机械 & 建筑":   ["engine_unit","electric_engine_unit","flying_robot_frame",
                        "assembling_machine_1","assembling_machine_2","assembling_machine_3",
                        "electric_furnace","steel_furnace","stone_furnace","chemical_plant",
                        "oil_refinery","pump","offshore_pump","pumpjack","lab","beacon",
                        "electric_mining_drill","burner_mining_drill"],
    "🚂  铁路":          ["rail","locomotive","cargo_wagon","fluid_wagon","artillery_wagon",
                        "train_stop","rail_signal","rail_chain_signal"],
    "🦾  插入臂":        ["inserter","burner_inserter","long_handed_inserter","fast_inserter",
                        "filter_inserter","bulk_inserter"],
    "📦  管道 & 储罐":   ["pipe_to_ground","storage_tank"],
    "💣  武器 & 弹药":   ["firearm_magazine","piercing_rounds_magazine","uranium_rounds_magazine",
                        "shotgun_shells","piercing_shotgun_shells","cannon_shell",
                        "explosive_cannon_shell","uranium_cannon_shell","explosive_uranium_cannon_shell",
                        "artillery_shell","grenade","cluster_grenade","cliff_explosives",
                        "rocket","explosive_rocket","atomic_bomb","land_mine",
                        "poison_capsule","slowdown_capsule",
                        "defender_capsule","distractor_capsule","destroyer_capsule",
                        "rocket_launcher","shotgun","combat_shotgun","pistol","submachine_gun","flamethrower","flamethrower_ammo"],
    "🛡️  装备":          ["light_armor","heavy_armor","modular_armor","power_armor","power_armor_mk2",
                        "energy_shield","energy_shield_mk2","personal_battery","personal_battery_mk2",
                        "belt_immunity_equipment","exoskeleton","personal_roboport","personal_roboport_mk2",
                        "nightvision","personal_laser_defense","discharge_defense",
                        "portable_solar_panel","portable_fission_reactor"],
    "🏰  防御设施":      ["gun_turret","laser_turret","flamethrower_turret","artillery_turret","radar","land_mine"],
    "☢️  核能":          ["uranium_fuel_cell","uranium_processing","kovarex_enrichment"],
    "🏗️  建材":          ["concrete","hazard_concrete","refined_concrete","refined_hazard_concrete","landfill"],
    "🚀  火箭":          ["rocket_silo","low_density_structure","rocket_part","satellite"],
    "📡  电路网络":      ["arithmetic_combinator","decider_combinator","selector_combinator","constant_combinator","programmable_speaker"],
    "📦  模块":          ["speed_module","speed_module_2","speed_module_3",
                        "productivity_module","productivity_module_2","productivity_module_3",
                        "efficiency_module","efficiency_module_2","efficiency_module_3"],
    "🚗  载具":          ["car","tank","spidertron"],
    "🌲  木材制品":      ["wooden_chest","repair_pack"],
}

# ═══════════════════════════════════════════════════════════
#  核心计算逻辑
# ═══════════════════════════════════════════════════════════
def get_machine_speed(category: str, assembling_level: int) -> float:
    if category == "assembling":
        return ASSEMBLING_SPEED.get(assembling_level, 0.75)
    return MACHINE_SPEED_MAP.get(category, 1.0)


@dataclass
class ProductionPlan:
    machines:     dict[str, int]   = field(default_factory=dict)
    actual_rates: dict[str, float] = field(default_factory=dict)
    raw_demand:   dict[str, float] = field(default_factory=dict)


def compute_plan(
    item: str,
    target_per_sec: float,
    assembling_level: int,
    plan: Optional[ProductionPlan] = None,
) -> ProductionPlan:
    if plan is None:
        plan = ProductionPlan()

    if item in RAW_ITEMS or item not in RECIPES:
        plan.raw_demand[item] = plan.raw_demand.get(item, 0.0) + target_per_sec
        return plan

    recipe = RECIPES[item]
    speed  = get_machine_speed(recipe.category, assembling_level)
    rate_per_machine = (recipe.output * speed) / recipe.time
    count  = math.ceil(target_per_sec / rate_per_machine)
    actual = count * rate_per_machine

    plan.machines[item]      = plan.machines.get(item, 0) + count
    plan.actual_rates[item]  = plan.actual_rates.get(item, 0.0) + actual

    for dep, qty in recipe.inputs.items():
        compute_plan(dep, actual * (qty / recipe.output), assembling_level, plan)

    return plan


# ═══════════════════════════════════════════════════════════
#  主题颜色
# ═══════════════════════════════════════════════════════════
BG       = "#16181f"
BG2      = "#1f2230"
BG3      = "#282d40"
BG4      = "#313650"
ACCENT   = "#f5a623"
ACCENT2  = "#d4881a"
FG       = "#dde2f0"
FG_DIM   = "#7a82a0"
FG_BRIGHT= "#ffffff"
GREEN    = "#50c878"
BLUE     = "#6ab0e8"
RED      = "#e05c5c"
CYAN     = "#50c8c8"
GOLD     = "#f5c842"

# 字体 —— 更大更清晰
FONT_TITLE  = ("Microsoft YaHei UI", 14, "bold")
FONT_HEAD   = ("Microsoft YaHei UI", 11, "bold")
FONT_BODY   = ("Microsoft YaHei UI", 10)
FONT_SMALL  = ("Microsoft YaHei UI", 9)
FONT_MONO   = ("Consolas", 10)
FONT_SEARCH = ("Microsoft YaHei UI", 11)
FONT_NUM    = ("Consolas", 11, "bold")

ROW_H = 26  # 行高


class FactorioCalc(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("异星工厂 产线计算器  v4  (Vanilla 1.1)")
        self.geometry("1380x860")
        self.minsize(1100, 680)
        self.configure(bg=BG)
        self._selected_item: Optional[str] = None
        # 多目标: list of {"item":str, "rate_var":StringVar, "unit_var":StringVar}
        self._targets: list[dict] = []
        self._build_ui()
        self._populate_list()

    # ─────────────── UI 构建 ───────────────
    def _build_ui(self):
        self._style()

        # ── 顶栏
        top = tk.Frame(self, bg=BG, pady=8)
        top.pack(fill="x", padx=14)
        tk.Label(top, text="⚙  异星工厂  产线计算器",
                 font=("Microsoft YaHei UI", 16, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(top, text="Factorio Vanilla 1.1 · 全配方 · 多目标合并计算",
                 font=FONT_BODY, bg=BG, fg=FG_DIM).pack(side="left", padx=14)

        # ── 主区域
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._build_left(main)
        self._build_right(main)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox",
                    fieldbackground=BG3, background=BG3,
                    foreground=FG, selectbackground=BG3,
                    arrowcolor=ACCENT, bordercolor=BG3, relief="flat")
        s.configure("Accent.TButton",
                    background=ACCENT, foreground="#16181f",
                    font=("Microsoft YaHei UI", 11, "bold"),
                    relief="flat", padding=(10, 5))
        s.map("Accent.TButton", background=[("active", ACCENT2)])
        s.configure("Del.TButton",
                    background="#4a1515", foreground=FG,
                    font=("Microsoft YaHei UI", 10, "bold"),
                    relief="flat", padding=(5, 3))
        s.map("Del.TButton", background=[("active", RED)])
        s.configure("Calc.TButton",
                    background="#1a3a52", foreground=BLUE,
                    font=("Microsoft YaHei UI", 10),
                    relief="flat", padding=(6, 3))
        s.map("Calc.TButton", background=[("active", "#224a68")])

    def _build_left(self, parent):
        lf = tk.Frame(parent, bg=BG2, width=310,
                      highlightbackground=BG4, highlightthickness=1)
        lf.pack(side="left", fill="y", padx=(0, 10), pady=4)
        lf.pack_propagate(False)

        # 搜索框
        tk.Label(lf, text="🔍  搜索物品", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", padx=12, pady=(12, 3))
        sf = tk.Frame(lf, bg=BG3, padx=2, pady=2)
        sf.pack(fill="x", padx=10, pady=(0, 8))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        tk.Entry(sf, textvariable=self._search_var,
                 bg=BG3, fg=FG_BRIGHT, insertbackground=ACCENT,
                 relief="flat", font=FONT_SEARCH, bd=6).pack(fill="x")

        tk.Label(lf, text="双击物品直接添加（默认1个/分）",
                 font=FONT_SMALL, bg=BG2, fg=FG_DIM).pack(anchor="w", padx=12)

        # 物品列表
        frame = tk.Frame(lf, bg=BG2)
        frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        scroll = tk.Scrollbar(frame, bg=BG3, troughcolor=BG2, relief="flat", width=6)
        self._listbox = tk.Listbox(
            frame, bg=BG2, fg=FG, selectbackground=BG4,
            selectforeground=ACCENT, activestyle="none",
            relief="flat", borderwidth=0,
            font=FONT_BODY, highlightthickness=0,
            yscrollcommand=scroll.set,
        )
        scroll.config(command=self._listbox.yview)
        self._listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Double-Button-1>", self._on_double_click)

    def _build_right(self, parent):
        rf = tk.Frame(parent, bg=BG)
        rf.pack(side="left", fill="both", expand=True, pady=4)

        # ── 上半：目标列表区
        top_frame = tk.Frame(rf, bg=BG2,
                             highlightbackground=BG4, highlightthickness=1)
        top_frame.pack(fill="x", pady=(0, 10))

        # 标题栏
        hdr = tk.Frame(top_frame, bg=BG2)
        hdr.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(hdr, text="📋  生产目标列表", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left")

        # 组装机等级（全局）
        lvl_f = tk.Frame(hdr, bg=BG2)
        lvl_f.pack(side="right")
        tk.Label(lvl_f, text="组装机等级：", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(side="left")
        self._level_var = tk.StringVar(value="2")
        for val, label, clr in [("1","  Lv.1  ",FG_DIM),("2","  Lv.2  ",GREEN),("3","  Lv.3  ",CYAN)]:
            tk.Radiobutton(
                lvl_f, text=label, variable=self._level_var, value=val,
                bg=BG2, fg=clr, selectcolor=BG4,
                activebackground=BG2, activeforeground=ACCENT,
                font=FONT_HEAD, indicatoron=1,
            ).pack(side="left", padx=2)

        # ── 目标表格标题
        hdr2 = tk.Frame(top_frame, bg=BG3)
        hdr2.pack(fill="x", padx=10)
        for txt, w, anchor in [
            ("物品名称", 28, "w"), ("产量", 9, "e"), ("单位", 8, "w"), ("操作", 5, "c")
        ]:
            tk.Label(hdr2, text=txt, font=FONT_HEAD, bg=BG3, fg=FG_DIM,
                     width=w, anchor=anchor).pack(side="left", padx=4, pady=3)

        # 目标行容器（可滚动）
        tbl_outer = tk.Frame(top_frame, bg=BG2)
        tbl_outer.pack(fill="x", padx=10, pady=(0, 4))
        self._tgt_canvas = tk.Canvas(tbl_outer, bg=BG2, height=160,
                                     highlightthickness=0)
        tgt_scroll = tk.Scrollbar(tbl_outer, orient="vertical",
                                  command=self._tgt_canvas.yview,
                                  bg=BG3, troughcolor=BG2, relief="flat", width=6)
        self._tgt_canvas.configure(yscrollcommand=tgt_scroll.set)
        tgt_scroll.pack(side="right", fill="y")
        self._tgt_canvas.pack(fill="x")
        self._tgt_inner = tk.Frame(self._tgt_canvas, bg=BG2)
        self._tgt_canvas_win = self._tgt_canvas.create_window(
            (0, 0), window=self._tgt_inner, anchor="nw")
        self._tgt_inner.bind("<Configure>", self._on_tgt_configure)
        self._tgt_canvas.bind("<Configure>",
            lambda e: self._tgt_canvas.itemconfig(self._tgt_canvas_win, width=e.width))

        # ── 按钮行
        btn_row = tk.Frame(top_frame, bg=BG2)
        btn_row.pack(fill="x", padx=12, pady=(2, 10))

        self._selected_label = tk.Label(
            btn_row, text="← 请从左侧选择物品（或双击快速添加）",
            font=FONT_BODY, bg=BG2, fg=FG_DIM, anchor="w", width=38)
        self._selected_label.pack(side="left")

        tk.Label(btn_row, text="产量", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(side="left", padx=(8, 4))
        self._rate_var = tk.StringVar(value="1")
        tk.Entry(btn_row, textvariable=self._rate_var,
                 width=7, bg=BG3, fg=FG_BRIGHT, insertbackground=ACCENT,
                 relief="flat", font=FONT_SEARCH, bd=4
                 ).pack(side="left")
        self._unit_var = tk.StringVar(value="个/分")
        unit_om = tk.OptionMenu(btn_row, self._unit_var, "个/秒", "个/分")
        unit_om.config(bg=BG3, fg=FG, activebackground=BG4,
                       activeforeground=FG, highlightthickness=0,
                       relief="flat", font=FONT_BODY, width=5)
        unit_om["menu"].config(bg=BG3, fg=FG, font=FONT_BODY)
        unit_om.pack(side="left", padx=(2, 10))

        tk.Button(btn_row, text="＋  添加",
                  bg="#1a3a20", fg=GREEN, activebackground="#225228",
                  activeforeground=FG_BRIGHT,
                  relief="flat", bd=0, padx=10, pady=4,
                  font=FONT_HEAD, cursor="hand2",
                  command=self._add_target).pack(side="left", padx=(0, 6))

        tk.Button(btn_row, text="清空",
                  bg="#3a1515", fg=RED, activebackground="#501515",
                  activeforeground=FG_BRIGHT,
                  relief="flat", bd=0, padx=8, pady=4,
                  font=FONT_HEAD, cursor="hand2",
                  command=self._clear_targets).pack(side="left", padx=(0, 20))

        tk.Button(btn_row, text="  ▶  开始计算  ",
                  bg=ACCENT, fg="#16181f", activebackground=ACCENT2,
                  activeforeground="#16181f",
                  relief="flat", bd=0, padx=14, pady=5,
                  font=("Microsoft YaHei UI", 12, "bold"), cursor="hand2",
                  command=self._calculate).pack(side="left")

        # ── 下半：结果 Notebook
        nb = ttk.Notebook(rf)
        nb.pack(fill="both", expand=True)

        s = ttk.Style()
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=BG3, foreground=FG_DIM,
                    font=FONT_HEAD, padding=(12, 5))
        s.map("TNotebook.Tab",
              background=[("selected", BG2)],
              foreground=[("selected", ACCENT)])

        self._machine_frame = tk.Frame(nb, bg=BG2)
        self._raw_frame     = tk.Frame(nb, bg=BG2)
        self._tree_frame    = tk.Frame(nb, bg=BG2)

        nb.add(self._machine_frame, text="🏭  机器需求")
        nb.add(self._raw_frame,     text="⛏️  原料需求")
        nb.add(self._tree_frame,    text="🌲  配方展开")

        self._build_machine_tab()
        self._build_raw_tab()
        self._build_tree_tab()

    def _on_tgt_configure(self, _e=None):
        self._tgt_canvas.configure(scrollregion=self._tgt_canvas.bbox("all"))

    # ─────────────── 目标管理 ───────────────
    def _add_target(self, item=None, rate=1.0, unit="个/分"):
        if item is None:
            item = self._selected_item
        if not item:
            messagebox.showwarning("提示", "请先从左侧选择一个物品")
            return
        if item not in RECIPES:
            messagebox.showwarning("提示", f"「{ITEM_DISPLAY_NAME.get(item,item)}」是原料，无需计算")
            return
        try:
            r = float(self._rate_var.get()) if item == self._selected_item else rate
            if r <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "请输入大于 0 的产量")
            return

        u = self._unit_var.get() if item == self._selected_item else unit
        rate_var = tk.StringVar(value=f"{r:.4g}")
        unit_var = tk.StringVar(value=u)
        self._targets.append({"item": item, "rate_var": rate_var, "unit_var": unit_var})
        self._refresh_target_rows()

    def _on_double_click(self, _event=None):
        """双击物品列表直接添加，默认1个/分"""
        sel = self._listbox.curselection()
        if not sel:
            return
        q = self._search_var.get().strip().lower()
        if q:
            filtered = [(d.strip(), k) for d, k in self._list_data
                        if k != "__cat__" and
                        (q in ITEM_DISPLAY_NAME.get(k, k).lower() or q in k.lower())]
            if sel[0] < len(filtered):
                key = filtered[sel[0]][1]
            else:
                return
        else:
            idx = sel[0]
            if idx >= len(self._list_data):
                return
            _, key = self._list_data[idx]
            if key == "__cat__":
                return
        self._selected_item = key
        name  = ITEM_DISPLAY_NAME.get(key, key)
        cat   = RECIPES[key].category if key in RECIPES else "raw"
        mname = MACHINE_NAME.get(cat, cat)
        self._selected_label.config(text=f"✅  {name}  [{mname}]", fg=ACCENT)
        # 直接添加
        self._add_target(item=key, rate=1.0, unit="个/分")

    def _remove_target(self, idx: int):
        if 0 <= idx < len(self._targets):
            del self._targets[idx]
            self._refresh_target_rows()

    def _clear_targets(self):
        self._targets.clear()
        self._refresh_target_rows()

    def _refresh_target_rows(self):
        for w in self._tgt_inner.winfo_children():
            w.destroy()

        if not self._targets:
            tk.Label(self._tgt_inner, text="（列表为空，请添加目标或双击左侧物品快速添加）",
                     bg=BG2, fg=FG_DIM, font=FONT_BODY).pack(padx=10, pady=10)
            self._on_tgt_configure()
            return

        for i, tgt in enumerate(self._targets):
            row_bg = BG2 if i % 2 == 0 else BG3
            row = tk.Frame(self._tgt_inner, bg=row_bg)
            row.pack(fill="x")

            name = ITEM_DISPLAY_NAME.get(tgt["item"], tgt["item"])
            cat  = RECIPES[tgt["item"]].category if tgt["item"] in RECIPES else ""
            mname = MACHINE_NAME.get(cat, "")

            # 物品名
            tk.Label(row, text=f"{name}",
                     bg=row_bg, fg=FG_BRIGHT, font=FONT_BODY,
                     width=22, anchor="w").pack(side="left", padx=(8, 2), pady=4)
            tk.Label(row, text=f"[{mname}]",
                     bg=row_bg, fg=FG_DIM, font=FONT_SMALL,
                     width=6, anchor="w").pack(side="left", padx=(0, 4))

            # 产量输入框（可直接编辑）
            e = tk.Entry(row, textvariable=tgt["rate_var"],
                         width=8, bg=BG4, fg=GOLD,
                         insertbackground=ACCENT,
                         relief="flat", font=FONT_NUM, bd=3,
                         justify="right")
            e.pack(side="left", padx=2)

            # 单位下拉
            um = tk.OptionMenu(row, tgt["unit_var"], "个/秒", "个/分")
            um.config(bg=BG4, fg=FG, activebackground=BG3,
                      activeforeground=FG, highlightthickness=0,
                      relief="flat", font=FONT_SMALL, width=5,
                      cursor="hand2")
            um["menu"].config(bg=BG3, fg=FG, font=FONT_BODY)
            um.pack(side="left", padx=4)

            # 删除按钮
            idx = i
            tk.Button(
                row, text=" ✕ ", font=("Microsoft YaHei UI", 9, "bold"),
                bg="#4a1a1a", fg="#ff8888",
                activebackground=RED, activeforeground=FG_BRIGHT,
                relief="flat", bd=0, cursor="hand2",
                command=lambda x=idx: self._remove_target(x)
            ).pack(side="left", padx=6)

        self._on_tgt_configure()

    # ─────────────── 结果标签页 ───────────────
    def _build_machine_tab(self):
        cols = ("物品", "机器类型", "台数", "实际产出/s", "实际产出/min")
        self._machine_tree = self._make_tree(self._machine_frame, cols,
                                              widths=[240, 100, 80, 110, 110])

    def _build_raw_tab(self):
        cols = ("原料", "需求量/s", "需求量/min")
        self._raw_tree = self._make_tree(self._raw_frame, cols,
                                         widths=[260, 120, 120])

    def _build_tree_tab(self):
        f = tk.Frame(self._tree_frame, bg=BG2)
        f.pack(fill="both", expand=True)
        self._tree_text = tk.Text(
            f, bg=BG2, fg=FG,
            font=FONT_MONO, relief="flat",
            selectbackground=BG3, wrap="none",
            state="disabled",
        )
        self._tree_text.tag_configure("header",  foreground=ACCENT,  font=("Consolas", 11, "bold"))
        self._tree_text.tag_configure("target",  foreground=GOLD,    font=("Consolas", 11, "bold"))
        self._tree_text.tag_configure("machine", foreground=CYAN,    font=FONT_MONO)
        self._tree_text.tag_configure("raw",     foreground=GREEN,   font=FONT_MONO)
        sb_y = tk.Scrollbar(f, orient="vertical",   command=self._tree_text.yview,
                            bg=BG3, troughcolor=BG2, relief="flat", width=6)
        sb_x = tk.Scrollbar(f, orient="horizontal", command=self._tree_text.xview,
                            bg=BG3, troughcolor=BG2, relief="flat")
        self._tree_text.config(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self._tree_text.pack(fill="both", expand=True)

    def _make_tree(self, parent, cols, widths=None):
        s = ttk.Style()
        s.configure("Dark.Treeview",
                    background=BG2, foreground=FG,
                    fieldbackground=BG2,
                    rowheight=28, font=FONT_BODY,
                    borderwidth=0)
        s.configure("Dark.Treeview.Heading",
                    background=BG3, foreground=ACCENT,
                    font=FONT_HEAD, relief="flat")
        s.map("Dark.Treeview",
              background=[("selected", BG4)],
              foreground=[("selected", FG_BRIGHT)])

        frame = tk.Frame(parent, bg=BG2)
        frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(frame, bg=BG3, troughcolor=BG2, relief="flat", width=6)
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview",
                            yscrollcommand=sb.set)
        sb.config(command=tree.yview)

        for i, col in enumerate(cols):
            tree.heading(col, text=col)
            w = widths[i] if widths and i < len(widths) else 150
            anchor = "e" if any(x in col for x in ["产出", "需求", "台数"]) else "w"
            tree.column(col, width=w, anchor=anchor, minwidth=60)

        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tree.tag_configure("odd",     background=BG2, foreground=FG)
        tree.tag_configure("even",    background=BG3, foreground=FG)
        tree.tag_configure("total",   background=BG4, foreground=GOLD,
                                       font=("Microsoft YaHei UI", 11, "bold"))
        tree.tag_configure("subtotal",background="#1a2840", foreground=BLUE,
                                       font=("Microsoft YaHei UI", 10, "bold"))
        return tree

    # ─────────────── 物品列表 ───────────────
    def _populate_list(self):
        self._list_data: list[tuple[str, str]] = []
        for cat, items in ITEM_CATEGORIES.items():
            self._list_data.append((cat, "__cat__"))
            for key in items:
                if key in RECIPES:
                    name = ITEM_DISPLAY_NAME.get(key, key)
                    self._list_data.append((f"   {name}", key))
        self._render_list(self._list_data)

    def _render_list(self, data: list[tuple[str, str]]):
        self._listbox.delete(0, "end")
        for display, key in data:
            self._listbox.insert("end", display)
            if key == "__cat__":
                idx = self._listbox.size() - 1
                self._listbox.itemconfig(idx, fg=ACCENT,
                                         selectbackground=BG2,
                                         selectforeground=ACCENT)

    def _filter_list(self):
        q = self._search_var.get().strip().lower()
        if not q:
            self._render_list(self._list_data)
            return
        filtered = []
        for display, key in self._list_data:
            if key == "__cat__":
                continue
            name_cn = ITEM_DISPLAY_NAME.get(key, key).lower()
            if q in name_cn or q in key.lower():
                filtered.append((display.strip(), key))
        self._render_list(filtered)

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        q = self._search_var.get().strip().lower()
        if q:
            filtered = [(d.strip(), k) for d, k in self._list_data
                        if k != "__cat__" and
                        (q in ITEM_DISPLAY_NAME.get(k, k).lower() or q in k.lower())]
            if sel[0] < len(filtered):
                key = filtered[sel[0]][1]
            else:
                return
        else:
            idx = sel[0]
            if idx >= len(self._list_data):
                return
            _, key = self._list_data[idx]
            if key == "__cat__":
                return

        self._selected_item = key
        name  = ITEM_DISPLAY_NAME.get(key, key)
        cat   = RECIPES[key].category if key in RECIPES else "raw"
        mname = MACHINE_NAME.get(cat, cat)
        self._selected_label.config(text=f"✅  {name}  [{mname}]", fg=ACCENT)

    # ─────────────── 合并计算 ───────────────
    def _calculate(self):
        if not self._targets:
            messagebox.showwarning("提示", "请先添加至少一个生产目标")
            return

        # 验证产量
        targets_ok = []
        for tgt in self._targets:
            try:
                rate = float(tgt["rate_var"].get())
                if rate <= 0:
                    raise ValueError()
                targets_ok.append((tgt["item"], rate, tgt["unit_var"].get()))
            except ValueError:
                name = ITEM_DISPLAY_NAME.get(tgt["item"], tgt["item"])
                messagebox.showerror("错误", f"「{name}」的产量无效，请检查输入")
                return

        level = int(self._level_var.get())
        merged = ProductionPlan()
        for item, rate, unit in targets_ok:
            per_sec = rate if unit == "个/秒" else rate / 60.0
            compute_plan(item, per_sec, level, merged)

        self._show_machine_results(merged, level)
        self._show_raw_results(merged)
        self._show_tree_multi(targets_ok, level)

    def _show_machine_results(self, plan: ProductionPlan, level: int):
        tree = self._machine_tree
        tree.delete(*tree.get_children())

        by_cat: dict[str, list] = defaultdict(list)
        for item, count in plan.machines.items():
            cat = RECIPES[item].category if item in RECIPES else "?"
            by_cat[cat].append((item, count, plan.actual_rates.get(item, 0)))

        row_idx = 0
        cat_order = ("assembling", "furnace", "chemical", "refinery", "centrifuge", "rocket")
        grand_total_assembling = 0

        for cat in cat_order:
            entries = by_cat.get(cat, [])
            if not entries:
                continue
            mname = MACHINE_NAME.get(cat, cat)
            cat_total = sum(c for _, c, _ in entries)

            for item, count, rate in sorted(entries, key=lambda x: -x[2]):
                name = ITEM_DISPLAY_NAME.get(item, item)
                tag  = "odd" if row_idx % 2 == 0 else "even"
                tree.insert("", "end", tags=(tag,), values=(
                    name, mname,
                    f"{count}",
                    f"{rate:.3f}",
                    f"{rate*60:.2f}",
                ))
                row_idx += 1

            # 每类小计
            tree.insert("", "end", tags=("subtotal",), values=(
                f"──  {mname} 小计", "",
                f"▶ {cat_total} 台",
                "", "",
            ))
            row_idx += 1

            if cat == "assembling":
                grand_total_assembling = cat_total

        # 组装机总计（如果有多类）
        all_total = sum(c for _, entries in by_cat.items() for _, c, _ in entries)
        # 全部机器总计行
        tree.insert("", "end", tags=("total",), values=(
            "═══  全部机器合计", "",
            f"◆ {all_total} 台",
            "", "",
        ))

    def _show_raw_results(self, plan: ProductionPlan):
        tree = self._raw_tree
        tree.delete(*tree.get_children())
        total_entries = sorted(plan.raw_demand.items(), key=lambda x: -x[1])
        for i, (item, rate) in enumerate(total_entries):
            name = ITEM_DISPLAY_NAME.get(item, item)
            tag  = "odd" if i % 2 == 0 else "even"
            tree.insert("", "end", tags=(tag,), values=(
                name,
                f"{rate:.4f}",
                f"{rate*60:.2f}",
            ))
        # 合计种类
        tree.insert("", "end", tags=("total",), values=(
            f"──  共 {len(total_entries)} 种原料", "", "",
        ))

    def _show_tree_multi(self, targets_ok, level: int):
        t = self._tree_text
        t.config(state="normal")
        t.delete("1.0", "end")

        sep = "═" * 60 + "\n"
        t.insert("end", sep, "header")
        t.insert("end", "  合并产线  —  配方展开\n", "header")
        t.insert("end", sep, "header")

        for item, rate, unit in targets_ok:
            per_sec = rate if unit == "个/秒" else rate / 60.0
            name = ITEM_DISPLAY_NAME.get(item, item)
            t.insert("end", f"\n▶  {name}   {rate:.4g} {unit}\n", "target")
            t.insert("end", "─" * 50 + "\n", "header")
            self._append_tree_colored(item, per_sec, level, 0, t)

        t.config(state="disabled")

    def _append_tree_colored(self, item: str, per_sec: float, level: int,
                              depth: int, t: tk.Text):
        indent = "  " * depth
        prefix = indent + ("└─ " if depth > 0 else "")
        if item in RAW_ITEMS or item not in RECIPES:
            name = ITEM_DISPLAY_NAME.get(item, item)
            t.insert("end", f"{prefix}[原料] {name}  {per_sec:.3f}/s\n", "raw")
            return

        recipe = RECIPES[item]
        speed  = get_machine_speed(recipe.category, level)
        rate_pm = (recipe.output * speed) / recipe.time
        count  = math.ceil(per_sec / rate_pm)
        actual = count * rate_pm
        name   = ITEM_DISPLAY_NAME.get(item, item)
        mname  = MACHINE_NAME.get(recipe.category, recipe.category)
        t.insert("end", f"{prefix}{name}  ×{count} {mname}  ({actual:.3f}/s)\n", "machine")

        for dep, qty in recipe.inputs.items():
            self._append_tree_colored(dep, actual * (qty / recipe.output),
                                      level, depth + 1, t)


def main():
    app = FactorioCalc()
    app.mainloop()


if __name__ == "__main__":
    main()