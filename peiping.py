"""
异星工厂产线计算工具 v3 — Tkinter GUI
原版 1.1 全配方覆盖
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
MINING_SPEED       = 1.0   # 采矿机视为速度1

# ═══════════════════════════════════════════════════════════
#  配方数据结构
# ═══════════════════════════════════════════════════════════
@dataclass
class Recipe:
    time: float
    output: float
    inputs: dict[str, float]
    category: str   # assembling/furnace/chemical/refinery/centrifuge/rocket/mining/raw

# ═══════════════════════════════════════════════════════════
#  原版 1.1 完整配方表
# ═══════════════════════════════════════════════════════════
RECIPES: dict[str, Recipe] = {

    # ────────── 冶炼 (smelting, furnace speed=2.0) ──────────
    "iron_plate":           Recipe(3.2,  1,  {"iron_ore": 1},             "furnace"),
    "copper_plate":         Recipe(3.2,  1,  {"copper_ore": 1},           "furnace"),
    "steel_plate":          Recipe(16.0, 1,  {"iron_plate": 5},           "furnace"),
    "stone_brick":          Recipe(3.2,  1,  {"stone": 2},                "furnace"),

    # ────────── 基础零件 ──────────
    "copper_cable":         Recipe(0.5,  2,  {"copper_plate": 1},                    "assembling"),
    "iron_gear_wheel":      Recipe(0.5,  1,  {"iron_plate": 2},                      "assembling"),
    "iron_stick":           Recipe(0.5,  2,  {"iron_plate": 1},                      "assembling"),
    "pipe":                 Recipe(0.5,  1,  {"iron_plate": 1},                      "assembling"),
    "empty_barrel":         Recipe(1.0,  1,  {"steel_plate": 1},                     "assembling"),
    "stone_wall":           Recipe(0.5,  1,  {"stone_brick": 5},                     "assembling"),
    "gate":                 Recipe(0.5,  1,  {"stone_wall": 1, "steel_plate": 2, "green_circuit": 2}, "assembling"),

    # ────────── 电路板 ──────────
    "green_circuit":        Recipe(0.5,  1,  {"iron_plate": 1, "copper_cable": 3},   "assembling"),
    # advanced_circuit = red_circuit（原版内部名 advanced-circuit）
    "advanced_circuit":     Recipe(6.0,  1,  {"green_circuit": 2, "plastic_bar": 2, "copper_cable": 4}, "assembling"),
    # processing_unit = blue_circuit
    "processing_unit":      Recipe(10.0, 1,  {"green_circuit": 20, "advanced_circuit": 2, "sulfuric_acid": 5}, "chemical"),

    # ────────── 化工品 ──────────
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

    # ────────── 炼油 ──────────
    "petroleum_gas_basic":  Recipe(5.0,  45, {"crude_oil": 100},                    "refinery"),
    "advanced_oil_processing": Recipe(5.0, 1, {"crude_oil": 100, "water": 50},      "refinery"),
    "heavy_oil_cracking":   Recipe(2.0,  30, {"heavy_oil": 40, "water": 30},        "chemical"),
    "light_oil_cracking":   Recipe(2.0,  20, {"light_oil": 30, "water": 30},        "chemical"),
    "coal_liquefaction":    Recipe(5.0,  90, {"coal": 10, "heavy_oil": 25, "steam": 50}, "refinery"),
    "flamethrower_ammo":    Recipe(6.0,  1,  {"crude_oil": 100, "steel_plate": 5},  "chemical"),

    # ────────── 科研包 ──────────
    "automation_science_pack":  Recipe(5.0,  1,  {"copper_plate": 1, "iron_gear_wheel": 1},                         "assembling"),
    "logistic_science_pack":    Recipe(6.0,  1,  {"inserter": 1, "transport_belt": 1},                              "assembling"),
    "military_science_pack":    Recipe(10.0, 2,  {"stone_wall": 2, "grenade": 1, "piercing_rounds_magazine": 1},    "assembling"),
    "chemical_science_pack":    Recipe(24.0, 2,  {"advanced_circuit": 3, "engine_unit": 2, "sulfur": 1},            "assembling"),
    "production_science_pack":  Recipe(21.0, 3,  {"electric_furnace": 1, "productivity_module": 1, "rail": 30},     "assembling"),
    "utility_science_pack":     Recipe(21.0, 3,  {"flying_robot_frame": 1, "low_density_structure": 3, "processing_unit": 2}, "assembling"),
    "space_science_pack":       Recipe(40.57, 1000, {"rocket_part": 100, "satellite": 1},                           "rocket"),

    # ────────── 传送带 ──────────
    "transport_belt":           Recipe(0.5,  2,  {"iron_gear_wheel": 1, "iron_plate": 1},                    "assembling"),
    "fast_transport_belt":      Recipe(0.5,  1,  {"iron_gear_wheel": 5, "transport_belt": 1},                "assembling"),
    "express_transport_belt":   Recipe(0.5,  1,  {"iron_gear_wheel": 10, "fast_transport_belt": 1, "lubricant": 20}, "chemical"),
    "underground_belt":         Recipe(1.0,  2,  {"iron_plate": 10, "transport_belt": 5},                    "assembling"),
    "fast_underground_belt":    Recipe(2.0,  2,  {"iron_gear_wheel": 40, "underground_belt": 2},             "assembling"),
    "express_underground_belt": Recipe(2.0,  2,  {"iron_gear_wheel": 80, "fast_underground_belt": 2, "lubricant": 40}, "chemical"),
    "splitter":                 Recipe(1.0,  1,  {"green_circuit": 5, "iron_plate": 5, "transport_belt": 4}, "assembling"),
    "fast_splitter":            Recipe(2.0,  1,  {"green_circuit": 10, "iron_gear_wheel": 10, "splitter": 1},"assembling"),
    "express_splitter":         Recipe(2.0,  1,  {"advanced_circuit": 10, "iron_gear_wheel": 10, "fast_splitter": 1, "lubricant": 80}, "chemical"),

    # ────────── 插入臂 ──────────
    "inserter":                 Recipe(0.5,  1,  {"green_circuit": 1, "iron_gear_wheel": 1, "iron_plate": 1}, "assembling"),
    "burner_inserter":          Recipe(0.5,  1,  {"iron_gear_wheel": 1, "iron_plate": 1},                    "assembling"),
    "long_handed_inserter":     Recipe(0.5,  1,  {"inserter": 1, "iron_gear_wheel": 1, "iron_plate": 1},     "assembling"),
    "fast_inserter":            Recipe(0.5,  1,  {"green_circuit": 2, "iron_plate": 2, "inserter": 1},       "assembling"),
    "filter_inserter":          Recipe(0.5,  1,  {"fast_inserter": 1, "green_circuit": 4},                   "assembling"),
    "bulk_inserter":            Recipe(0.5,  1,  {"advanced_circuit": 1, "fast_inserter": 1, "green_circuit": 15, "iron_gear_wheel": 15}, "assembling"),

    # ────────── 机器人 & 仓库 ──────────
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

    # ────────── 机械组件 ──────────
    "engine_unit":              Recipe(10.0, 1,  {"iron_gear_wheel": 1, "pipe": 2, "steel_plate": 1},        "assembling"),
    "electric_engine_unit":     Recipe(10.0, 1,  {"green_circuit": 2, "engine_unit": 1, "lubricant": 15},    "chemical"),
    "flying_robot_frame":       Recipe(20.0, 1,  {"battery": 2, "electric_engine_unit": 1, "green_circuit": 3, "steel_plate": 1}, "assembling"),

    # ────────── 建筑机器 ──────────
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

    # ────────── 矿机 ──────────
    "burner_mining_drill":      Recipe(2.0,  1,  {"iron_gear_wheel": 3, "iron_plate": 3, "stone_furnace": 1},"assembling"),
    "electric_mining_drill":    Recipe(2.0,  1,  {"green_circuit": 3, "iron_gear_wheel": 5, "iron_plate": 10}, "assembling"),

    # ────────── 电力 ──────────
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
    "display_panel":            Recipe(0.5,  1,  {"green_circuit": 1, "iron_plate": 1},                      "assembling"),

    # ────────── 管道 & 储罐 ──────────
    "pipe_to_ground":           Recipe(0.5,  2,  {"iron_plate": 5, "pipe": 10},                              "assembling"),
    "storage_tank":             Recipe(3.0,  1,  {"iron_plate": 20, "steel_plate": 5},                       "assembling"),

    # ────────── 铁路 ──────────
    "rail":                     Recipe(0.5,  2,  {"iron_stick": 1, "steel_plate": 1, "stone": 1},            "assembling"),
    "locomotive":               Recipe(4.0,  1,  {"electric_motor": 20, "steel_plate": 30, "green_circuit": 10}, "assembling"),
    "cargo_wagon":              Recipe(1.0,  1,  {"iron_gear_wheel": 10, "iron_plate": 20, "steel_plate": 20}, "assembling"),
    "fluid_wagon":              Recipe(1.5,  1,  {"iron_gear_wheel": 10, "pipe": 8, "steel_plate": 16, "storage_tank": 1}, "assembling"),
    "artillery_wagon":          Recipe(4.0,  1,  {"advanced_circuit": 20, "engine_unit": 64, "iron_gear_wheel": 10, "pipe": 16, "steel_plate": 40}, "assembling"),
    "train_stop":               Recipe(0.5,  1,  {"green_circuit": 5, "iron_plate": 6, "iron_stick": 6, "steel_plate": 3}, "assembling"),
    "rail_signal":              Recipe(0.5,  1,  {"green_circuit": 1, "iron_plate": 5},                      "assembling"),
    "rail_chain_signal":        Recipe(0.5,  1,  {"green_circuit": 1, "iron_plate": 5},                      "assembling"),

    # ────────── 模块 ──────────
    "speed_module":             Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "speed_module_2":           Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "speed_module": 4}, "assembling"),
    "speed_module_3":           Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "speed_module_2": 4}, "assembling"),
    "productivity_module":      Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "productivity_module_2":    Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "productivity_module": 4}, "assembling"),
    "productivity_module_3":    Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "productivity_module_2": 4}, "assembling"),
    "efficiency_module":        Recipe(15.0, 1,  {"advanced_circuit": 5, "green_circuit": 5},                "assembling"),
    "efficiency_module_2":      Recipe(30.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "efficiency_module": 4}, "assembling"),
    "efficiency_module_3":      Recipe(60.0, 1,  {"advanced_circuit": 5, "processing_unit": 5, "efficiency_module_2": 4}, "assembling"),

    # ────────── 武器 & 弹药 ──────────
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

    # ────────── 炮塔 & 防御 ──────────
    "gun_turret":               Recipe(8.0,  1,  {"copper_plate": 10, "iron_gear_wheel": 10, "iron_plate": 20}, "assembling"),
    "laser_turret":             Recipe(20.0, 1,  {"battery": 12, "green_circuit": 20, "steel_plate": 20},    "assembling"),
    "flamethrower_turret":      Recipe(20.0, 1,  {"engine_unit": 5, "iron_gear_wheel": 15, "pipe": 10, "steel_plate": 30}, "assembling"),
    "artillery_turret":         Recipe(40.0, 1,  {"advanced_circuit": 20, "concrete": 60, "iron_gear_wheel": 40, "steel_plate": 60}, "assembling"),
    "radar":                    Recipe(0.5,  1,  {"green_circuit": 5, "iron_gear_wheel": 5, "iron_plate": 10}, "assembling"),

    # ────────── 装备（个人防护） ──────────
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

    # ────────── 核能 ──────────
    "uranium_fuel_cell":        Recipe(10.0, 10, {"iron_plate": 10, "uranium_235": 1, "uranium_238": 19},    "assembling"),
    "uranium_processing":       Recipe(12.0, 1,  {"uranium_ore": 10},                                        "centrifuge"),   # 实际产出 U235+U238，简化为原料
    "kovarex_enrichment":       Recipe(60.0, 41, {"uranium_235": 40, "uranium_238": 5},                      "centrifuge"),

    # ────────── 混凝土 & 建材 ──────────
    "concrete":                 Recipe(10.0, 10, {"iron_ore": 1, "stone_brick": 5, "water": 100},            "chemical"),
    "hazard_concrete":          Recipe(0.25, 10, {"concrete": 10},                                           "assembling"),
    "refined_concrete":         Recipe(15.0, 10, {"concrete": 20, "iron_stick": 8, "steel_plate": 1, "water": 100}, "chemical"),
    "refined_hazard_concrete":  Recipe(0.25, 10, {"refined_concrete": 10},                                   "assembling"),
    "landfill":                 Recipe(0.5,  1,  {"stone": 50},                                              "assembling"),

    # ────────── 火箭 ──────────
    "rocket_silo":              Recipe(30.0, 1,  {"concrete": 1000, "electric_engine_unit": 200, "pipe": 100, "processing_unit": 200, "steel_plate": 1000}, "assembling"),
    "low_density_structure":    Recipe(15.0, 1,  {"copper_plate": 20, "plastic_bar": 5, "steel_plate": 2},  "assembling"),
    "rocket_part":              Recipe(3.0,  1,  {"low_density_structure": 10, "processing_unit": 10, "rocket_fuel": 10}, "rocket"),
    "satellite":                Recipe(5.0,  1,  {"accumulator": 100, "low_density_structure": 100, "processing_unit": 100, "radar": 5, "rocket_fuel": 50, "solar_panel": 100}, "assembling"),

    # ────────── 电路网络 ──────────
    "arithmetic_combinator":    Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 5},                   "assembling"),
    "decider_combinator":       Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 5},                   "assembling"),
    "selector_combinator":      Recipe(0.5,  1,  {"advanced_circuit": 2, "decider_combinator": 5},          "assembling"),
    "constant_combinator":      Recipe(0.5,  1,  {"copper_cable": 5, "green_circuit": 2},                   "assembling"),
    "programmable_speaker":     Recipe(2.0,  1,  {"copper_cable": 5, "green_circuit": 4, "iron_plate": 3, "iron_stick": 4}, "assembling"),

    # ────────── 载具 ──────────
    "car":                      Recipe(2.0,  1,  {"engine_unit": 8, "iron_plate": 20, "steel_plate": 5},    "assembling"),
    "tank":                     Recipe(5.0,  1,  {"advanced_circuit": 10, "engine_unit": 32, "iron_gear_wheel": 15, "steel_plate": 50}, "assembling"),
    "spidertron":               Recipe(10.0, 1,  {"efficiency_module_3": 2, "exoskeleton": 4, "low_density_structure": 150, "portable_fission_reactor": 2, "processing_unit": 16, "radar": 2, "raw_fish": 1, "rocket_launcher": 4}, "assembling"),
    "cargo_landing_pad":        Recipe(30.0, 1,  {"concrete": 200, "processing_unit": 10, "steel_plate": 25}, "assembling"),

    # ────────── 其他 ──────────
    "repair_pack":              Recipe(0.5,  1,  {"green_circuit": 2, "iron_gear_wheel": 2},                 "assembling"),
    "wooden_chest":             Recipe(0.5,  1,  {"wood": 2},                                                "assembling"),
    "wall":                     Recipe(0.5,  1,  {"stone_brick": 5},                                         "assembling"),
}

# locomotive 用 engine_unit 而非 electric_motor（2.0新增），修正
RECIPES["locomotive"] = Recipe(4.0, 1, {"engine_unit": 20, "green_circuit": 10, "steel_plate": 30}, "assembling")


# 删除重复键（advanced_circuit = red_circuit，processing_unit = blue_circuit 用于友好显示名）
# 实际保持两套 key 共存，指向相同配方数据即可

# ═══════════════════════════════════════════════════════════
#  原料（终端节点）
# ═══════════════════════════════════════════════════════════
RAW_ITEMS = frozenset({
    "iron_ore", "copper_ore", "coal", "stone", "wood",
    "crude_oil", "water", "petroleum_gas", "heavy_oil", "light_oil",
    "steam", "uranium_ore", "uranium_235", "uranium_238",
    "raw_fish", "solid_fuel",
})

# ═══════════════════════════════════════════════════════════
#  显示名称
# ═══════════════════════════════════════════════════════════
ITEM_DISPLAY_NAME: dict[str, str] = {
    # 原料
    "iron_ore": "铁矿石", "copper_ore": "铜矿石", "coal": "煤",
    "stone": "石头", "wood": "木材", "crude_oil": "原油",
    "water": "水", "petroleum_gas": "石油气", "heavy_oil": "重油",
    "light_oil": "轻油", "steam": "蒸汽", "uranium_ore": "铀矿石",
    "uranium_235": "铀-235", "uranium_238": "铀-238",
    "raw_fish": "鱼", "solid_fuel": "固体燃料（外购）",

    # 冶炼
    "iron_plate": "铁板", "copper_plate": "铜板",
    "steel_plate": "钢板", "stone_brick": "石砖",

    # 中间件
    "copper_cable": "铜线", "iron_gear_wheel": "铁齿轮",
    "iron_stick": "铁棍", "pipe": "管道", "empty_barrel": "空桶",
    "stone_wall": "石墙", "gate": "大门",

    # 电路
    "green_circuit": "绿电路（电子电路）",
    "red_circuit": "红电路（高级电路）",
    "blue_circuit": "蓝电路（处理器）",
    "advanced_circuit": "高级电路",
    "processing_unit": "处理器",

    # 化工
    "plastic_bar": "塑料条", "sulfur": "硫磺",
    "sulfuric_acid": "硫酸", "battery": "电池",
    "explosives": "炸药",
    "solid_fuel_from_light_oil": "固体燃料(轻油)",
    "solid_fuel_from_petroleum": "固体燃料(石油气)",
    "solid_fuel_from_heavy_oil": "固体燃料(重油)",
    "lubricant": "润滑剂", "rocket_fuel": "火箭燃料",
    "nuclear_fuel": "核燃料",

    # 炼油
    "basic_oil_processing": "基础炼油",
    "advanced_oil_processing": "高级炼油",
    "coal_liquefaction": "煤液化",
    "heavy_to_light": "重油裂解",
    "light_to_gas": "轻油裂解",

    # 科研
    "automation_science_pack": "自动化科研包（红瓶）",
    "logistic_science_pack": "物流科研包（绿瓶）",
    "military_science_pack": "军事科研包（灰瓶）",
    "chemical_science_pack": "化学科研包（蓝瓶）",
    "production_science_pack": "生产科研包（紫瓶）",
    "utility_science_pack": "实用科研包（黄瓶）",
    "space_science_pack": "太空科研包（白瓶）",
    "science_pack_1": "自动化科研包",

    # 物流
    "transport_belt": "传送带", "fast_transport_belt": "快速传送带",
    "express_transport_belt": "极速传送带",
    "underground_belt": "地下传送带", "fast_underground_belt": "快速地下传送带",
    "express_underground_belt": "极速地下传送带",
    "splitter": "分配器", "fast_splitter": "快速分配器",
    "express_splitter": "极速分配器",

    # 机器人
    "logistic_robot": "物流机器人", "construction_robot": "建造机器人",
    "roboport": "机器人港口",
    "active_provider_chest": "主动提供箱", "passive_provider_chest": "被动提供箱",
    "requester_chest": "请求箱", "storage_chest": "存储箱",
    "buffer_chest": "缓冲箱", "steel_chest": "钢箱", "iron_chest": "铁箱",

    # 机械
    "engine_unit": "发动机组件", "electric_engine_unit": "电动发动机",
    "flying_robot_frame": "飞行机器人机架",
    "assembling_machine_1": "组装机1", "assembling_machine_2": "组装机2",
    "assembling_machine_3": "组装机3",
    "electric_furnace": "电炉", "steel_furnace": "钢炉",
    "stone_furnace": "石炉", "chemical_plant": "化工厂",
    "oil_refinery": "炼油厂", "pump": "泵", "offshore_pump": "近海泵",

    # 电力
    "electric_mining_drill": "电动矿机", "burner_mining_drill": "燃料矿机",
    "boiler": "锅炉", "steam_engine": "蒸汽机", "steam_turbine": "蒸汽轮机",
    "solar_panel": "太阳能板", "accumulator": "蓄电器",
    "nuclear_reactor": "核反应堆", "heat_exchanger": "热交换器",
    "heat_pipe": "热管", "centrifuge": "离心机",
    "electric_pole": "小型电杆", "medium_electric_pole": "中型电杆",
    "big_electric_pole": "大型电杆", "substation": "变电站",
    "power_switch": "电源开关",

    # 管道
    "pipe_to_ground": "地下管道", "storage_tank": "储液罐",
    "fluid_wagon": "液体车厢",

    # 铁路
    "rail": "铁轨", "locomotive": "机车", "cargo_wagon": "货运车厢",
    "train_stop": "车站", "rail_signal": "轨道信号", "rail_chain_signal": "轨道链信号",

    # 插入臂
    "inserter": "插入臂", "long_handed_inserter": "长臂插入臂",
    "fast_inserter": "快速插入臂", "filter_inserter": "过滤插入臂",
    "stack_inserter": "堆叠插入臂", "stack_filter_inserter": "堆叠过滤插入臂",

    # 模块
    "speed_module": "速度模块1", "speed_module_2": "速度模块2",
    "speed_module_3": "速度模块3",
    "productivity_module": "产能模块1", "productivity_module_2": "产能模块2",
    "productivity_module_3": "产能模块3",
    "effectivity_module": "效率模块1", "effectivity_module_2": "效率模块2",
    "effectivity_module_3": "效率模块3",
    "efficiency_module_3": "效率模块3",

    # 武器
    "firearm_magazine": "弹匣", "piercing_rounds_magazine": "穿甲弹匣",
    "uranium_rounds_magazine": "铀弹匣",
    "shotgun_shell": "霰弹", "piercing_shotgun_shell": "穿甲霰弹",
    "cannon_shell": "炮弹", "explosive_cannon_shell": "爆炸炮弹",
    "uranium_cannon_shell": "铀炮弹",
    "explosive_uranium_cannon_shell": "爆炸铀炮弹",
    "artillery_shell": "榴弹炮炮弹",
    "rocket": "火箭弹", "explosive_rocket": "爆炸火箭弹",
    "atomic_bomb": "原子弹",
    "grenade": "手雷", "cluster_grenade": "集束手雷",
    "poison_capsule": "毒气胶囊", "slowdown_capsule": "减速胶囊",
    "defender_capsule": "防卫胶囊", "distractor_capsule": "干扰胶囊",
    "destroyer_capsule": "毁灭胶囊",

    # 装备
    "light_armor": "轻甲", "heavy_armor": "重甲",
    "modular_armor": "模块甲", "power_armor": "动力甲",
    "power_armor_mk2": "动力甲MK2",
    "personal_laser_defense_equipment": "个人激光防御",
    "energy_shield_equipment": "能量护盾", "energy_shield_mk2_equipment": "能量护盾MK2",
    "battery_equipment": "电池组件", "battery_mk2_equipment": "电池组件MK2",
    "belt_immunity_equipment": "传送带免疫",
    "exoskeleton_equipment": "外骨骼", "personal_roboport_equipment": "个人机器人港口",
    "personal_roboport_mk2_equipment": "个人机器人港口MK2",
    "night_vision_equipment": "夜视仪",

    # 炮塔
    "gun_turret": "枪炮塔", "laser_turret": "激光炮塔",
    "flamethrower_turret": "火焰炮塔", "artillery_turret": "榴弹炮塔",
    "radar": "雷达", "land_mine": "地雷",

    # 核
    "uranium_fuel_cell": "铀燃料棒",
    "used_up_uranium_fuel_cell": "用完的燃料棒",
    "uranium_processing": "铀处理",
    "kovarex_enrichment": "科瓦雷克浓缩",

    # 建材
    "concrete": "混凝土", "hazard_concrete": "警示混凝土",
    "refined_concrete": "精炼混凝土", "refined_hazard_concrete": "精炼警示混凝土",

    # 火箭
    "rocket_silo": "火箭发射井",
    "low_density_structure": "低密度结构",
    "rocket_control_unit": "火箭控制单元",
    "rocket_part": "火箭零件", "satellite": "卫星",

    # 电路网络
    "arithmetic_combinator": "算术组合器", "decider_combinator": "判定组合器",
    "constant_combinator": "常量组合器", "programmable_speaker": "可编程扬声器",

    # 载具
    "car": "汽车", "tank": "坦克", "spidertron": "蜘蛛机器人",

    # 武器装备
    "rocket_launcher": "火箭筒", "shotgun": "霰弹枪",
    "combat_shotgun": "战斗霰弹枪", "sniper_rifle": "狙击步枪",
    "submachine_gun": "冲锋枪", "pistol": "手枪",
    "flamethrower": "火焰喷射器",

    # 木制
    "wooden_chest": "木箱",

    # 特殊
    "fused_gear_wheel": "熔合齿轮", "efficiency_module_3": "效率模块3",
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
    "assembling": -1,   # 由等级决定
    "furnace":    FURNACE_SPEED,
    "chemical":   CHEM_PLANT_SPEED,
    "refinery":   OIL_REFINERY_SPEED,
    "centrifuge": CENTRIFUGE_SPEED,
    "rocket":     ROCKET_SILO_SPEED,
    "mining":     MINING_SPEED,
}

# 分类归组（用于 GUI 左侧列表）
ITEM_CATEGORIES: dict[str, list[str]] = {
    "⚗️  科研包":       ["automation_science_pack","logistic_science_pack","military_science_pack",
                        "chemical_science_pack","production_science_pack","utility_science_pack","space_science_pack"],
    "🔌  电路板":        ["green_circuit","advanced_circuit","processing_unit"],
    "🏭  冶炼品":        ["iron_plate","copper_plate","steel_plate","stone_brick"],
    "🔧  基础零件":      ["copper_cable","iron_gear_wheel","iron_stick","pipe","empty_barrel","stone_wall","gate"],
    "🧪  化工品":        ["plastic_bar","sulfur","sulfuric_acid","battery","explosives",
                        "lubricant","rocket_fuel","nuclear_fuel","solid_fuel_from_light_oil",
                        "solid_fuel_from_petroleum","solid_fuel_from_heavy_oil"],
    "🛢️  炼油":          ["basic_oil_processing","advanced_oil_processing","heavy_to_light","light_to_gas"],
    "🚛  传送带 & 物流":  ["transport_belt","fast_transport_belt","express_transport_belt",
                        "underground_belt","fast_underground_belt","express_underground_belt",
                        "splitter","fast_splitter","express_splitter"],
    "🤖  机器人":        ["logistic_robot","construction_robot","roboport",
                        "active_provider_chest","passive_provider_chest","requester_chest",
                        "storage_chest","buffer_chest","steel_chest","iron_chest"],
    "🔌  电力设备":      ["electric_pole","medium_electric_pole","big_electric_pole","substation",
                        "power_switch","boiler","steam_engine","steam_turbine","solar_panel",
                        "accumulator","nuclear_reactor","heat_exchanger","heat_pipe","centrifuge"],
    "⚙️  机械 & 建筑":   ["engine_unit","electric_engine_unit","flying_robot_frame",
                        "assembling_machine_1","assembling_machine_2","assembling_machine_3",
                        "electric_furnace","steel_furnace","stone_furnace","chemical_plant",
                        "oil_refinery","pump","offshore_pump","electric_mining_drill","burner_mining_drill"],
    "🚂  铁路":          ["rail","locomotive","cargo_wagon","fluid_wagon",
                        "train_stop","rail_signal","rail_chain_signal"],
    "🦾  插入臂":        ["inserter","long_handed_inserter","fast_inserter","filter_inserter",
                        "stack_inserter","stack_filter_inserter"],
    "📦  管道 & 储罐":   ["pipe_to_ground","storage_tank"],
    "💣  武器 & 弹药":   ["firearm_magazine","piercing_rounds_magazine","uranium_rounds_magazine",
                        "shotgun_shell","piercing_shotgun_shell","cannon_shell",
                        "explosive_cannon_shell","grenade","cluster_grenade",
                        "rocket","explosive_rocket","atomic_bomb","land_mine",
                        "poison_capsule","slowdown_capsule",
                        "defender_capsule","distractor_capsule","destroyer_capsule",
                        "rocket_launcher","shotgun","pistol","flamethrower"],
    "🛡️  装备":          ["light_armor","heavy_armor","modular_armor","power_armor","power_armor_mk2",
                        "energy_shield_equipment","energy_shield_mk2_equipment",
                        "battery_equipment","battery_mk2_equipment",
                        "belt_immunity_equipment","exoskeleton_equipment",
                        "personal_roboport_equipment","personal_roboport_mk2_equipment",
                        "night_vision_equipment","personal_laser_defense_equipment"],
    "🏰  防御设施":      ["gun_turret","laser_turret","flamethrower_turret","artillery_turret","radar"],
    "☢️  核能":          ["uranium_fuel_cell","uranium_processing","kovarex_enrichment"],
    "🏗️  建材":          ["concrete","hazard_concrete","refined_concrete","refined_hazard_concrete"],
    "🚀  火箭":          ["rocket_silo","low_density_structure","rocket_control_unit","rocket_part","satellite"],
    "📡  电路网络":      ["arithmetic_combinator","decider_combinator","constant_combinator","programmable_speaker"],
    "📦  模块":          ["speed_module","speed_module_2","speed_module_3",
                        "productivity_module","productivity_module_2","productivity_module_3",
                        "effectivity_module","effectivity_module_2","effectivity_module_3"],
    "🚗  载具":          ["car","tank"],
    "🌲  木材制品":      ["wooden_chest"],
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
#  Tkinter GUI
# ═══════════════════════════════════════════════════════════
BG       = "#1a1c23"
BG2      = "#23262f"
BG3      = "#2d3142"
ACCENT   = "#f4a535"
ACCENT2  = "#e07b10"
FG       = "#e8eaf0"
FG_DIM   = "#8a8fa8"
GREEN    = "#4caf82"
BLUE     = "#5b9bd5"
RED      = "#e05c5c"
CYAN     = "#5bc8c8"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_HEAD   = ("Segoe UI", 10, "bold")
FONT_BODY   = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_SEARCH = ("Segoe UI", 10)



class FactorioCalc(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("异星工厂 产线计算器  v3  (Vanilla 1.1)")
        self.geometry("1260x800")
        self.minsize(1000, 640)
        self.configure(bg=BG)
        self._selected_item: Optional[str] = None
        # 多目标列表: list of {"item": str, "rate": float, "unit": str}
        self._targets: list[dict] = []
        self._build_ui()
        self._populate_list()

    # ─────────────── UI 构建 ───────────────
    def _build_ui(self):
        self._style()

        # ── 顶栏标题
        top = tk.Frame(self, bg=BG, pady=6)
        top.pack(fill="x", padx=12)
        tk.Label(top, text="⚙  异星工厂  产线计算器", font=("Segoe UI", 15, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(top, text="Factorio Vanilla 1.1 · 全配方 · 多目标合并计算",
                 font=FONT_BODY, bg=BG, fg=FG_DIM).pack(side="left", padx=12)

        # ── 主区域水平分割
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
                    arrowcolor=ACCENT, bordercolor=BG3,
                    relief="flat")
        s.configure("Accent.TButton",
                    background=ACCENT, foreground="#1a1c23",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat", padding=(8, 4))
        s.map("Accent.TButton", background=[("active", ACCENT2)])
        s.configure("Del.TButton",
                    background="#5c2020", foreground=FG,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat", padding=(4, 2))
        s.map("Del.TButton", background=[("active", RED)])
        s.configure("Add.TButton",
                    background="#1e4d2b", foreground=FG,
                    font=("Segoe UI", 9),
                    relief="flat", padding=(6, 2))
        s.map("Add.TButton", background=[("active", GREEN)])

    def _build_left(self, parent):
        lf = tk.Frame(parent, bg=BG2, width=290,
                      highlightbackground=BG3, highlightthickness=1)
        lf.pack(side="left", fill="y", padx=(0, 8), pady=4)
        lf.pack_propagate(False)

        # 搜索框
        tk.Label(lf, text="搜索物品", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", padx=10, pady=(10, 2))
        sf = tk.Frame(lf, bg=BG3)
        sf.pack(fill="x", padx=8, pady=(0, 6))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        tk.Entry(sf, textvariable=self._search_var,
                 bg=BG3, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_SEARCH,
                 bd=4).pack(fill="x")

        # 物品列表
        frame = tk.Frame(lf, bg=BG2)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        scroll = tk.Scrollbar(frame, bg=BG3, troughcolor=BG2,
                              relief="flat", width=6)
        self._listbox = tk.Listbox(
            frame, bg=BG2, fg=FG, selectbackground=ACCENT,
            selectforeground="#1a1c23", activestyle="none",
            relief="flat", borderwidth=0,
            font=FONT_BODY, highlightthickness=0,
            yscrollcommand=scroll.set,
        )
        scroll.config(command=self._listbox.yview)
        self._listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

    def _build_right(self, parent):
        rf = tk.Frame(parent, bg=BG)
        rf.pack(side="left", fill="both", expand=True, pady=4)

        # ── 上半：目标列表区 ──────────────────────────────
        top_frame = tk.Frame(rf, bg=BG2,
                             highlightbackground=BG3, highlightthickness=1)
        top_frame.pack(fill="x", pady=(0, 8))

        # 标题栏
        hdr = tk.Frame(top_frame, bg=BG2)
        hdr.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(hdr, text="生产目标列表", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text="（从左侧选中物品后点 ＋ 添加；双击行可删除）",
                 font=FONT_BODY, bg=BG2, fg=FG_DIM).pack(side="left", padx=10)

        # 组装机等级（全局）
        lvl_f = tk.Frame(hdr, bg=BG2)
        lvl_f.pack(side="right")
        tk.Label(lvl_f, text="组装机", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(side="left")
        self._level_var = tk.StringVar(value="2")
        for val, label in [("1","Lv.1"),("2","Lv.2"),("3","Lv.3")]:
            tk.Radiobutton(
                lvl_f, text=label, variable=self._level_var, value=val,
                bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                activeforeground=ACCENT, font=FONT_BODY,
            ).pack(side="left", padx=3)

        # ── 目标表格
        tbl_outer = tk.Frame(top_frame, bg=BG2)
        tbl_outer.pack(fill="x", padx=10, pady=(0, 6))

        # 列标题
        cols_hdr = tk.Frame(tbl_outer, bg=BG3)
        cols_hdr.pack(fill="x")
        for txt, w in [("物品名称", 26), ("产量", 8), ("单位", 8), ("", 6)]:
            tk.Label(cols_hdr, text=txt, font=FONT_HEAD, bg=BG3, fg=FG_DIM,
                     width=w, anchor="w").pack(side="left", padx=4, pady=2)

        # 目标行容器（可滚动）
        self._tgt_canvas = tk.Canvas(tbl_outer, bg=BG2, height=130,
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

        # ── 添加行 & 计算按钮
        btn_row = tk.Frame(top_frame, bg=BG2)
        btn_row.pack(fill="x", padx=10, pady=(2, 8))

        # 选中物品提示
        self._selected_label = tk.Label(
            btn_row, text="← 请从左侧选择物品",
            font=FONT_BODY, bg=BG2, fg=FG_DIM, anchor="w", width=30)
        self._selected_label.pack(side="left")

        # 产量输入
        tk.Label(btn_row, text="产量", font=FONT_HEAD,
                 bg=BG2, fg=FG_DIM).pack(side="left", padx=(10, 4))
        self._rate_var = tk.StringVar(value="1")
        tk.Entry(btn_row, textvariable=self._rate_var,
                 width=7, bg=BG3, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_SEARCH, bd=4
                 ).pack(side="left")
        self._unit_var = tk.StringVar(value="个/分")
        om = tk.OptionMenu(btn_row, self._unit_var, "个/秒", "个/分")
        om.config(bg=BG3, fg=FG, activebackground=BG3, activeforeground=FG,
                  highlightthickness=0, relief="flat", font=FONT_BODY, width=5)
        om.pack(side="left", padx=(2, 12))

        ttk.Button(btn_row, text="＋  添加到列表",
                   style="Add.TButton",
                   command=self._add_target).pack(side="left", padx=(0, 8))

        ttk.Button(btn_row, text="清空列表",
                   style="Del.TButton",
                   command=self._clear_targets).pack(side="left", padx=(0, 20))

        ttk.Button(btn_row, text="  合并计算  ▶",
                   style="Accent.TButton",
                   command=self._calculate).pack(side="left")

        # ── 下半：结果 Notebook
        result_frame = tk.Frame(rf, bg=BG)
        result_frame.pack(fill="both", expand=True)

        nb = ttk.Notebook(result_frame)
        nb.pack(fill="both", expand=True)

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
        self._tgt_canvas.configure(
            scrollregion=self._tgt_canvas.bbox("all"))

    # ─────────────── 目标管理 ───────────────
    def _add_target(self):
        if not self._selected_item:
            messagebox.showwarning("提示", "请先从左侧选择一个物品")
            return
        try:
            rate = float(self._rate_var.get())
            if rate <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "请输入大于 0 的产量")
            return

        self._targets.append({
            "item": self._selected_item,
            "rate": rate,
            "unit": self._unit_var.get(),
        })
        self._refresh_target_rows()

    def _remove_target(self, idx: int):
        if 0 <= idx < len(self._targets):
            del self._targets[idx]
            self._refresh_target_rows()

    def _clear_targets(self):
        self._targets.clear()
        self._refresh_target_rows()

    def _refresh_target_rows(self):
        # 清除旧行
        for w in self._tgt_inner.winfo_children():
            w.destroy()

        if not self._targets:
            tk.Label(self._tgt_inner, text="（列表为空，请添加目标）",
                     bg=BG2, fg=FG_DIM, font=FONT_BODY).pack(padx=8, pady=6)
            self._on_tgt_configure()
            return

        for i, tgt in enumerate(self._targets):
            row_bg = BG2 if i % 2 == 0 else "#262932"
            row = tk.Frame(self._tgt_inner, bg=row_bg)
            row.pack(fill="x")

            name = ITEM_DISPLAY_NAME.get(tgt["item"], tgt["item"])
            cat  = RECIPES[tgt["item"]].category if tgt["item"] in RECIPES else ""
            mname = MACHINE_NAME.get(cat, "")

            tk.Label(row, text=f"{name}  [{mname}]",
                     bg=row_bg, fg=FG, font=FONT_BODY,
                     width=26, anchor="w").pack(side="left", padx=6, pady=3)
            tk.Label(row, text=f"{tgt['rate']:.3g}",
                     bg=row_bg, fg=ACCENT, font=FONT_BODY,
                     width=8, anchor="e").pack(side="left", padx=2)
            tk.Label(row, text=tgt["unit"],
                     bg=row_bg, fg=FG_DIM, font=FONT_BODY,
                     width=8, anchor="w").pack(side="left", padx=2)

            idx = i  # capture
            del_btn = tk.Button(
                row, text="✕", font=("Segoe UI", 8, "bold"),
                bg="#4a1a1a", fg=FG, activebackground=RED,
                activeforeground=FG, relief="flat", bd=0,
                cursor="hand2",
                command=lambda x=idx: self._remove_target(x))
            del_btn.pack(side="left", padx=6)

        self._on_tgt_configure()

    # ─────────────── 结果标签页 ───────────────
    def _build_machine_tab(self):
        cols = ("物品", "机器类型", "台数", "实际产出/s", "实际产出/min")
        self._machine_tree = self._make_tree(self._machine_frame, cols)

    def _build_raw_tab(self):
        cols = ("原料", "需求量/s", "需求量/min")
        self._raw_tree = self._make_tree(self._raw_frame, cols)

    def _build_tree_tab(self):
        self._tree_text = tk.Text(
            self._tree_frame, bg=BG2, fg=FG,
            font=FONT_MONO, relief="flat",
            selectbackground=BG3, wrap="none",
            state="disabled",
        )
        sb_y = tk.Scrollbar(self._tree_frame, orient="vertical",
                            command=self._tree_text.yview,
                            bg=BG3, troughcolor=BG2, relief="flat", width=6)
        sb_x = tk.Scrollbar(self._tree_frame, orient="horizontal",
                            command=self._tree_text.xview,
                            bg=BG3, troughcolor=BG2, relief="flat")
        self._tree_text.config(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self._tree_text.pack(fill="both", expand=True)

    def _make_tree(self, parent, cols):
        s = ttk.Style()
        s.configure("Dark.Treeview",
                    background=BG2, foreground=FG,
                    fieldbackground=BG2,
                    rowheight=22, font=FONT_BODY,
                    borderwidth=0)
        s.configure("Dark.Treeview.Heading",
                    background=BG3, foreground=ACCENT,
                    font=FONT_HEAD, relief="flat")
        s.map("Dark.Treeview", background=[("selected", BG3)],
              foreground=[("selected", ACCENT)])

        frame = tk.Frame(parent, bg=BG2)
        frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(frame, bg=BG3, troughcolor=BG2,
                         relief="flat", width=6)
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview",
                            yscrollcommand=sb.set)
        sb.config(command=tree.yview)

        for col in cols:
            tree.heading(col, text=col)
            if "产出" in col or "需求" in col or "台数" in col:
                tree.column(col, width=110, anchor="e")
            else:
                tree.column(col, width=200, anchor="w")

        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tree.tag_configure("odd",  background=BG2)
        tree.tag_configure("even", background="#262932")

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
        self._selected_label.config(
            text=f"✅  {name}  [{mname}]",
            fg=ACCENT,
        )

    # ─────────────── 合并计算 ───────────────
    def _calculate(self):
        if not self._targets:
            messagebox.showwarning("提示", "请先添加至少一个生产目标")
            return

        level = int(self._level_var.get())
        # 合并所有目标到同一个 plan
        merged = ProductionPlan()
        for tgt in self._targets:
            per_sec = tgt["rate"] if tgt["unit"] == "个/秒" else tgt["rate"] / 60.0
            compute_plan(tgt["item"], per_sec, level, merged)

        self._show_machine_results(merged)
        self._show_raw_results(merged)
        self._show_tree_multi(level)

    def _show_machine_results(self, plan: ProductionPlan):
        tree = self._machine_tree
        tree.delete(*tree.get_children())

        by_cat: dict[str, list[tuple[str, int, float]]] = defaultdict(list)
        for item, count in plan.machines.items():
            cat = RECIPES[item].category if item in RECIPES else "?"
            by_cat[cat].append((item, count, plan.actual_rates.get(item, 0)))

        row_idx = 0
        for cat in ("assembling", "furnace", "chemical", "refinery", "centrifuge", "rocket"):
            entries = by_cat.get(cat, [])
            if not entries:
                continue
            mname = MACHINE_NAME.get(cat, cat)
            for item, count, rate in sorted(entries, key=lambda x: -x[2]):
                name = ITEM_DISPLAY_NAME.get(item, item)
                tag  = "odd" if row_idx % 2 == 0 else "even"
                tree.insert("", "end", tags=(tag,), values=(
                    name, mname, f"{count}  台",
                    f"{rate:.3f}", f"{rate*60:.1f}",
                ))
                row_idx += 1

    def _show_raw_results(self, plan: ProductionPlan):
        tree = self._raw_tree
        tree.delete(*tree.get_children())
        for i, (item, rate) in enumerate(
            sorted(plan.raw_demand.items(), key=lambda x: -x[1])
        ):
            name = ITEM_DISPLAY_NAME.get(item, item)
            tag  = "odd" if i % 2 == 0 else "even"
            tree.insert("", "end", tags=(tag,), values=(
                name,
                f"{rate:.3f}",
                f"{rate*60:.1f}",
            ))

    def _show_tree_multi(self, level: int):
        lines: list[str] = []
        lines.append("═" * 64)
        lines.append("  合并产线  —  配方展开（各目标独立展开后汇总）")
        lines.append("═" * 64)

        for tgt in self._targets:
            per_sec = tgt["rate"] if tgt["unit"] == "个/秒" else tgt["rate"] / 60.0
            name = ITEM_DISPLAY_NAME.get(tgt["item"], tgt["item"])
            lines.append(f"\n▶  {name}   {tgt['rate']:.3g} {tgt['unit']}")
            lines.append("─" * 48)
            self._append_tree(tgt["item"], per_sec, level, 0, lines)

        self._set_tree_text(lines)

    def _append_tree(self, item: str, per_sec: float, level: int,
                     depth: int, lines: list[str]):
        prefix = "  " * depth + ("└─ " if depth > 0 else "")
        if item in RAW_ITEMS or item not in RECIPES:
            name = ITEM_DISPLAY_NAME.get(item, item)
            lines.append(f"{prefix}[原料] {name}  {per_sec:.3f}/s")
            return

        recipe = RECIPES[item]
        speed  = get_machine_speed(recipe.category, level)
        rate_pm = (recipe.output * speed) / recipe.time
        count  = math.ceil(per_sec / rate_pm)
        actual = count * rate_pm
        name   = ITEM_DISPLAY_NAME.get(item, item)
        mname  = MACHINE_NAME.get(recipe.category, recipe.category)
        lines.append(f"{prefix}{name}  ×{count} {mname}  ({actual:.3f}/s)")

        for dep, qty in recipe.inputs.items():
            self._append_tree(dep, actual * (qty / recipe.output),
                              level, depth + 1, lines)

    def _set_tree_text(self, lines: list[str]):
        t = self._tree_text
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", "\n".join(lines))
        t.config(state="disabled")


def main():
    app = FactorioCalc()
    app.mainloop()


if __name__ == "__main__":
    main()