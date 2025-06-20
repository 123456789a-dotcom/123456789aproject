import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import json
import random
import asyncio
import os
import time

load_dotenv()

# Bot owner ID - replace with your Discord user ID
OWNER_ID = 1228257836547702847  # Replace this with your actual Discord ID

# Global variables
big_dice_pot = 0

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='rpgs ', intents=intents, help_command=None)


@bot.event
async def on_ready():
    global player_data, guild_data
    player_data = load_player_data()
    guild_data = load_guild_data()
    print(f'{bot.user} has connected to Discord!')
    print(f'disRPG is ready to adventure!')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands normally
    await bot.process_commands(message)


# Comprehensive Shop System
SHOP_ITEMS = {
    # Page 1 - Basic Items
    "basic_items": {
        "life potion": {"price": 25, "description": "Restore your life with heal"},
        "basic armor": {"price": 200, "description": "An ugly armor made of wood [+2 def]"},
        "basic sword": {"price": 150, "description": "Better than nothing huh? [+1 at]"},
        "basic horse": {"price": 500, "description": "Just a normie horse"},
        "EPIC jump": {"price": "2 Time Dragon essences", "description": "Used to go to Area 16+ areas"}
    },

    # Life Boosts
    "boosts": {
        "life boost A": {"price": 10000, "description": "10 temporary life, one time use and not stackable"},
        "life boost B": {"price": 100000, "description": "25 temporary life, one time use and not stackable"},
        "life boost C": {"price": 1000000, "description": "50 temporary life, one time use and not stackable"}
    },

    # Lottery Tickets
    "lottery": {
        "lottery ticket": {"price": "varies", "description": "To join the lottery (max: 10)"}
    },

    # Farming
    "farming": {
        "seed": {"price": 4000, "description": "Used to farm"}
    },

    # Lootboxes
    "lootboxes": {
        "common lootbox": {"price": 800, "level_req": 2, "alias": "c lb"},
        "uncommon lootbox": {"price": 6000, "level_req": 4, "alias": "u lb"},
        "rare lootbox": {"price": 40000, "level_req": 6, "alias": "r lb"},
        "EPIC lootbox": {"price": 150000, "level_req": 8, "alias": "ep lb"},
        "EDGY lootbox": {"price": 420666, "level_req": 10, "alias": "ed lb"}
    },

    # Other items
    "other": {
        "magic bed": {"price": 250, "description": "all players get 1.2x monster drop chance for 45m"}
    }
}

# Dungeon Key Prices by dungeon number
DUNGEON_KEY_PRICES = {
    1: 5000,
    2: 25000,
    3: 60000,
    4: 150000,
    5: 350000,
    6: 600000,
    7: 1000000,
    8: 1500000,
    9: 2500000,
    10: 10000000,
    11: 25000000,
    12: 50000000,
    13: 100000000,
    14: 250000000
}

# Epic Shop Items
EPIC_SHOP_ITEMS = {
    # Upgrades
    "upgrades": {
        "ruby upgrade": {"price": 1, "description": "Upgrade your ruby income"},
        "fish upgrade": {"price": 2, "description": "Upgrade your fishing"},
        "log upgrade": {"price": 3, "description": "Upgrade your woodcutting"}
    },

    # Profile Backgrounds
    "backgrounds": {
        "forest background": {"price": 5, "description": "Forest themed profile background"},
        "ocean background": {"price": 5, "description": "Ocean themed profile background"},
        "space background": {"price": 10, "description": "Space themed profile background"}
    },

    # Consumables
    "consumables": {
        "time potion": {"price": 8, "description": "Reduces all cooldowns by 50%"},
        "XP potion": {"price": 12, "description": "Double XP for 1 hour"},
        "luck potion": {"price": 15, "description": "Double drop rates for 1 hour"}
    }
}

# Guild system
GUILD_TASKS = {
    "collect": {
        "Collect hunts": {"type": "hunt", "target": 100, "reward_xp": 50, "reward_rings": 10},
        "Collect adventures": {"type": "adventure", "target": 50, "reward_xp": 75, "reward_rings": 15},
        "Collect votes": {"type": "vote", "target": 25, "reward_xp": 40, "reward_rings": 8},
        "Collect profession XP": {"type": "profession", "target": 500, "reward_xp": 60, "reward_rings": 12}
    },
    "complete": {
        "Complete dungeons": {"type": "dungeon", "target": 10, "reward_xp": 100, "reward_rings": 20},
        "Complete quests": {"type": "quest", "target": 5, "reward_xp": 80, "reward_rings": 16}
    },
    "obtain": {
        "Drop lootboxes": {"type": "lootbox", "target": 20, "reward_xp": 60, "reward_rings": 12},
        "Drop monster items": {"type": "monster_drop", "target": 15, "reward_xp": 70, "reward_rings": 14},
        "Fish EPIC fish": {"type": "epic_fish", "target": 5, "reward_xp": 90, "reward_rings": 18},
        "Chop MEGA logs": {"type": "mega_log", "target": 10, "reward_xp": 85, "reward_rings": 17},
        "Pick up bananas": {"type": "banana", "target": 30, "reward_xp": 45, "reward_rings": 9},
        "Gain levels": {"type": "level", "target": 25, "reward_xp": 100, "reward_rings": 20}
    },
    "misc": {
        "Craft equipment": {"type": "craft", "target": 15, "reward_xp": 55, "reward_rings": 11},
        "Open lootboxes": {"type": "open", "target": 25, "reward_xp": 50, "reward_rings": 10},
        "Win duels": {"type": "duel_win", "target": 10, "reward_xp": 75, "reward_rings": 15},
        "Trigger events": {"type": "event", "target": 5, "reward_xp": 120, "reward_rings": 25}
    }
}

GUILD_SHOP_ITEMS = {
    "EPIC lootbox": {"cost": 4, "description": "Gives the buyer an EPIC lootbox"},
    "EDGY lootbox": {"cost": 20, "description": "Gives the buyer an EDGY lootbox"},
    "Cookie rain": {"cost": 25, "description": "Around 190 cookies will fall for everyone"},
    "Special seed": {"cost": 35, "description": "Gives 1 random special seed from farm"},
    "Achievement": {"cost": 100, "description": "There is an achievement for buying this"},
    "OMEGA horse token": {"cost": 150, "description": "Resets horse breeding/race cooldown"},
    "Magic chair": {"cost": 200, "description": "All players get 1.2x lootbox drop chance for 45m"},
    "Legendary toothbrush": {"cost": 350, "description": "Starts the lootbox summoning event"}
}

# Time Travel Titles
TT_TITLES = {
    1: "Time traveler",
    2: "One time wasn't enough",
    5: "I spend too much time here",
    10: "OOF",
    25: "OOFMEGA",
    50: "GOOFDLY",
    75: "VOOFID"
}

# Game data
AREAS = {
    1: {"name": "Area 1", "monsters": ["Wolf", "Slime", "Goblin"], "level_req": 1},
    2: {"name": "Area 2", "monsters": ["Wolf", "Nymph", "Skeleton"], "level_req": 5},
    3: {"name": "Area 3", "monsters": ["Zombie", "Ghost", "Baby Demon"], "level_req": 10},
    4: {"name": "Area 4", "monsters": ["Zombie", "Witch", "Imp"], "level_req": 15},
    5: {"name": "Area 5", "monsters": ["Unicorn", "Ghoul", "Giant Scorpion"], "level_req": 20},
    6: {"name": "Area 6", "monsters": ["Unicorn", "Sorcerer", "Baby Robot"], "level_req": 25},
    7: {"name": "Area 7", "monsters": ["Mermaid", "Cecaelia", "Giant Piranha"], "level_req": 30},
    8: {"name": "Area 8", "monsters": ["Mermaid", "Nereid", "Giant Crocodile"], "level_req": 35},
    9: {"name": "Area 9", "monsters": ["Killer Robot", "Demon", "Harpy"], "level_req": 40},
    10: {"name": "Area 10", "monsters": ["Killer Robot", "Manticore", "Dullahan"], "level_req": 45},
    11: {"name": "Area 11", "monsters": ["Scaled Baby Dragon", "Baby Dragon", "Young Dragon"], "level_req": 50},
    12: {"name": "Area 12", "monsters": ["Kid Dragon", "Scaled Kid Dragon", "Not so Young Dragon"], "level_req": 55},
    13: {"name": "Area 13", "monsters": ["Teen Dragon", "Scaled Teen Dragon", "Definitely Not Young Dragon"],
         "level_req": 60},
    14: {"name": "Area 14", "monsters": ["Adult Dragon", "Scaled Adult Dragon", "Not Young at all Dragon"],
         "level_req": 65},
    15: {"name": "Area 15",
         "monsters": ["Old Dragon", "Scaled Old Dragon", "How do you dare call this Dragon \"young\""],
         "level_req": 70},
    16: {"name": "Area 16", "monsters": ["Ancient Dragon", "Elder Dragon", "Primordial Dragon"], "level_req": 75},
    17: {"name": "Area 17", "monsters": ["Cosmic Dragon", "Void Dragon", "Reality Dragon"], "level_req": 80},
    18: {"name": "Area 18", "monsters": ["Time Dragon", "Space Dragon", "Dimension Dragon"], "level_req": 85},
    19: {"name": "Area 19", "monsters": ["Omega Dragon", "Alpha Dragon", "Genesis Dragon"], "level_req": 90},
    20: {"name": "Area 20", "monsters": ["Final Dragon", "Ultimate Dragon", "Supreme Dragon"], "level_req": 95},
    21: {"name": "THE TOP", "monsters": ["Epic NPC", "God of Games", "The Creator"], "level_req": 100}
}

# Mob drop system
MOB_DROPS = {
    "Wolf": {"item": "Wolf Skin", "chance": 2, "sell_price": 500},
    "Zombie": {"item": "Zombie Eye", "chance": 2, "sell_price": 2000},
    "Unicorn": {"item": "Unicorn Horn", "chance": 2, "sell_price": 7500},
    "Mermaid": {"item": "Mermaid Hair", "chance": 2, "sell_price": 30000},
    "Killer Robot": {"item": "Chip", "chance": 2, "sell_price": 100000},
    "Scaled Dragon": {"item": "Dragon Scale", "chance": 2, "sell_price": 250000}
}

# Dark Energy drops (Areas 16-20)
DARK_ENERGY_DROP = {"item": "Dark Energy", "chance": 0.1, "sell_price": 5000000}

# Color schemes for different embed types
EMBED_COLORS = {
    "success": 0x00ff88,
    "error": 0xff4757,
    "warning": 0xffa502,
    "info": 0x3742fa,
    "combat": 0xff6b35,
    "economy": 0xffd700,
    "level_up": 0xff9ff3,
    "rare": 0x9c88ff,
    "epic": 0xff3838,
    "legendary": 0xf368e0
}

# Enhanced working drops
CHOPPING_DROPS = {
    "Wooden Log": {
        "area_1": {"chance": 70, "amount": [1, 2]},
        "area_2_plus": {"chance": 70, "amount": [1, 2]}
    },
    "Epic Log": {
        "area_1": {"chance": 30, "amount": [1, 2]},
        "area_2_plus": {"chance": 22, "amount": [1, 2]}
    },
    "Super Log": {
        "area_2_3": {"chance": 8, "amount": [1, 1]},
        "area_4_plus": {"chance": 7, "amount": [1, 1]}
    },
    "Mega Log": {
        "area_4_5": {"chance": 1, "amount": [1, 1]},
        "area_6_plus": {"chance": 0.7, "amount": [1, 1]}
    },
    "HYPER Log": {
        "area_6_8": {"chance": 0.3, "amount": [1, 1]},
        "area_9_plus": {"chance": 0.26, "amount": [1, 1]}
    },
    "ULTRA Log": {
        "area_9_plus": {"chance": 0.04, "amount": [1, 1]}
    },
    "ULTIMATE Log": {
        "area_9_plus": {"chance": 0.01, "amount": [1, 1]}
    }
}

FISHING_DROPS = {
    "area_1": {
        "Normie Fish": {"chance": 72, "amount": [1, 3]},
        "Golden Fish": {"chance": 28, "amount": [1, 2]}
    },
    "area_2_plus": {
        "Normie Fish": {"chance": 72, "amount": [1, 3]},
        "Golden Fish": {"chance": 27.7, "amount": [1, 2]},
        "EPIC Fish": {"chance": 0.3, "amount": [1, 1]},
        "SUPER Fish": {"chance": 0.01, "amount": [1, 1]}
    }
}

BOSS_DROPS = {
    "Dragon Essence": {"chance": 25, "dungeons": [1, 2, 3, 4, 5]},
    "Time Dragon Essence": {"chance": 100, "dungeons": [15]}
}

# Comprehensive crafting system
CRAFT_RECIPES = {
    # Basic Weapons
    "Wooden Sword": {
        "attack": 4, "defense": 0, "level_req": 1, "type": "weapon",
        "materials": {"Wooden Log": 15, "Epic Log": 1}
    },
    "Fish Sword": {
        "attack": 13, "defense": 0, "level_req": 2, "type": "weapon",
        "materials": {"Epic Log": 5, "Golden Fish": 20}
    },
    "Apple Sword": {
        "attack": 32, "defense": 0, "level_req": 4, "type": "weapon",
        "materials": {"Apple": 65, "Wooden Log": 40, "Super Log": 1}
    },
    "Zombie Sword": {
        "attack": 43, "defense": 0, "level_req": 6, "type": "weapon",
        "materials": {"Wooden Log": 230, "Apple": 50, "Super Log": 3, "Zombie Eye": 1}
    },
    "Ruby Sword": {
        "attack": 63, "defense": 0, "level_req": 8, "type": "weapon",
        "materials": {"Ruby": 4, "Mega Log": 1, "Potato": 36}
    },
    "Unicorn Sword": {
        "attack": 82, "defense": 0, "level_req": 11, "type": "weapon",
        "materials": {"Unicorn Horn": 6, "Normie Fish": 500, "Super Log": 8}
    },
    "Hair Sword": {
        "attack": 89, "defense": 0, "level_req": 14, "type": "weapon",
        "materials": {"Mermaid Hair": 4, "Bread": 220}
    },
    "Coin Sword": {
        "attack": 96, "defense": 0, "level_req": 17, "type": "weapon",
        "materials": {"Ruby": 4, "HYPER Log": 2}, "coin_cost": 1234567
    },
    "Electronical Sword": {
        "attack": 100, "defense": 0, "level_req": 20, "type": "weapon",
        "materials": {"Chip": 8, "Mega Log": 1, "Potato": 140}
    },
    "EDGY Sword": {
        "attack": 200, "defense": 0, "level_req": 50, "type": "weapon",
        "materials": {"Wooden Log": 1000, "ULTRA Log": 1}
    },

    # Basic Armor
    "Fish Armor": {
        "attack": 0, "defense": 9, "level_req": 1, "type": "armor",
        "materials": {"Normie Fish": 20, "Wooden Log": 10}
    },
    "Wolf Armor": {
        "attack": 0, "defense": 20, "level_req": 2, "type": "armor",
        "materials": {"Wooden Log": 120, "Epic Log": 2, "Wolf Skin": 2}
    },
    "Eye Armor": {
        "attack": 0, "defense": 26, "level_req": 4, "type": "armor",
        "materials": {"Zombie Eye": 1, "Wooden Log": 180, "Super Log": 3}
    },
    "Banana Armor": {
        "attack": 0, "defense": 36, "level_req": 6, "type": "armor",
        "materials": {"Banana": 20, "Super Log": 4}
    },
    "Epic Armor": {
        "attack": 0, "defense": 42, "level_req": 8, "type": "armor",
        "materials": {"Epic Log": 125, "EPIC Fish": 1}
    },
    "Ruby Armor": {
        "attack": 0, "defense": 54, "level_req": 11, "type": "armor",
        "materials": {"Ruby": 7, "Unicorn Horn": 4, "Potato": 120, "Mega Log": 2}
    },
    "Coin Armor": {
        "attack": 0, "defense": 68, "level_req": 14, "type": "armor",
        "materials": {"HYPER Log": 1}, "coin_cost": 654321
    },
    "Mermaid Armor": {
        "attack": 0, "defense": 83, "level_req": 17, "type": "armor",
        "materials": {"Mermaid Hair": 20, "Mega Log": 12, "Golden Fish": 200, "Normie Fish": 150}
    },
    "Electronical Armor": {
        "attack": 0, "defense": 100, "level_req": 20, "type": "armor",
        "materials": {"Chip": 12, "HYPER Log": 1, "Bread": 180}
    },
    "EDGY Armor": {
        "attack": 0, "defense": 200, "level_req": 50, "type": "armor",
        "materials": {"Wolf Skin": 50, "Zombie Eye": 50, "Unicorn Horn": 50, "Mermaid Hair": 35, "Chip": 15}
    }
}

# Forged items (Area 11+)
FORGE_RECIPES = {
    "ULTRA-EDGY Sword": {
        "attack": 300, "defense": 0, "level_req": 70, "area_req": 11, "type": "weapon",
        "materials": {"EDGY Sword": 1, "ULTRA Log": 1, "EPIC Fish": 10, "Dragon Scale": 10}
    },
    "ULTRA-EDGY Armor": {
        "attack": 0, "defense": 300, "level_req": 70, "area_req": 12, "type": "armor",
        "materials": {"EDGY Armor": 1, "ULTRA Log": 1, "Ruby": 400, "Dragon Scale": 20}
    },
    "OMEGA Sword": {
        "attack": 400, "defense": 0, "level_req": 100, "area_req": 13, "type": "weapon",
        "materials": {"ULTRA-EDGY Sword": 1, "Mega Log": 50, "Dragon Scale": 30}, "hp_req": 1001
    },
    "OMEGA Armor": {
        "attack": 0, "defense": 400, "level_req": 100, "area_req": 14, "type": "armor",
        "materials": {"ULTRA-EDGY Armor": 1, "OMEGA Lootbox": 1, "Dragon Scale": 50}
    },
    "ULTRA-OMEGA Sword": {
        "attack": 500, "defense": 0, "level_req": 200, "area_req": 15, "type": "weapon",
        "materials": {"OMEGA Sword": 1, "ULTRA Log": 50, "Dragon Scale": 80}
    },
    "ULTRA-OMEGA Armor": {
        "attack": 0, "defense": 500, "level_req": 200, "area_req": 15, "type": "armor",
        "materials": {"OMEGA Armor": 1, "Life Potion": 1, "Dragon Scale": 300}
    },
    "GODLY Sword": {
        "attack": 750, "defense": 0, "level_req": 500, "area_req": 16, "type": "weapon",
        "materials": {"ULTRA-OMEGA Sword": 1, "ULTRA-OMEGA Armor": 1, "Dragon Essence": 10, "GODLY Lootbox": 1,
                      "OMEGA Lootbox": 12}
    }
}

# Void forging (THE TOP area)
VOID_FORGE_RECIPES = {
    "VOID Sword": {
        "attack": 750, "defense": 0, "area_req": 16, "type": "weapon",
        "materials": {"Wooden Sword": 1, "ULTIMATE Log": 8, "Dark Energy": 60}
    },
    "VOID Armor": {
        "attack": 0, "defense": 750, "area_req": 16, "type": "armor",
        "materials": {"Fish Armor": 1, "SUPER Fish": 60, "Dark Energy": 90}
    },
    "ABYSS Sword": {
        "attack": 1000, "defense": 0, "area_req": 17, "type": "weapon",
        "materials": {"Electronical Sword": 1, "OMEGA Lootbox": 12, "Dark Energy": 200}
    },
    "ABYSS Armor": {
        "attack": 0, "defense": 1000, "area_req": 17, "type": "armor",
        "materials": {"Coin Armor": 1, "ULTIMATE Log": 20, "Dark Energy": 900}
    },
    "CORRUPTED Sword": {
        "attack": 2500, "defense": 0, "area_req": 18, "type": "weapon",
        "materials": {"OMEGA Sword": 1, "EDGY Lootbox": 800}
    },
    "CORRUPTED Armor": {
        "attack": 0, "defense": 2500, "area_req": 18, "type": "armor",
        "materials": {"SUPER Armor": 1, "SUPER Fish": 240, "Dark Energy": 650}
    },
    "SPACE Sword": {
        "attack": 5000, "defense": 0, "area_req": 19, "type": "weapon",
        "materials": {"OMEGA Sword": 1, "Life Potion": 10, "Watermelon": 2100, "Dark Energy": 1000}
    },
    "SPACE Armor": {
        "attack": 0, "defense": 5000, "area_req": 19, "type": "armor",
        "materials": {"Lootbox Armor": 1, "ULTIMATE Log": 80, "GODLY Lootbox": 2}, "coin_cost": 42000000000000
    },
    "TIME Sword": {
        "attack": 10000, "defense": 0, "area_req": 20, "type": "weapon",
        "materials": {"EDGY Sword": 1, "VOID Lootbox": 1, "Dark Energy": 15000}, "time_travel_req": 5
    },
    "TIME Armor": {
        "attack": 0, "defense": 10000, "area_req": 20, "type": "armor",
        "materials": {"EDGY Armor": 1, "ULTIMATE Log": 500, "Dark Energy": 15000}, "time_travel_req": 5
    }
}

# Material conversion recipes
MATERIAL_CONVERSION = {
    "Epic Log": {"base": "Wooden Log", "cost": 25, "return": 20},
    "Super Log": {"base": "Wooden Log", "cost": 250, "return": 160},
    "Mega Log": {"base": "Wooden Log", "cost": 2500, "return": 1280},
    "HYPER Log": {"base": "Wooden Log", "cost": 25000, "return": 10240},
    "ULTRA Log": {"base": "Wooden Log", "cost": 250000, "return": 81920},
    "Golden Fish": {"base": "Normie Fish", "cost": 15, "return": 12},
    "EPIC Fish": {"base": "Normie Fish", "cost": 1500, "return": 960},
    "Banana": {"base": "Apple", "cost": 15, "return": 12}
}

# Cooking recipes
COOKING_RECIPES = {
    "Cooked Fish": {
        "materials": {"Normie Fish": 1},
        "effect": "attack_boost",
        "boost": 5,
        "description": "Increases attack by 5"
    },
    "Apple Pie": {
        "materials": {"Apple": 3, "Bread": 1},
        "effect": "defense_boost",
        "boost": 10,
        "description": "Increases defense by 10"
    },
    "Dragon Steak": {
        "materials": {"Dragon Scale": 1, "Normie Fish": 5},
        "effect": "hp_boost",
        "boost": 100,
        "description": "Increases max HP by 100"
    }
}

WEAPONS = {
    "Wooden Sword": {"attack": 5, "level_req": 1},
    "Iron Sword": {"attack": 15, "level_req": 10},
    "Steel Sword": {"attack": 25, "level_req": 20},
    "Magic Sword": {"attack": 40, "level_req": 35},
    "Dragon Sword": {"attack": 60, "level_req": 50},
    "Legendary Blade": {"attack": 100, "level_req": 75},
    "God Slayer": {"attack": 200, "level_req": 100}
}

# Area unlock commands
AREA_UNLOCKS = {
    2: ["enchant", "area", "training"],
    3: ["axe", "net", "pickup"],
    4: ["ladder", "guild", "farm"],
    5: ["mine", "multidice", "cook"],
    6: ["bowsaw", "boat", "pickaxe"],
    7: ["refine", "big arena", "alchemy"],
    8: ["tractor", "wheel"],
    9: ["chainsaw", "bigboat"],
    10: ["drill", "minintboss"],
    11: ["time travel", "forge", "greenhouse"],
    12: ["dynamite", "pets", "ultraining", "badge"],
    13: ["transmute", "hunt hardmode"],
    14: ["adventure hardmode", "bigdice"],
    15: ["super time travel", "transcend"]
}

# Dungeon data
DUNGEONS = {
    1: {
        "name": "Ancient Dragon",
        "key_price": 5000,
        "hp_per_player": 50,
        "attack": 37,
        "reward_min": 10000,
        "reward_max": 45000,
        "commands": {
            "bite": {"chance": 100, "damage": 120},
            "stab": {"chance": 70, "damage": 200},
            "power": {"chance": 40, "damage": 400}
        }
    },
    2: {
        "name": "The Too Ancient Dragon",
        "key_price": 25000,
        "hp_per_player": 225,
        "attack": 71,
        "reward_min": 30000,
        "reward_max": 50000,
        "commands": {
            "bite": {"chance": 100, "damage": 120},
            "stab": {"chance": 70, "damage": 200},
            "power": {"chance": 40, "damage": 400},
            "epic punch": {"chance": 5, "damage": 4000}
        }
    },
    3: {
        "name": "The Ancientest Dragon",
        "key_price": 60000,
        "hp_per_player": 425,
        "attack": 109,
        "reward_min": 50000,
        "reward_max": 70000,
        "commands": {
            "bite": {"chance": 100, "damage": 120},
            "stab": {"chance": 70, "damage": 200},
            "power": {"chance": 40, "damage": 400},
            "epic punch": {"chance": 5, "damage": 4000}
        }
    },
    4: {
        "name": "The Purple Dragon",
        "key_price": 150000,
        "hp_per_player": 625,
        "attack": 143,
        "reward_min": 75000,
        "reward_max": 110000,
        "commands": {
            "bite": {"chance": 100, "damage": 120},
            "stab": {"chance": 70, "damage": 200},
            "power": {"chance": 40, "damage": 400},
            "healing spell": {"chance": 90, "heal": 20}
        }
    },
    5: {
        "name": "The Huh Idk Dragon",
        "key_price": 350000,
        "hp_per_player": 1500,
        "attack": 179,
        "reward_min": 90000,
        "reward_max": 150000,
        "commands": {
            "bite": {"chance": 100, "damage": 120},
            "stab": {"chance": 70, "damage": 200},
            "power": {"chance": 40, "damage": 400},
            "healing spell": {"chance": 90, "heal": 20}
        }
    }
}

# Player data storage
player_data = {}
guild_data = {}


def load_player_data():
    try:
        with open('players.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_guild_data():
    try:
        with open('guilds.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_player_data():
    with open('players.json', 'w') as f:
        json.dump(player_data, f, indent=2)


def save_guild_data():
    with open('guilds.json', 'w') as f:
        json.dump(guild_data, f, indent=2)


def get_player(user_id):
    if str(user_id) not in player_data:
        return None  # Return None if player doesn't exist
    return player_data[str(user_id)]


def create_player(user_id):
    """Create a new player account"""
    player_data[str(user_id)] = {
        "level": 1,
        "exp": 0,
        "hp": 100,
        "max_hp": 100,
        "coins": 100,
        "area": 1,
        "max_area_reached": 1,
        "weapon": "Wooden Sword",
        "armor": None,
        "inventory": {"Wooden Sword": 1, "Wooden Log": 50, "Normie Fish": 20, "Apple": 10},
        "last_hunt": 0,
        "last_adventure": 0,
        "last_daily": 0,
        "daily_streak": 0,
        "job_levels": {"mining": 1, "fishing": 1, "woodcutting": 1, "crafter": 1},
        "time_travels": 0,
        "cooking_boosts": {"attack_boost": 0, "defense_boost": 0, "hp_boost": 0},
        "enchants": {},
        "guild": None,
        "guild_rings": 0,
        "titles": [],
        "active_title": None,
        "registered": True
    }
    return player_data[str(user_id)]


def check_player_registered(ctx):
    """Check if player is registered, send message if not"""
    player = get_player(ctx.author.id)
    if player is None:
        ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return False
    return True


def create_progress_bar(percentage, length=10, filled_char="█", empty_char="░"):
    """Create a visual progress bar"""
    filled_length = int(length * percentage)
    bar = filled_char * filled_length + empty_char * (length - filled_length)
    return f"[{bar}] {percentage:.1%}"


def level_up_check(player):
    exp_needed = player["level"] * 100
    if player["exp"] >= exp_needed:
        player["level"] += 1
        player["exp"] -= exp_needed
        player["max_hp"] += 20
        player["hp"] = player["max_hp"]
        return True
    return False


def get_unlocked_commands(area):
    """Get all commands unlocked up to the given area"""
    unlocked = []
    for unlock_area, commands in AREA_UNLOCKS.items():
        if area >= unlock_area:
            unlocked.extend(commands)
    return unlocked


def check_command_unlocked(player_area, command_name, max_area_reached=None):
    """Check if a command is unlocked for the player's max area reached"""
    # Use max_area_reached if provided, otherwise fall back to current area
    check_area = max_area_reached if max_area_reached is not None else player_area
    unlocked_commands = get_unlocked_commands(check_area)
    return command_name.lower() in [cmd.lower() for cmd in unlocked_commands]


def is_owner(user_id):
    """Check if user is the bot owner"""
    return user_id == OWNER_ID


@bot.command(name='start')
async def start_game(ctx):
    """Register a new player account"""
    existing_player = get_player(ctx.author.id)

    if existing_player is not None:
        await ctx.send("🎮 You already have an account! Your adventure continues...")
        return

    # Create new player
    player = create_player(ctx.author.id)

    embed = discord.Embed(title="🎮 Welcome to disRPG!",
                          description=f"Welcome, {ctx.author.display_name}! Your adventure begins now!", color=0x00ff00)
    embed.add_field(name="Starting Stats",
                    value=f"Level: {player['level']}\nHP: {player['hp']}/{player['max_hp']}\nCoins: {player['coins']}\nArea: {player['area']}",
                    inline=True)
    embed.add_field(name="Starting Equipment", value=f"Weapon: {player['weapon']}\nStarting materials included!",
                    inline=True)
    embed.add_field(name="Get Started",
                    value="Use `rpg commands` to see all available commands\nTry `rpg hunt` to start your first battle!",
                    inline=False)
    embed.add_field(name="Tip", value="Use `rpg profile` to view your stats anytime", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='hunt', aliases=['h'])
async def hunt(ctx, mode=None):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Check for hardmode
    is_hardmode = mode and mode.lower() in ['h', 'hardmode']

    if is_hardmode and not check_command_unlocked(player["area"], "hunt hardmode"):
        await ctx.send("🔒 Hunt Hardmode is unlocked in Area 13!")
        return

    # Cooldown check
    import time
    current_time = time.time()
    cooldown_time = 8 if is_hardmode else 10  # Hardmode has shorter cooldown
    if current_time - player["last_hunt"] < cooldown_time:
        await ctx.send("You need to rest before hunting again!")
        return

    player["last_hunt"] = current_time

    # Check if player can access current area
    area = AREAS[player["area"]]
    if player["level"] < area["level_req"]:
        await ctx.send(f"You need level {area['level_req']} to hunt in {area['name']}!")
        return

    # Random monster encounter
    monster = random.choice(area["monsters"])

    # Monster emoji mapping
    monster_emojis = {
        "Wolf": "<:Wolf:1385232162588196924>", "Slime": "<:Slime:1385232673139851304>",
        "Goblin": "<:Goblin:1385231475535904840>",
        "Nymph": "<:Nymph:1385232894657695855>", "Skeleton": "<:Skeleton:1385232713472016384>",
        "Zombie": "<:Zombie:1385232073765425183>", "Ghost": "<:Ghost:1385231356237316156>",
        "Baby Demon": "<:Baby_demon:1385230950895714384>",
        "Witch": "<:Witch:1385232178186682529>", "Imp": "<:Imp:1385231852016631898>",
        "Unicorn": "<:Area_5__Unicorn:1385230926174486628>", "Ghoul": "<:Ghoul:1385231367603753011>",
        "Giant Scorpion": "<:Area_5__Giant_Scorpion:1385230920365379614>",
        "Sorcerer": "<:Sorcerer:1385232628579434606>", "Baby Robot": "<:Baby_Robot:1385230959615672393>",
        "Mermaid": "<:Mermaid:1385233248375803994>", "Cecaelia": "<:Cecaelia:1385230992826044538>",
        "Giant Piranha": "<:Giant_Piranha:1385231440173858876>",
        "Nereid": "<:Nereid:1385232996520427571>", "Giant Crocodile": "<:Giant_Crocodile:1385231383496232981>",
        "Killer Robot": "<:Killer_Robot:1385232042173661287>", "Demon": "<:Demon:1385231209348595732>", "Harpy": "🦅",
        "Manticore": "<:Manticore:1385233266251927602>", "Dullahan": "<:Dullahan:1385231286032924722>",
        "Scaled Baby Dragon": "<:Scaled_baby_dragon:1385232813933989960>", "Baby Dragon": "🐉",
        "Young Dragon": "<:Young_dragon:1385232089154060398>",
        "Kid Dragon": "<:Kid_dragon:1385232021206601829>", "Scaled Kid Dragon": "🐲",
        "Not so Young Dragon": "<:Not_so_young_dragon:1385232953868681409>",
        "Teen Dragon": "<:Teen_dragon:1385232584132395059>", "Scaled Teen Dragon": "🐲",
        "Definitely Not Young Dragon": "<:Definetly_not_young_dragon:1385231194584776865>",
        "Adult Dragon": "<:Adult_dragon:1385230870981640202>", "Scaled Adult Dragon": "🐲",
        "Not Young at all Dragon": "<:Not_young_at_all_dragon:1385232936969699359>",
        "Old Dragon": "🐲", "Scaled Old Dragon": "<:Scaled_Old_Dragon:1385232795265405091>",
        "How do you dare call this Dragon \"young\"": "<:How_do_you_dare_call_this_dragon:1385231530158461019>",
        "Ancient Dragon": "<:Ancient_Dragon:1385230881840697476>", "Elder Dragon": "🐉", "Primordial Dragon": "🐲",
        "Cosmic Dragon": "🌌", "Void Dragon": "⚫", "Reality Dragon": "🌍",
        "Time Dragon": "⏰", "Space Dragon": "🌌", "Dimension Dragon": "🌀",
        "Omega Dragon": "💫", "Alpha Dragon": "⭐", "Genesis Dragon": "✨",
        "Final Dragon": "🔥", "Ultimate Dragon": "⚡", "Supreme Dragon": "👑",
        "Epic NPC": "🎮", "God of Games": "🎯", "The Creator": "✨",
        # Adventure-only monsters from Epic RPG wiki
        "Mutant Water Bottle": "<:Mutant_Water_Bottle:1385233103563522209>",
        "Giant Spider": "<:Giant_Spider:1385231462885757019>", "Bunch of Bees": "<:Bunch_of_bees:1385230980637528135>",
        "Ogre": "<:Ogre:1385232875191930910>", "Dark Knight": "<:Dark_Knight:1385231176083574814>",
        "Hyper Giant Bowl": "<:Hyper_Giant_bowl:1385231696584249464>",
        "Mutant Shoe": "<:Mutant_Shoe:1385233119832969387>", "Werewolf": "<:Werewolf:1385232210734485634>",
        "Centaur": "<:Centaur:1385231007166234735>",
        "Chimera": "<:Chimera:1385231021804617829>",
        "Hyper Giant Aeronautical Engine": "<:Hyper_Giant_Aeronautical_Engine:1385231569161031721>",
        "Golem": "<:Golem:1385231499342647386>",
        "Mammoth": "<:Mammoth:1385233279237754970>", "Mutant Esc Key": "<:Mutant_Esc_Key:1385233217283690586>",
        "Ent": "<:Ent:1385231301405315123>",
        "Dinosaur": "<:Dinosaur:1385231268890935428>", "Hyper Giant Door": "<:Hyper_Giant_Door:1385231730427957421>",
        "Cyclops": "<:Cyclops:1385231143531446302>",
        "Attack Helicopter": "<:Attack_Helicopter:1385230939076034622>",
        "Mutant Book": "<:Mutant_Book:1385233152775032934>", "Hydra": "<:Hydra:1385231549733011626>",
        "Kraken": "<:Kraken:1385232055574597764>", "Hyper Giant Chest": "<:Hyper_Giant_Chest:1385231714779140257>",
        "Leviathan": "<:Leviathan:1385233305066012744>",
        "War Tank": "<:War_Tank:1385232229390749797>", "Mutant Backpack": "<:Mutant_Backpack:1385233187105669170>",
        "Wyrm": "<:Wyrm:1385232124361052210>",
        "Hyper Giant Toilet": "<:Hyper_Giant_Toilet:1385231764468797462>", "Titan": "<:Titan:1385232413961228288>",
        "Typhon": "<:Typhon:1385232399100543016>",
        "Hyper Giant Dragon": "<:Hyper_giant_dragon:1385231748022931476>", "Even More Ancient Dragon": "🐲",
        "Ancientest Dragon": "<:Ancientest_Dragon:1385230898647007382>",
        "Another Mutant Dragon Like In Area 11 But Stronger": "<:Another_mutant_dragon_like_in_a1:1385230911313936404>",
        "Just Purple Dragon": "🟣",
        "Yes As You Expected Another Hyper Giant Dragon But Op Etc": "🐲",
        "I Have No More Ideas Dragon": "<:I_have_no_more_ideas_dragon:1385231829107347608>",
        "Mutantest Dragon": "<:Mutantest_dragon:1385233081425985658>"
    }

    if is_hardmode:
        # Hardmode: stronger monsters, better rewards
        monster_hp = random.randint(50, 120) + (player["area"] * 15)
        monster_attack = random.randint(15, 35) + (player["area"] * 8)
        reward_multiplier = 1.5
        mode_text = "HARDMODE "
    else:
        # Normal mode
        monster_hp = random.randint(30, 80) + (player["area"] * 10)
        monster_attack = random.randint(10, 25) + (player["area"] * 5)
        reward_multiplier = 1.0
        mode_text = ""

    # Player attack power
    weapon = WEAPONS.get(player["weapon"], {"attack": 5})
    player_attack = weapon["attack"] + random.randint(5, 15)

    # Calculate if player is too high level (no damage taken)
    level_advantage = player["level"] - area["level_req"]
    takes_no_damage = level_advantage >= 20  # If 20+ levels above area requirement

    # Always victory for simplicity - player always kills the monster
    base_exp = int((random.randint(20, 40) + (player["area"] * 5)) * reward_multiplier)
    coin_gain = int((random.randint(10, 30) + (player["area"] * 3)) * reward_multiplier)

    # Apply TT EXP bonus
    tt_bonuses = calculate_tt_bonuses(player.get("time_travels", 0))
    exp_multiplier = 1 + (tt_bonuses["exp"] / 100)
    exp_gain = int(base_exp * exp_multiplier)

    # Apply guild EXP bonus if in guild
    if player.get("guild"):
        guild = guild_data.get(player["guild"])
        if guild:
            guild_bonus = guild["level"] * 0.02  # 2% per guild level
            exp_gain = int(exp_gain * (1 + guild_bonus))
            coin_gain = int(coin_gain * (1 + guild_bonus))

    # Scale rewards for higher level players
    if player["level"] > 50:
        coin_gain *= (player["level"] // 10)
        exp_gain *= (player["level"] // 20 + 1)

    player["exp"] += exp_gain
    player["coins"] += coin_gain

    # Calculate damage taken
    damage_taken = 0
    if not takes_no_damage:
        # Calculate damage based on monster attack vs player defense
        base_damage = random.randint(8 if is_hardmode else 5, 25 if is_hardmode else 15)
        # Reduce damage if player is higher level
        damage_reduction = max(0, level_advantage * 0.1)  # 10% reduction per level advantage
        damage_taken = max(0, int(base_damage * (1 - damage_reduction)))

        player["hp"] -= damage_taken
        if player["hp"] < 0:
            player["hp"] = 0

    monster_emoji = monster_emojis.get(monster, "👹")

    # Create beautiful embed instead of plain text
    embed = discord.Embed(
        title=f"⚔️ {mode_text}Combat Report",
        description=f"**{ctx.author.display_name}** encountered a {monster_emoji} **{monster.upper()}**",
        color=EMBED_COLORS["combat"]
    )

    # Add monster thumbnail (you can replace with actual images)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1234567890.png")

    # Battle results with visual bars
    hp_percentage = player['hp'] / player['max_hp']
    hp_bar = create_progress_bar(hp_percentage, 10, "🟩", "🟥")

    embed.add_field(
        name="💀 Battle Result",
        value=f"Defeated the {monster_emoji} **{monster.upper()}**",
        inline=False
    )

    embed.add_field(
        name="💰 Rewards Earned",
        value=f"```yaml\nCoins: +{coin_gain:,}\nEXP:   +{exp_gain:,}```",
        inline=True
    )

    embed.add_field(
        name="❤️ Health Status",
        value=f"```diff\n- Damage Taken: {damage_taken}\n+ HP Remaining: {player['hp']}/{player['max_hp']}```\n{hp_bar}",
        inline=True
    )

    # Add area context
    embed.add_field(
        name="🗺️ Location",
        value=f"Area {player['area']} - {AREAS[player['area']]['name']}",
        inline=True
    )

    result_message = ""

    # Check for mob drops and add to embed
    rare_drops = []

    # Check specific mob drops
    if monster in MOB_DROPS:
        drop_data = MOB_DROPS[monster]
        base_chance = 7  # 7% base hunt drop chance
        mob_chance = drop_data["chance"]
        tt_bonus = tt_bonuses["drops"] / 100  # Convert percentage to multiplier
        hardmode_bonus = 0.5 if is_hardmode else 0  # 50% better drop chance in hardmode
        total_chance = (base_chance + mob_chance) * (1 + tt_bonus + hardmode_bonus)

        if random.random() * 100 < total_chance:
            drop_item = drop_data["item"]
            if drop_item not in player["inventory"]:
                player["inventory"][drop_item] = 0
            player["inventory"][drop_item] += 1

            # Format drop message with emoji
            drop_emoji = {
                "Wolf Skin": "🐺",
                "Zombie Eye": "👁️",
                "Unicorn Horn": "🦄",
                "Mermaid Hair": "🧜‍♀️",
                "Chip": "🤖",
                "Dragon Scale": "🐲"
            }.get(drop_item, "💎")

            rare_drops.append(f"{drop_emoji} **{drop_item}** x1")

    # Check for Dark Energy (Areas 16-20)
    if 16 <= player["area"] <= 20:
        dark_chance = DARK_ENERGY_DROP["chance"] * (1 + tt_bonus + (0.5 if is_hardmode else 0))
        if random.random() * 100 < dark_chance:
            if "Dark Energy" not in player["inventory"]:
                player["inventory"]["Dark Energy"] = 0
            player["inventory"]["Dark Energy"] += 1
            rare_drops.append("🌌 **Dark Energy** x1")

    # Add rare drops to embed if any
    if rare_drops:
        embed.add_field(
            name="✨ Rare Drops!",
            value="\n".join(rare_drops),
            inline=False
        )
        embed.color = EMBED_COLORS["rare"]

    # Check level up and enhance embed
    if level_up_check(player):
        embed.add_field(
            name="🎊 LEVEL UP!",
            value=f"Congratulations! You reached **Level {player['level']}**!\n+20 Max HP gained!",
            inline=False
        )
        embed.color = EMBED_COLORS["level_up"]

        # Add celebration footer
        embed.set_footer(text="🎉 Keep adventuring to unlock new areas and commands!")

    # Add timestamp and author
    embed.timestamp = discord.utils.utcnow()
    embed.set_author(name=ctx.author.display_name,
                     icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='stats')
async def stats(ctx):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return
    area_name = AREAS[player["area"]]["name"]

    embed = discord.Embed(title=f"📊 {ctx.author.display_name}'s Stats", color=0x0099ff)
    embed.add_field(name="Level", value=player["level"], inline=True)
    embed.add_field(name="EXP", value=f"{player['exp']}/{player['level'] * 100}", inline=True)
    embed.add_field(name="HP", value=f"{player['hp']}/{player['max_hp']}", inline=True)
    embed.add_field(name="Coins", value=player["coins"], inline=True)
    embed.add_field(name="Current Area", value=f"{player['area']} - {area_name}", inline=True)
    embed.add_field(name="Weapon", value=player["weapon"], inline=True)

    await ctx.send(embed=embed)


@bot.command(name='heal')
async def heal(ctx):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Check if player is at max HP or has life boost
    current_hp = player["hp"]
    max_hp = player["max_hp"]

    if current_hp >= max_hp:
        await ctx.send("You're already at full health!")
        return

    # Check for life potions first
    if player["inventory"].get("life potion", 0) > 0:
        # Use life potion
        player["inventory"]["life potion"] -= 1
        if player["inventory"]["life potion"] <= 0:
            del player["inventory"]["life potion"]

        player["hp"] = player["max_hp"]

        # Check for heal event (0.75% chance in area 6+)
        if player["area"] >= 6 and random.random() * 100 < 0.75:
            await handle_heal_event(ctx, player)
            save_player_data()
            return

        embed = discord.Embed(title="💊 Life Potion Used", color=0x00ff00)
        embed.add_field(name="Result", value=f"HP restored to {player['max_hp']}", inline=False)
        embed.add_field(name="Life Potions Remaining", value=player["inventory"].get("life potion", 0), inline=False)

        save_player_data()
        await ctx.send(embed=embed)
        return

    # No life potions, check for coins
    heal_cost = 50
    if player["coins"] < heal_cost:
        await ctx.send(
            "You don't have enough coins to heal! Buy life potions with `rpg buy life potion` or earn them from daily rewards.")
        return

    player["hp"] = player["max_hp"]
    player["coins"] -= heal_cost

    # Check for heal event (0.75% chance in area 6+)
    if player["area"] >= 6 and random.random() * 100 < 0.75:
        await handle_heal_event(ctx, player)
        save_player_data()
        return

    # Area 16+ HP loss penalty
    if player["area"] >= 16:
        hp_loss = max(1, int(player["max_hp"] * 0.01))  # 1% of max HP
        player["max_hp"] -= hp_loss
        player["hp"] = player["max_hp"]

        embed = discord.Embed(title="💊 Healing Complete", color=0xffaa00)
        embed.add_field(name="Result", value=f"HP restored but max HP reduced by {hp_loss} due to Area 16+ penalty",
                        inline=False)
        embed.add_field(name="New Max HP", value=f"{player['max_hp']}", inline=True)
        embed.add_field(name="Cost", value=f"{heal_cost} coins", inline=True)
        embed.add_field(name="Tip", value="Use life potions or brew potion potions to avoid this penalty!",
                        inline=False)
    else:
        embed = discord.Embed(title="💊 Healing Complete", color=0x00ff00)
        embed.add_field(name="Result", value=f"HP restored to {player['max_hp']}", inline=False)
        embed.add_field(name="Cost", value=f"{heal_cost} coins", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


async def handle_heal_event(ctx, player):
    """Handle the mysterious heal event"""
    embed = discord.Embed(title="😴 Mysterious Event", color=0x800080)
    embed.add_field(name="What happened?",
                    value="Your rest got interrupted! You notice that someone stole your money and gear!",
                    inline=False)
    embed.add_field(name="What do you do?",
                    value="React with 😭 to **Cry** or 🔍 to **Search** for the mysterious person!",
                    inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("😭")
    await message.add_reaction("🔍")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["😭", "🔍"] and reaction.message.id == message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)

        if str(reaction.emoji) == "😭":
            # Cry - safe option
            embed = discord.Embed(title="😭 You cried yourself to sleep...", color=0x00ff00)
            embed.add_field(name="Result",
                            value="You woke up hoping it was all a dream. Your HP is restored and nothing else happened.",
                            inline=False)
            player["hp"] = player["max_hp"]

        elif str(reaction.emoji) == "🔍":
            # Search - leads to more choices
            embed = discord.Embed(title="🔍 You decide to search...", color=0x800080)
            embed.add_field(name="You found the mysterious person!",
                            value="React with 😭 to **Cry** or ⚔️ to **Fight**!",
                            inline=False)

            await message.clear_reactions()
            await message.edit(embed=embed)
            await message.add_reaction("😭")
            await message.add_reaction("⚔️")

            try:
                reaction2, user2 = await bot.wait_for('reaction_add', timeout=30.0,
                                                      check=lambda r, u: u == ctx.author and str(r.emoji) in ["😭",
                                                                                                              "⚔️"] and r.message.id == message.id)

                if str(reaction2.emoji) == "😭":
                    # Cry again
                    embed = discord.Embed(title="😭 You cried...", color=0x00ff00)
                    embed.add_field(name="Result",
                                    value="The mysterious person felt bad and left. Your HP is restored.", inline=False)
                    player["hp"] = player["max_hp"]

                elif str(reaction2.emoji) == "⚔️":
                    # Fight - 50/50 chance
                    if random.random() < 0.5:
                        # Victory - gain a level
                        old_level = player["level"]
                        player["level"] += 1
                        player["max_hp"] += 20
                        player["hp"] = player["max_hp"]

                        embed = discord.Embed(title="⚔️ Victory!", color=0x00ff00)
                        embed.add_field(name="Result",
                                        value=f"You defeated the mysterious person and gained a level! ({old_level} → {player['level']})",
                                        inline=False)
                        embed.add_field(name="Bonus", value=f"Max HP increased to {player['max_hp']}", inline=False)
                    else:
                        # Defeat - lose a level
                        if player["level"] > 1:
                            old_level = player["level"]
                            player["level"] -= 1
                            player["max_hp"] = max(100, player["max_hp"] - 20)
                            player["hp"] = player["max_hp"]

                            embed = discord.Embed(title="💀 Defeat!", color=0xff0000)
                            embed.add_field(name="Result",
                                            value=f"The mysterious person was too strong! You lost a level. ({old_level} → {player['level']})",
                                            inline=False)
                            embed.add_field(name="Penalty", value=f"Max HP reduced to {player['max_hp']}", inline=False)
                        else:
                            player["hp"] = player["max_hp"]
                            embed = discord.Embed(title="💀 Defeat!", color=0xff0000)
                            embed.add_field(name="Result",
                                            value="The mysterious person was too strong, but you can't lose any more levels!",
                                            inline=False)

            except asyncio.TimeoutError:
                embed = discord.Embed(title="⏰ No Response", color=0x808080)
                embed.add_field(name="Result", value="You took too long to decide. Your HP is restored normally.",
                                inline=False)
                player["hp"] = player["max_hp"]

    except asyncio.TimeoutError:
        embed = discord.Embed(title="⏰ No Response", color=0x808080)
        embed.add_field(name="Result", value="You took too long to decide. Your HP is restored normally.", inline=False)
        player["hp"] = player["max_hp"]

    await message.edit(embed=embed)
    await message.clear_reactions()


@bot.command(name='area')
async def area_command(ctx, action=None, area_num=None):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Check if first parameter is a number (rpgs area <number>)
    if action and not area_num:
        try:
            target_area = int(action)
            # Treat as rpgs area <area> = rpgs area move <area>
            action = "move"
            area_num = str(target_area)
        except ValueError:
            # Not a number, continue with normal logic
            pass

    if action == "move" and area_num:
        try:
            target_area = int(area_num)
            if target_area < 1 or target_area > 21:
                await ctx.send("Area must be between 1 and 21!")
                return

            if target_area > player["area"] + 1:
                await ctx.send("You can only move to the next area!")
                return

            area_info = AREAS[target_area]
            if player["level"] < area_info["level_req"]:
                await ctx.send(f"You need level {area_info['level_req']} to enter {area_info['name']}!")
                return

            old_area = player["area"]
            player["area"] = target_area

            # Update max area reached
            if "max_area_reached" not in player:
                player["max_area_reached"] = old_area
            player["max_area_reached"] = max(player["max_area_reached"], target_area)

            # Check for newly unlocked commands
            newly_unlocked = []
            if target_area in AREA_UNLOCKS:
                newly_unlocked = AREA_UNLOCKS[target_area]

            save_player_data()

            embed = discord.Embed(title=f"🗺️ Area Progress", color=0x00ff00)
            embed.add_field(name="New Location", value=f"Area {target_area} - {area_info['name']}", inline=False)

            if newly_unlocked:
                embed.add_field(name="🎉 New Commands Unlocked!", value=", ".join(newly_unlocked), inline=False)
                embed.add_field(name="Note", value="Try out your new commands!", inline=False)

            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("Please provide a valid area number!")
    else:
        # Show current area info
        current_area = AREAS[player["area"]]
        embed = discord.Embed(title=f"🗺️ Area {player['area']} - {current_area['name']}", color=0x9932cc)
        embed.add_field(name="Level Requirement", value=current_area["level_req"], inline=True)
        embed.add_field(name="Monsters", value=", ".join(current_area["monsters"]), inline=False)

        if player["area"] < 21:
            next_area = AREAS[player["area"] + 1]
            embed.add_field(name="Next Area",
                            value=f"Area {player['area'] + 1} - {next_area['name']} (Level {next_area['level_req']})",
                            inline=False)

        # Show unlocked commands for current area
        unlocked_commands = get_unlocked_commands(player["area"])
        if unlocked_commands:
            embed.add_field(name="Unlocked Commands", value=", ".join(unlocked_commands), inline=False)

        # Show what commands will unlock in next area
        if player["area"] + 1 in AREA_UNLOCKS:
            next_unlocks = AREA_UNLOCKS[player["area"] + 1]
            embed.add_field(name="Next Area Unlocks", value=", ".join(next_unlocks), inline=False)

        await ctx.send(embed=embed)


@bot.command(name='inventory')
async def inventory(ctx):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    embed = discord.Embed(title=f"🎒 {ctx.author.display_name}'s Inventory", color=0xffd700)

    if player["inventory"]:
        inv_text = ""
        for item, quantity in player["inventory"].items():
            inv_text += f"{item}: {quantity}\n"
        embed.add_field(name="Items", value=inv_text, inline=False)
    else:
        embed.add_field(name="Items", value="Empty", inline=False)

    embed.add_field(name="Coins", value=player["coins"], inline=True)

    await ctx.send(embed=embed)


@bot.command(name='shop')
async def shop(ctx, page=None):
    player = get_player(ctx.author.id)

    if page == "2":
        # Page 2 - Lootboxes and Special Items
        embed = discord.Embed(
            title="🏪 Mystical Marketplace",
            description="*Premium Lootboxes & Special Items*",
            color=EMBED_COLORS["economy"]
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1234567890.png")  # Replace with actual lootbox icon

        # Lootboxes with enhanced display
        lootbox_list = []
        for name, data in SHOP_ITEMS["lootboxes"].items():
            if player and player["level"] >= data["level_req"]:
                status = "✅ Available"
                price_color = "+"
            else:
                status = f"🔒 Requires Level {data['level_req']}"
                price_color = "-"

            alias = f" `{data['alias']}`" if "alias" in data else ""
            lootbox_list.append(f"{price_color} {name}{alias}\n  💰 {data['price']:,} coins • {status}")

        embed.add_field(
            name="🎁 Premium Lootboxes",
            value=f"```diff\n" + "\n".join(lootbox_list) + "```",
            inline=False
        )

        embed.add_field(
            name="⚠️ Purchase Rules",
            value="```yaml\nCooldown: 3 hours between purchases\nRequirement: Must meet level requirements\nBonus: Higher tiers = better rewards```",
            inline=False
        )

        embed.add_field(
            name="🛏️ Special Item",
            value=f"```css\nMagic Bed - {SHOP_ITEMS['other']['magic bed']['price']} coins\n{SHOP_ITEMS['other']['magic bed']['description']}```",
            inline=False
        )

    else:
        # Page 1 - Basic Items with enhanced layout
        embed = discord.Embed(
            title="🏪 Adventure Outfitters",
            description="*Essential Items & Equipment*",
            color=EMBED_COLORS["economy"]
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1234567890.png")  # Replace with actual shop icon

        # Basic Items in organized format
        basic_items = []
        for name, data in SHOP_ITEMS["basic_items"].items():
            if isinstance(data['price'], str):
                price_str = data['price']
            else:
                price_str = f"{data['price']:,} coins"
            basic_items.append(f"• **{name}** - {price_str}\n  *{data['description']}*")

        embed.add_field(
            name="🛡️ Essential Equipment",
            value="\n\n".join(basic_items),
            inline=False
        )

        # Life Boosts with pricing tiers
        boost_items = []
        for name, data in SHOP_ITEMS["boosts"].items():
            boost_items.append(f"• **{name}** - {data['price']:,} coins\n  *{data['description']}*")

        embed.add_field(
            name="💊 Health Enhancement",
            value="\n\n".join(boost_items),
            inline=False
        )

        # Quick access items
        embed.add_field(
            name="🎲 Quick Access",
            value=f"```yaml\nLottery Ticket: {SHOP_ITEMS['lottery']['lottery ticket']['description']}\nGarden Seed:    {SHOP_ITEMS['farming']['seed']['price']:,} coins - {SHOP_ITEMS['farming']['seed']['description']}```",
            inline=False
        )

    # Player's current coins and navigation
    embed.add_field(
        name="💰 Your Wallet",
        value=f"```yaml\nCurrent Balance: {player['coins']:,} coins```",
        inline=True
    )

    nav_text = "📄 `rpg shop` - Basic Items\n📄 `rpg shop 2` - Lootboxes\n🛒 `rpg buy <item>` - Purchase"
    embed.add_field(
        name="🧭 Navigation",
        value=nav_text,
        inline=True
    )

    embed.set_footer(text="💡 Tip: Higher areas unlock better equipment in the craft system!")
    await ctx.send(embed=embed)


@bot.command(name='buy')
async def buy(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to buy! Use `rpg shop` to see available items.")
        return

    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    item_name_lower = item_name.lower()
    item_found = None
    item_data = None
    item_category = None

    # Check all shop categories for the item
    for category, items in SHOP_ITEMS.items():
        for item, data in items.items():
            if item.lower() == item_name_lower or (data.get("alias") and data["alias"].lower() == item_name_lower):
                item_found = item
                item_data = data
                item_category = category
                break
        if item_found:
            break

    # Check for dungeon key
    if not item_found and "dungeon key" in item_name_lower:
        # Player wants to buy a dungeon key for their current area
        if player["area"] in DUNGEON_KEY_PRICES:
            price = DUNGEON_KEY_PRICES[player["area"]]
            if player["coins"] < price:
                await ctx.send(f"You need {price:,} coins to buy a dungeon key for Area {player['area']}!")
                return

            player["coins"] -= price
            key_name = f"Dungeon {player['area']} Key"
            if key_name not in player["inventory"]:
                player["inventory"][key_name] = 0
            player["inventory"][key_name] += 1

            embed = discord.Embed(title="🔑 Dungeon Key Purchased", color=0x00ff00)
            embed.add_field(name="Item", value=key_name, inline=True)
            embed.add_field(name="Cost", value=f"{price:,} coins", inline=True)

            save_player_data()
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send(f"No dungeon key available for Area {player['area']}!")
            return

    # Check weapons as fallback
    if not item_found:
        for weapon in WEAPONS:
            if weapon.lower() == item_name_lower:
                weapon_stats = WEAPONS[weapon]
                price = weapon_stats["attack"] * 10

                if player["level"] < weapon_stats["level_req"]:
                    await ctx.send(f"You need level {weapon_stats['level_req']} to buy this weapon!")
                    return

                if player["coins"] < price:
                    await ctx.send(f"You need {price} coins to buy this weapon!")
                    return

                player["coins"] -= price
                player["weapon"] = weapon
                if weapon not in player["inventory"]:
                    player["inventory"][weapon] = 0
                player["inventory"][weapon] += 1

                embed = discord.Embed(title="🛒 Weapon Purchased", color=0x00ff00)
                embed.add_field(name="Weapon", value=weapon, inline=True)
                embed.add_field(name="Cost", value=f"{price} coins", inline=True)
                embed.add_field(name="Attack Power", value=weapon_stats["attack"], inline=True)

                save_player_data()
                await ctx.send(embed=embed)
                return

    if not item_found:
        await ctx.send("Item not found! Use `rpg shop` to see available items.")
        return

    # Handle special pricing
    if item_data["price"] == "varies":
        await ctx.send("Lottery ticket prices vary. Check current lottery for pricing!")
        return

    if isinstance(item_data["price"], str) and "essence" in item_data["price"]:
        await ctx.send("This item requires Time Dragon essences, not coins!")
        return

    price = item_data["price"]

    # Check level requirement for lootboxes
    if item_category == "lootboxes" and "level_req" in item_data:
        if player["level"] < item_data["level_req"]:
            await ctx.send(f"You need level {item_data['level_req']} to buy {item_found}!")
            return

    # Check if player has enough coins
    if player["coins"] < price:
        await ctx.send(f"You need {price:,} coins to buy {item_found}!")
        return

    # Special items handling
    if item_found == "life potion":
        # Add life potion to inventory instead of using immediately
        player["coins"] -= price
        if "life potion" not in player["inventory"]:
            player["inventory"]["life potion"] = 0
        player["inventory"]["life potion"] += 1

        embed = discord.Embed(title="💊 Life Potion Purchased", color=0x00ff00)
        embed.add_field(name="Item", value="Life Potion", inline=True)
        embed.add_field(name="Cost", value=f"{price} coins", inline=True)
        embed.add_field(name="Total Life Potions", value=player["inventory"]["life potion"], inline=True)
        embed.add_field(name="Usage", value="Use `rpg heal` to consume a life potion when injured", inline=False)

    elif item_found == "basic horse":
        # Give player a horse
        if "horse" in player:
            await ctx.send("You already have a horse!")
            return

        player["coins"] -= price
        player["horse"] = {
            "tier": 1,
            "level": 1,
            "type": "normie",
            "epicness": 0
        }

        embed = discord.Embed(title="🐴 Horse Purchased", color=0x00ff00)
        embed.add_field(name="Horse", value="Basic Horse (Tier I)", inline=True)
        embed.add_field(name="Cost", value=f"{price} coins", inline=True)

    elif "boost" in item_found:
        # Life boost items
        player["coins"] -= price
        boost_amount = 10 if "A" in item_found else (25 if "B" in item_found else 50)
        player["hp"] += boost_amount

        embed = discord.Embed(title="💊 Life Boost Applied", color=0x00ff00)
        embed.add_field(name="Boost", value=f"+{boost_amount} temporary HP", inline=True)
        embed.add_field(name="Cost", value=f"{price:,} coins", inline=True)
        embed.add_field(name="Current HP", value=f"{player['hp']}/{player['max_hp']}", inline=True)

    else:
        # Regular item purchase
        player["coins"] -= price
        if item_found not in player["inventory"]:
            player["inventory"][item_found] = 0
        player["inventory"][item_found] += 1

        embed = discord.Embed(title="🛒 Purchase Complete", color=0x00ff00)
        embed.add_field(name="Item Purchased", value=item_found, inline=True)
        embed.add_field(name="Cost", value=f"{price:,} coins", inline=True)
        embed.add_field(name="Description", value=item_data["description"], inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='epicshop', aliases=['eshop'])
async def epic_shop(ctx, category=None):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    epic_coins = player.get("epic_coins", 0)

    if category == "upgrades":
        embed = discord.Embed(title="⚡ Epic Shop - Upgrades", color=0x9932cc)
        upgrade_text = ""
        for name, data in EPIC_SHOP_ITEMS["upgrades"].items():
            upgrade_text += f"**{name}** - {data['price']} Epic Coins\n{data['description']}\n\n"
        embed.add_field(name="Available Upgrades", value=upgrade_text, inline=False)

    elif category == "backgrounds":
        embed = discord.Embed(title="🖼️ Epic Shop - Backgrounds", color=0x9932cc)
        bg_text = ""
        for name, data in EPIC_SHOP_ITEMS["backgrounds"].items():
            bg_text += f"**{name}** - {data['price']} Epic Coins\n{data['description']}\n\n"
        embed.add_field(name="Available Backgrounds", value=bg_text, inline=False)

    elif category == "consumables":
        embed = discord.Embed(title="🧪 Epic Shop - Consumables", color=0x9932cc)
        consumable_text = ""
        for name, data in EPIC_SHOP_ITEMS["consumables"].items():
            consumable_text += f"**{name}** - {data['price']} Epic Coins\n{data['description']}\n\n"
        embed.add_field(name="Available Consumables", value=consumable_text, inline=False)

    else:
        embed = discord.Embed(title="⭐ Epic Shop", description="Premium items for Epic Coins", color=0x9932cc)
        embed.add_field(name="Categories",
                        value="`rpg epicshop upgrades` - Permanent upgrades\n`rpg epicshop backgrounds` - Profile backgrounds\n`rpg epicshop consumables` - Temporary boosts",
                        inline=False)
        embed.add_field(name="Note", value="Epic Coins are earned through special events, voting, and achievements!",
                        inline=False)

    embed.add_field(name="Your Epic Coins", value=f"💎 {epic_coins}", inline=True)
    embed.add_field(name="Usage", value="Use `rpg buy <item_name>` to purchase with Epic Coins", inline=False)

    await ctx.send(embed=embed)


@bot.command(name='leaderboard', aliases=['top', 'ranking'])
async def leaderboard(ctx, leaderboard_type="level", page=1):
    if not player_data:
        await ctx.send("No players found!")
        return

    try:
        page = int(page)
        if page < 1:
            page = 1
    except:
        page = 1

    # Different leaderboard types
    if leaderboard_type.lower() in ["level", "lvl"]:
        sorted_players = sorted(player_data.items(), key=lambda x: (x[1]["level"], x[1]["exp"]), reverse=True)
        title = "🏆 Level Leaderboard"
        value_format = lambda data: f"Level {data['level']} (Area {data['area']})"

    elif leaderboard_type.lower() in ["coins", "coin"]:
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]["coins"], reverse=True)
        title = "💰 Coins Leaderboard"
        value_format = lambda data: f"{data['coins']:,} coins"

    elif leaderboard_type.lower() in ["timetravel", "tt"]:
        sorted_players = sorted(player_data.items(), key=lambda x: x[1].get("time_travels", 0), reverse=True)
        title = "⏰ Time Travel Leaderboard"
        value_format = lambda data: f"{data.get('time_travels', 0)} TTs"

    else:
        # Default to level leaderboard
        sorted_players = sorted(player_data.items(), key=lambda x: (x[1]["level"], x[1]["exp"]), reverse=True)
        title = "🏆 Level Leaderboard"
        value_format = lambda data: f"Level {data['level']} (Area {data['area']})"

    # Pagination
    per_page = 10
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_players = sorted_players[start_idx:end_idx]

    if not page_players:
        await ctx.send("No players found on this page!")
        return

    embed = discord.Embed(title=title, color=0xffd700)

    leaderboard_text = ""
    for i, (user_id, data) in enumerate(page_players):
        try:
            user = bot.get_user(int(user_id))
            username = user.display_name if user else f"User {user_id}"
            rank = start_idx + i + 1
            leaderboard_text += f"{rank}. {username} - {value_format(data)}\n"
        except:
            rank = start_idx + i + 1
            leaderboard_text += f"{rank}. Unknown User - {value_format(data)}\n"

    embed.add_field(name="Rankings", value=leaderboard_text, inline=False)

    # Show available leaderboard types
    if leaderboard_type == "level":
        embed.add_field(name="Other Leaderboards",
                        value="`rpg top coins` - Richest players\n`rpg top tt` - Most time travels",
                        inline=False)

    # Pagination info
    total_pages = (len(sorted_players) + per_page - 1) // per_page
    embed.add_field(name="Navigation",
                    value=f"Page {page}/{total_pages}\nUse `rpg top {leaderboard_type} {page + 1}` for next page",
                    inline=False)

    await ctx.send(embed=embed)


@bot.command(name='profile', aliases=['p'])
async def profile(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author

    player = get_player(user.id)
    if player is None:
        if user == ctx.author:
            await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        else:
            await ctx.send(f"{user.display_name} hasn't started their adventure yet!")
        return
    area_name = AREAS[player["area"]]["name"]

    # Build title display
    title_display = user.display_name
    if player.get("active_title"):
        title_display = f"{player['active_title']} {user.display_name}"

    embed = discord.Embed(
        title=f"👤 {title_display}",
        description=f"*Adventure Profile*",
        color=EMBED_COLORS["info"]
    )
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

    # Level and EXP with progress bar
    exp_percentage = player['exp'] / (player['level'] * 100)
    exp_bar = create_progress_bar(exp_percentage, 15, "🔹", "▫️")
    embed.add_field(
        name="📈 Character Progress",
        value=f"```yaml\nLevel: {player['level']}\nEXP:   {player['exp']:,}/{player['level'] * 100:,}```\n{exp_bar}",
        inline=False
    )

    # Health with visual bar
    hp_percentage = player['hp'] / player['max_hp']
    hp_bar = create_progress_bar(hp_percentage, 15, "❤️", "🤍")
    embed.add_field(
        name="❤️ Health Status",
        value=f"```diff\n+ HP: {player['hp']}/{player['max_hp']}```\n{hp_bar}",
        inline=True
    )

    # Wealth display
    embed.add_field(
        name="💰 Wealth",
        value=f"```yaml\nCoins: {player['coins']:,}```",
        inline=True
    )

    # Location and Equipment
    embed.add_field(
        name="🗺️ Location & Gear",
        value=f"```yaml\nArea:   {player['area']} - {area_name}\nWeapon: {player['weapon']}\nArmor:  {player.get('armor', 'None')}```",
        inline=False
    )

    # Time travel info with special styling
    tt_count = player.get("time_travels", 0)
    if tt_count > 0:
        tt_bonuses = calculate_tt_bonuses(tt_count)
        embed.add_field(
            name="⏰ Time Mastery",
            value=f"```css\nTime Travels: {tt_count}\nEXP Bonus:    +{tt_bonuses['exp']}%\nDrop Bonus:   +{tt_bonuses['drops']}%```",
            inline=True
        )

    # Guild info with enhanced display
    if player.get("guild"):
        guild = guild_data.get(player["guild"])
        if guild:
            role = "👑 Owner" if str(user.id) == guild["owner"] else "👤 Member"
            embed.add_field(
                name="🏰 Guild Affiliation",
                value=f"```yaml\nGuild: {guild['name']}\nRole:  {role}\nLevel: {guild['level']}\nRings: {player.get('guild_rings', 0)}```",
                inline=True
            )

    # Achievements section
    achievements = []
    if player.get("titles"):
        achievements.append(f"🏆 {len(player['titles'])} Titles")
    if tt_count > 0:
        achievements.append(f"⏰ Time Traveler")
    if player["level"] >= 50:
        achievements.append(f"⭐ Veteran")
    if player["area"] >= 15:
        achievements.append(f"🌌 Dragon Slayer")

    if achievements:
        embed.add_field(
            name="🎖️ Achievements",
            value=" • ".join(achievements),
            inline=False
        )

    # Add footer with last activity or status
    embed.set_footer(text=f"Adventuring since {area_name} • Use 'rpg help' for commands")
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)


@bot.command(name='adventure', aliases=['adv'])
async def adventure(ctx, mode=None):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Check for hardmode
    is_hardmode = mode and mode.lower() in ['h', 'hardmode']

    if is_hardmode and not check_command_unlocked(player["area"], "adventure hardmode"):
        await ctx.send("🔒 Adventure Hardmode is unlocked in Area 14!")
        return

    # Cooldown check
    import time
    current_time = time.time()
    cooldown_time = 45 if is_hardmode else 60  # Hardmode has shorter cooldown
    if current_time - player.get("last_adventure", 0) < cooldown_time:
        await ctx.send("You need to rest before going on another adventure!")
        return

    player["last_adventure"] = current_time

    # Check if player can access current area
    area = AREAS[player["area"]]
    if player["level"] < area["level_req"]:
        await ctx.send(f"You need level {area['level_req']} to adventure in {area['name']}!")
        return

    # Stronger enemy encounter
    base_monster = random.choice(area['monsters'])

    # Monster emoji mapping
    monster_emojis = {
        "Wolf": "<:Wolf:1385232162588196924>", "Slime": "<:Slime:1385232673139851304>",
        "Goblin": "<:Goblin:1385231475535904840>",
        "Nymph": "<:Nymph:1385232894657695855>", "Skeleton": "<:Skeleton:1385232713472016384>",
        "Zombie": "<:Zombie:1385232073765425183>", "Ghost": "<:Ghost:1385231356237316156>",
        "Baby Demon": "<:Baby_demon:1385230950895714384>",
        "Witch": "<:Witch:1385232178186682529>", "Imp": "<:Imp:1385231852016631898>",
        "Unicorn": "<:Area_5__Unicorn:1385230926174486628>", "Ghoul": "<:Ghoul:1385231367603753011>",
        "Giant Scorpion": "<:Area_5__Giant_Scorpion:1385230920365379614>",
        "Sorcerer": "<:Sorcerer:1385232628579434606>", "Baby Robot": "<:Baby_Robot:1385230959615672393>",
        "Mermaid": "<:Mermaid:1385233248375803994>", "Cecaelia": "<:Cecaelia:1385230992826044538>",
        "Giant Piranha": "<:Giant_Piranha:1385231440173858876>",
        "Nereid": "<:Nereid:1385232996520427571>", "Giant Crocodile": "<:Giant_Crocodile:1385231383496232981>",
        "Killer Robot": "<:Killer_Robot:1385232042173661287>", "Demon": "<:Demon:1385231209348595732>", "Harpy": "🦅",
        "Manticore": "<:Manticore:1385233266251927602>", "Dullahan": "<:Dullahan:1385231286032924722>",
        "Scaled Baby Dragon": "<:Scaled_baby_dragon:1385232813933989960>", "Baby Dragon": "🐉",
        "Young Dragon": "<:Young_dragon:1385232089154060398>",
        "Kid Dragon": "<:Kid_dragon:1385232021206601829>", "Scaled Kid Dragon": "🐲",
        "Not so Young Dragon": "<:Not_so_young_dragon:1385232953868681409>",
        "Teen Dragon": "<:Teen_dragon:1385232584132395059>", "Scaled Teen Dragon": "🐲",
        "Definitely Not Young Dragon": "<:Definetly_not_young_dragon:1385231194584776865>",
        "Adult Dragon": "<:Adult_dragon:1385230870981640202>", "Scaled Adult Dragon": "🐲",
        "Not Young at all Dragon": "<:Not_young_at_all_dragon:1385232936969699359>",
        "Old Dragon": "🐲", "Scaled Old Dragon": "<:Scaled_Old_Dragon:1385232795265405091>",
        "How do you dare call this Dragon \"young\"": "<:How_do_you_dare_call_this_dragon:1385231530158461019>",
        "Ancient Dragon": "<:Ancient_Dragon:1385230881840697476>", "Elder Dragon": "🐉", "Primordial Dragon": "🐲",
        "Cosmic Dragon": "🌌", "Void Dragon": "⚫", "Reality Dragon": "🌍",
        "Time Dragon": "⏰", "Space Dragon": "🌌", "Dimension Dragon": "🌀",
        "Omega Dragon": "💫", "Alpha Dragon": "⭐", "Genesis Dragon": "✨",
        "Final Dragon": "🔥", "Ultimate Dragon": "⚡", "Supreme Dragon": "👑",
        "Epic NPC": "🎮", "God of Games": "🎯", "The Creator": "✨",
        # Adventure-only monsters from Epic RPG wiki
        "Mutant Water Bottle": "<:Mutant_Water_Bottle:1385233103563522209>",
        "Giant Spider": "<:Giant_Spider:1385231462885757019>", "Bunch of Bees": "<:Bunch_of_bees:1385230980637528135>",
        "Ogre": "<:Ogre:1385232875191930910>", "Dark Knight": "<:Dark_Knight:1385231176083574814>",
        "Hyper Giant Bowl": "<:Hyper_Giant_bowl:1385231696584249464>",
        "Mutant Shoe": "<:Mutant_Shoe:1385233119832969387>", "Werewolf": "<:Werewolf:1385232210734485634>",
        "Centaur": "<:Centaur:1385231007166234735>",
        "Chimera": "<:Chimera:1385231021804617829>",
        "Hyper Giant Aeronautical Engine": "<:Hyper_Giant_Aeronautical_Engine:1385231569161031721>",
        "Golem": "<:Golem:1385231499342647386>",
        "Mammoth": "<:Mammoth:1385233279237754970>", "Mutant Esc Key": "<:Mutant_Esc_Key:1385233217283690586>",
        "Ent": "<:Ent:1385231301405315123>",
        "Dinosaur": "<:Dinosaur:1385231268890935428>", "Hyper Giant Door": "<:Hyper_Giant_Door:1385231730427957421>",
        "Cyclops": "<:Cyclops:1385231143531446302>",
        "Attack Helicopter": "<:Attack_Helicopter:1385230939076034622>",
        "Mutant Book": "<:Mutant_Book:1385233152775032934>", "Hydra": "<:Hydra:1385231549733011626>",
        "Kraken": "<:Kraken:1385232055574597764>", "Hyper Giant Chest": "<:Hyper_Giant_Chest:1385231714779140257>",
        "Leviathan": "<:Leviathan:1385233305066012744>",
        "War Tank": "<:War_Tank:1385232229390749797>", "Mutant Backpack": "<:Mutant_Backpack:1385233187105669170>",
        "Wyrm": "<:Wyrm:1385232124361052210>",
        "Hyper Giant Toilet": "<:Hyper_Giant_Toilet:1385231764468797462>", "Titan": "<:Titan:1385232413961228288>",
        "Typhon": "<:Typhon:1385232399100543016>",
        "Hyper Giant Dragon": "<:Hyper_giant_dragon:1385231748022931476>", "Even More Ancient Dragon": "🐲",
        "Ancientest Dragon": "<:Ancientest_Dragon:1385230898647007382>",
        "Another Mutant Dragon Like In Area 11 But Stronger": "<:Another_mutant_dragon_like_in_a1:1385230911313936404>",
        "Just Purple Dragon": "🟣",
        "Yes As You Expected Another Hyper Giant Dragon But Op Etc": "🐲",
        "I Have No More Ideas Dragon": "<:I_have_no_more_ideas_dragon:1385231829107347608>",
        "Mutantest Dragon": "<:Mutantest_dragon:1385233081425985658>"
    }

    if is_hardmode:
        # Hardmode: even stronger enemies, better rewards
        monster_hp = random.randint(120, 220) + (player["area"] * 30)
        monster_attack = random.randint(30, 60) + (player["area"] * 12)
        reward_multiplier = 2.0
        mode_text = "HARDMODE "
        elite_text = "ULTRA ELITE"
    else:
        # Normal mode
        monster_hp = random.randint(80, 150) + (player["area"] * 20)
        monster_attack = random.randint(20, 40) + (player["area"] * 8)
        reward_multiplier = 1.0
        mode_text = ""
        elite_text = "ELITE"

    # Player attack power
    weapon = WEAPONS.get(player["weapon"], {"attack": 5})
    player_attack = weapon["attack"] + random.randint(10, 25)

    # Calculate if player is too high level (no damage taken)
    level_advantage = player["level"] - area["level_req"]
    takes_no_damage = level_advantage >= 20  # If 20+ levels above area requirement

    # Always victory for simplicity - player always kills the monster
    base_exp = int((random.randint(50, 100) + (player["area"] * 10)) * reward_multiplier)
    coin_gain = int((random.randint(30, 60) + (player["area"] * 8)) * reward_multiplier)

    # Apply TT EXP bonus
    tt_bonuses = calculate_tt_bonuses(player.get("time_travels", 0))
    exp_multiplier = 1 + (tt_bonuses["exp"] / 100)
    exp_gain = int(base_exp * exp_multiplier)

    # Scale rewards for higher level players
    if player["level"] > 50:
        coin_gain *= (player["level"] // 8)
        exp_gain *= (player["level"] // 15 + 1)

    player["exp"] += exp_gain
    player["coins"] += coin_gain

    # Calculate damage taken
    damage_taken = 0
    if not takes_no_damage:
        # Calculate damage based on monster attack vs player defense
        base_damage = random.randint(25 if is_hardmode else 15, 45 if is_hardmode else 30)
        # Reduce damage if player is higher level
        damage_reduction = max(0, level_advantage * 0.1)  # 10% reduction per level advantage
        damage_taken = max(0, int(base_damage * (1 - damage_reduction)))

        player["hp"] -= damage_taken
        if player["hp"] < 0:
            player["hp"] = 0

    monster_emoji = monster_emojis.get(base_monster, "👹")

    # Format the message like the example
    result_message = f"**{ctx.author.display_name}** found and killed a {monster_emoji} **{mode_text}{elite_text} {base_monster.upper()}**\n"
    result_message += f"Earned **{coin_gain:,}** coins and **{exp_gain:,}** XP\n"
    result_message += f"Lost **{damage_taken}** HP, remaining HP is **{player['hp']}/{player['max_hp']}**"

    # Check for mob drops (adventures can also drop items)
    if base_monster in MOB_DROPS:
        drop_data = MOB_DROPS[base_monster]
        base_chance = 7  # 7% base adventure drop chance
        mob_chance = drop_data["chance"]
        tt_bonus = tt_bonuses["drops"] / 100  # Convert percentage to multiplier
        hardmode_bonus = 0.5 if is_hardmode else 0  # 50% better drop chance in hardmode
        total_chance = (base_chance + mob_chance) * (1 + tt_bonus + hardmode_bonus)

        if random.random() * 100 < total_chance:
            drop_item = drop_data["item"]
            if drop_item not in player["inventory"]:
                player["inventory"][drop_item] = 0
            player["inventory"][drop_item] += 1

            # Format drop message like the example (with emoji)
            drop_emoji = {
                "Wolf Skin": "🐺",
                "Zombie Eye": "👁️",
                "Unicorn Horn": "🦄",
                "Mermaid Hair": "🧜‍♀️",
                "Chip": "🤖",
                "Dragon Scale": "🐲"
            }.get(drop_item, "💎")

            result_message += f"\n**{ctx.author.display_name}** got **1** {drop_emoji} **{drop_item.lower()}**"

    # Check for Dark Energy (Areas 16-20)
    if 16 <= player["area"] <= 20:
        dark_chance = DARK_ENERGY_DROP["chance"] * (1 + tt_bonus + (0.5 if is_hardmode else 0))
        if random.random() * 100 < dark_chance:
            if "Dark Energy" not in player["inventory"]:
                player["inventory"]["Dark Energy"] = 0
            player["inventory"]["Dark Energy"] += 1
            result_message += f"\n**{ctx.author.display_name}** got **1** 🌌 **dark energy**"

    # Check level up
    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='fish')
async def fish(ctx):
    player = get_player(ctx.author.id)

    # Enhanced fishing with proper drop system
    drops_received = []
    area = player["area"]

    # Determine which drop table to use
    if area == 1:
        drop_table = FISHING_DROPS["area_1"]
    else:
        drop_table = FISHING_DROPS["area_2_plus"]

    # Roll for each fish type
    for fish_type, drop_data in drop_table.items():
        if random.random() * 100 < drop_data["chance"]:
            quantity = random.randint(drop_data["amount"][0], drop_data["amount"][1])
            if fish_type not in player["inventory"]:
                player["inventory"][fish_type] = 0
            player["inventory"][fish_type] += quantity

            # Add emojis for different fish types
            fish_emojis = {
                "Normie Fish": "🐟",
                "Golden Fish": "🐠",
                "EPIC Fish": "🌟",
                "SUPER Fish": "⭐"
            }
            emoji = fish_emojis.get(fish_type, "🐟")

            if fish_type in ["EPIC Fish", "SUPER Fish"]:
                drops_received.append(f"{emoji} **{fish_type}** x{quantity}")
            else:
                drops_received.append(f"{emoji} **{fish_type}** x{quantity}")

    base_exp = random.randint(8, 20)
    coin_gain = random.randint(5, 15)

    # Apply TT bonuses to working commands
    tt_bonuses = calculate_tt_bonuses(player.get("time_travels", 0))
    exp_multiplier = 1 + (tt_bonuses["exp"] / 100)
    exp_gain = int(base_exp * exp_multiplier)

    player["exp"] += exp_gain
    player["coins"] += coin_gain

    # Create beautiful result message
    actions = [
        "is fishing in the calm waters! Their line dances in the current",
        "casts their line with expert precision! The fish are biting today",
        "is patiently waiting by the water's edge! Something tugs at the line",
        "is fishing like a true master! The water ripples with activity"
    ]
    action = random.choice(actions)

    result_message = f"**{ctx.author.display_name}** {action}\n"

    if drops_received:
        result_message += f"**{ctx.author.display_name}** got {', '.join(drops_received)}\n"
    else:
        result_message += f"**{ctx.author.display_name}** didn't catch anything this time\n"

    result_message += f"Earned **{exp_gain:,}** XP and **{coin_gain:,}** coins"

    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='chop')
async def chop(ctx):
    player = get_player(ctx.author.id)

    # Enhanced chopping with proper drop system
    drops_received = []
    area = player["area"]

    # Roll for each possible log type
    for log_type, drop_data in CHOPPING_DROPS.items():
        chance = 0
        amount_range = [1, 1]

        # Determine chance and amount based on area
        if log_type == "Wooden Log":
            chance = drop_data["area_1"]["chance"]
            amount_range = drop_data["area_1"]["amount"]
        elif log_type == "Epic Log":
            if area == 1:
                chance = drop_data["area_1"]["chance"]
                amount_range = drop_data["area_1"]["amount"]
            else:
                chance = drop_data["area_2_plus"]["chance"]
                amount_range = drop_data["area_2_plus"]["amount"]
        elif log_type == "Super Log":
            if area >= 2:
                if area <= 3:
                    chance = drop_data["area_2_3"]["chance"]
                else:
                    chance = drop_data["area_4_plus"]["chance"]
                amount_range = drop_data["area_2_3"]["amount"]
        elif log_type == "Mega Log":
            if area >= 4:
                if area <= 5:
                    chance = drop_data["area_4_5"]["chance"]
                else:
                    chance = drop_data["area_6_plus"]["chance"]
                amount_range = drop_data["area_4_5"]["amount"]
        elif log_type == "HYPER Log":
            if area >= 6:
                if area <= 8:
                    chance = drop_data["area_6_8"]["chance"]
                else:
                    chance = drop_data["area_9_plus"]["chance"]
                amount_range = drop_data["area_6_8"]["amount"]
        elif log_type == "ULTRA Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]
                amount_range = drop_data["area_9_plus"]["amount"]
        elif log_type == "ULTIMATE Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]
                amount_range = drop_data["area_9_plus"]["amount"]

        # Roll for drop
        if chance > 0 and random.random() * 100 < chance:
            quantity = random.randint(amount_range[0], amount_range[1])
            if log_type not in player["inventory"]:
                player["inventory"][log_type] = 0
            player["inventory"][log_type] += quantity

            # Add emojis for different log types
            log_emojis = {
                "Wooden Log": "🪵",
                "Epic Log": "📜",
                "Super Log": "🟫",
                "Mega Log": "🟤",
                "HYPER Log": "🟨",
                "ULTRA Log": "🟪",
                "ULTIMATE Log": "⭐"
            }
            emoji = log_emojis.get(log_type, "🪵")
            drops_received.append(f"{emoji} **{log_type}** x{quantity}")

    exp_gain = random.randint(10, 25)
    player["exp"] += exp_gain

    # Create beautiful result message
    actions = [
        "is chopping with their **AXE**! The sound of wood echoes through the forest",
        "swings their **AXE** with precision! Wood chips fly everywhere",
        "is working hard in the forest! Their axe gleams in the sunlight",
        "chops wood like a true lumberjack! The trees don't stand a chance"
    ]
    action = random.choice(actions)

    result_message = f"**{ctx.author.display_name}** {action}\n"

    if drops_received:
        result_message += f"**{ctx.author.display_name}** got {', '.join(drops_received)}\n"
    else:
        result_message += f"**{ctx.author.display_name}** didn't find any usable wood this time\n"

    result_message += f"Earned **{exp_gain:,}** XP"

    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='cooldowns', aliases=['cooldown', 'cd', 'cds'])
async def cooldowns(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author

    player = get_player(user.id)

    import time
    current_time = time.time()

    embed = discord.Embed(title=f"⏰ {user.display_name}'s Cooldowns", color=0x9932cc)

    cooldowns_text = ""

    # Hunt cooldown
    hunt_cd = player.get("last_hunt", 0) + 10 - current_time
    if hunt_cd > 0:
        cooldowns_text += f"Hunt: {int(hunt_cd)}s\n"
    else:
        cooldowns_text += "Hunt: Ready ✅\n"

    # Adventure cooldown
    adv_cd = player.get("last_adventure", 0) + 60 - current_time
    if adv_cd > 0:
        cooldowns_text += f"Adventure: {int(adv_cd)}s\n"
    else:
        cooldowns_text += "Adventure: Ready ✅\n"

    embed.add_field(name="Cooldowns", value=cooldowns_text, inline=False)
    await ctx.send(embed=embed)


@bot.command(name='ready', aliases=['rd'])
async def ready(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author

    player = get_player(user.id)

    import time
    current_time = time.time()

    embed = discord.Embed(title=f"✅ {user.display_name}'s Ready Commands", color=0x00ff00)

    ready_text = ""

    # Hunt cooldown
    hunt_cd = player.get("last_hunt", 0) + 10 - current_time
    if hunt_cd <= 0:
        ready_text += "Hunt ✅\n"

    # Adventure cooldown
    adv_cd = player.get("last_adventure", 0) + 60 - current_time
    if adv_cd <= 0:
        ready_text += "Adventure ✅\n"

    if not ready_text:
        ready_text = "No commands ready"

    embed.add_field(name="Ready Commands", value=ready_text, inline=False)
    await ctx.send(embed=embed)


@bot.command(name='daily')
async def daily(ctx):
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    import time
    from datetime import datetime, timedelta

    current_time = time.time()
    last_daily = player.get("last_daily", 0)

    # Check if 24 hours have passed
    if current_time - last_daily < 86400:  # 24 hours in seconds
        time_left = 86400 - (current_time - last_daily)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await ctx.send(f"You already claimed your daily reward! Come back in {hours}h {minutes}m")
        return

    # Calculate streak
    if current_time - last_daily <= 172800:  # Less than 48 hours
        player["daily_streak"] = player.get("daily_streak", 0) + 1
    else:
        player["daily_streak"] = 1

    player["last_daily"] = current_time

    # Calculate rewards based on streak
    base_coins = 100
    streak_bonus = min(player["daily_streak"] * 20, 500)  # Max 500 bonus
    total_coins = base_coins + streak_bonus

    # Calculate life potions based on max area reached
    max_area_reached = player.get("max_area_reached", player["area"])
    if player["area"] > max_area_reached:
        player["max_area_reached"] = player["area"]
        max_area_reached = player["area"]

    life_potions = min(max_area_reached // 3 + 1, 10)  # 1-10 life potions based on max area

    player["coins"] += total_coins
    player["hp"] = player["max_hp"]  # Full heal

    # Add life potions
    if "life potion" not in player["inventory"]:
        player["inventory"]["life potion"] = 0
    player["inventory"]["life potion"] += life_potions

    embed = discord.Embed(title="🎁 Daily Reward", color=0xffd700)
    embed.add_field(name="Streak", value=f"Day {player['daily_streak']}", inline=True)
    embed.add_field(name="Coins Earned", value=total_coins, inline=True)
    embed.add_field(name="Life Potions", value=f"+{life_potions}", inline=True)
    embed.add_field(name="HP", value="Fully healed!", inline=True)

    if player["daily_streak"] >= 7:
        embed.add_field(name="Streak Bonus!", value="🎊 Epic streak reward!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='sell')
async def sell(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to sell!")
        return

    player = get_player(ctx.author.id)

    # Find item in inventory
    item_found = None
    for item in player["inventory"]:
        if item.lower() == item_name.lower():
            item_found = item
            break

    if not item_found or player["inventory"][item_found] <= 0:
        await ctx.send("You don't have this item!")
        return

    # Calculate sell price (basic formula)
    sell_price = random.randint(5, 20)
    if item_found in WEAPONS:
        sell_price = WEAPONS[item_found]["attack"] * 5

    player["inventory"][item_found] -= 1
    if player["inventory"][item_found] <= 0:
        del player["inventory"][item_found]

    player["coins"] += sell_price

    embed = discord.Embed(title="💰 Item Sold", color=0x00ff00)
    embed.add_field(name="Item", value=item_found, inline=True)
    embed.add_field(name="Price", value=f"{sell_price} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='craft')
async def craft_item(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to craft! Use `rpg recipes` to see available items.")
        return

    player = get_player(ctx.author.id)

    # Find recipe
    recipe = None
    recipe_name = None
    for name, data in CRAFT_RECIPES.items():
        if name.lower() == item_name.lower():
            recipe = data
            recipe_name = name
            break

    if not recipe:
        await ctx.send("Recipe not found! Use `rpg recipes` to see available items.")
        return

    # Check requirements
    if player["level"] < recipe["level_req"]:
        await ctx.send(f"You need level {recipe['level_req']} to craft {recipe_name}!")
        return

    # Check if player has equipment equipped (can't craft while equipped)
    if recipe["type"] == "weapon" and player["weapon"] == recipe_name:
        await ctx.send("You cannot craft equipment you currently have equipped!")
        return
    if recipe["type"] == "armor" and player["armor"] == recipe_name:
        await ctx.send("You cannot craft equipment you currently have equipped!")
        return

    # Check materials
    missing_materials = []
    for material, needed in recipe["materials"].items():
        if player["inventory"].get(material, 0) < needed:
            missing_materials.append(f"{material}: {needed - player['inventory'].get(material, 0)}")

    # Check coin cost if any
    if "coin_cost" in recipe and player["coins"] < recipe["coin_cost"]:
        missing_materials.append(f"Coins: {recipe['coin_cost'] - player['coins']}")

    if missing_materials:
        await ctx.send(f"Missing materials: {', '.join(missing_materials)}")
        return

    # Consume materials
    for material, needed in recipe["materials"].items():
        player["inventory"][material] -= needed
        if player["inventory"][material] <= 0:
            del player["inventory"][material]

    if "coin_cost" in recipe:
        player["coins"] -= recipe["coin_cost"]

    # Add crafted item
    if recipe_name not in player["inventory"]:
        player["inventory"][recipe_name] = 0
    player["inventory"][recipe_name] += 1

    # Crafter profession bonus (chance to get materials back)
    crafter_level = player["job_levels"]["crafter"]
    return_chance = min(12.25 + (2.25 * max(0, crafter_level - 100) ** 0.2), 50)

    if random.random() * 100 < return_chance:
        returned_materials = []
        for material, needed in recipe["materials"].items():
            return_amount = max(1, int(needed * 0.1225))
            if material not in player["inventory"]:
                player["inventory"][material] = 0
            player["inventory"][material] += return_amount
            returned_materials.append(f"{material}: {return_amount}")

        embed = discord.Embed(title="🔨 Crafting Success!", color=0x00ff00)
        embed.add_field(name="Crafted", value=recipe_name, inline=True)
        embed.add_field(name="Stats", value=f"ATK: {recipe['attack']} | DEF: {recipe['defense']}", inline=True)
        embed.add_field(name="Crafter Bonus!", value=f"Returned: {', '.join(returned_materials)}", inline=False)
    else:
        embed = discord.Embed(title="🔨 Crafting Success!", color=0x00ff00)
        embed.add_field(name="Crafted", value=recipe_name, inline=True)
        embed.add_field(name="Stats", value=f"ATK: {recipe['attack']} | DEF: {recipe['defense']}", inline=True)

    # Level up crafter profession
    player["job_levels"]["crafter"] += random.randint(1, 3)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='forge')
async def forge_item(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to forge! Use `rpg recipes forge` to see available items.")
        return

    player = get_player(ctx.author.id)

    if player["area"] < 11:
        await ctx.send("Forging is unlocked in Area 11!")
        return

    # Find forge recipe
    recipe = None
    recipe_name = None
    for name, data in FORGE_RECIPES.items():
        if name.lower() == item_name.lower():
            recipe = data
            recipe_name = name
            break

    if not recipe:
        await ctx.send("Forge recipe not found! Use `rpg recipes forge` to see available items.")
        return

    # Check requirements
    if player["level"] < recipe["level_req"]:
        await ctx.send(f"You need level {recipe['level_req']} to forge {recipe_name}!")
        return

    if player["area"] < recipe["area_req"]:
        await ctx.send(f"You need to reach Area {recipe['area_req']} to forge {recipe_name}!")
        return

    if "hp_req" in recipe and player["max_hp"] < recipe["hp_req"]:
        await ctx.send(f"You need {recipe['hp_req']} HP to forge {recipe_name}!")
        return

    # Check materials
    missing_materials = []
    for material, needed in recipe["materials"].items():
        if player["inventory"].get(material, 0) < needed:
            missing_materials.append(f"{material}: {needed - player['inventory'].get(material, 0)}")

    if missing_materials:
        await ctx.send(f"Missing materials: {', '.join(missing_materials)}")
        return

    # Consume materials
    for material, needed in recipe["materials"].items():
        player["inventory"][material] -= needed
        if player["inventory"][material] <= 0:
            del player["inventory"][material]

    # Add forged item
    if recipe_name not in player["inventory"]:
        player["inventory"][recipe_name] = 0
    player["inventory"][recipe_name] += 1

    embed = discord.Embed(title="⚒️ Forging Success!", color=0xff6600)
    embed.add_field(name="Forged", value=recipe_name, inline=True)
    embed.add_field(name="Stats", value=f"ATK: {recipe['attack']} | DEF: {recipe['defense']}", inline=True)
    embed.add_field(name="Note", value="Enchants are preserved during forging!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='voidforge')
async def void_forge_item(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to void forge!")
        return

    player = get_player(ctx.author.id)

    if player["area"] < 21:
        await ctx.send("Void forging is only available in THE TOP area!")
        return

    # Find void forge recipe
    recipe = None
    recipe_name = None
    for name, data in VOID_FORGE_RECIPES.items():
        if name.lower() == item_name.lower():
            recipe = data
            recipe_name = name
            break

    if not recipe:
        await ctx.send("Void forge recipe not found!")
        return

    # Check requirements
    if player["area"] < recipe["area_req"]:
        await ctx.send(f"You need to reach Area {recipe['area_req']} to void forge {recipe_name}!")
        return

    if "time_travel_req" in recipe and player["time_travels"] < recipe["time_travel_req"]:
        await ctx.send(f"You need {recipe['time_travel_req']} Time Travels to forge {recipe_name}!")
        return

    # Check materials and coin cost
    missing_materials = []
    for material, needed in recipe["materials"].items():
        if player["inventory"].get(material, 0) < needed:
            missing_materials.append(f"{material}: {needed - player['inventory'].get(material, 0)}")

    if "coin_cost" in recipe and player["coins"] < recipe["coin_cost"]:
        missing_materials.append(f"Coins: {recipe['coin_cost'] - player['coins']}")

    if missing_materials:
        await ctx.send(f"Missing materials: {', '.join(missing_materials)}")
        return

    # Consume materials
    for material, needed in recipe["materials"].items():
        player["inventory"][material] -= needed
        if player["inventory"][material] <= 0:
            del player["inventory"][material]

    if "coin_cost" in recipe:
        player["coins"] -= recipe["coin_cost"]

    # Add void forged item
    if recipe_name not in player["inventory"]:
        player["inventory"][recipe_name] = 0
    player["inventory"][recipe_name] += 1

    embed = discord.Embed(title="🌌 Void Forging Success!", color=0x4b0082)
    embed.add_field(name="Void Forged", value=recipe_name, inline=True)
    embed.add_field(name="Stats", value=f"ATK: {recipe['attack']} | DEF: {recipe['defense']}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='dismantle')
async def dismantle_item(ctx, item_name=None, amount=1):
    if not item_name:
        await ctx.send("Please specify an item to dismantle!")
        return

    player = get_player(ctx.author.id)

    try:
        amount = int(amount)
    except:
        amount = 1

    # Find material conversion
    conversion = None
    for material, data in MATERIAL_CONVERSION.items():
        if material.lower() == item_name.lower():
            conversion = data
            item_name = material
            break

    if not conversion:
        await ctx.send("This item cannot be dismantled!")
        return

    if player["inventory"].get(item_name, 0) < amount:
        await ctx.send(f"You don't have {amount} {item_name}!")
        return

    # Dismantle
    player["inventory"][item_name] -= amount
    if player["inventory"][item_name] <= 0:
        del player["inventory"][item_name]

    base_material = conversion["base"]
    returned_amount = conversion["return"] * amount

    if base_material not in player["inventory"]:
        player["inventory"][base_material] = 0
    player["inventory"][base_material] += returned_amount

    embed = discord.Embed(title="🔧 Dismantling Complete", color=0x8b4513)
    embed.add_field(name="Dismantled", value=f"{item_name} x{amount}", inline=True)
    embed.add_field(name="Received", value=f"{base_material} x{returned_amount}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='cook')
async def cook_item(ctx, *, item_name=None):
    if not item_name:
        await ctx.send("Please specify an item to cook! Use `rpg recipes cook` to see recipes.")
        return

    player = get_player(ctx.author.id)

    # Find cooking recipe
    recipe = None
    recipe_name = None
    for name, data in COOKING_RECIPES.items():
        if name.lower() == item_name.lower():
            recipe = data
            recipe_name = name
            break

    if not recipe:
        await ctx.send("Cooking recipe not found!")
        return

    # Check materials
    missing_materials = []
    for material, needed in recipe["materials"].items():
        if player["inventory"].get(material, 0) < needed:
            missing_materials.append(f"{material}: {needed - player['inventory'].get(material, 0)}")

    if missing_materials:
        await ctx.send(f"Missing ingredients: {', '.join(missing_materials)}")
        return

    # Consume materials
    for material, needed in recipe["materials"].items():
        player["inventory"][material] -= needed
        if player["inventory"][material] <= 0:
            del player["inventory"][material]

    # Apply cooking boost
    boost_type = recipe["effect"]
    boost_amount = recipe["boost"]
    player["cooking_boosts"][boost_type] += boost_amount

    embed = discord.Embed(title="🍳 Cooking Success!", color=0xffa500)
    embed.add_field(name="Cooked", value=recipe_name, inline=True)
    embed.add_field(name="Effect", value=recipe["description"], inline=True)
    embed.add_field(name="Note", value="Boost applied permanently until Time Travel!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='recipes')
async def recipes(ctx, category=None):
    if category == "forge":
        embed = discord.Embed(title="⚒️ Forge Recipes (Area 11+)", color=0xff6600)
        recipe_text = ""
        for name, data in list(FORGE_RECIPES.items())[:10]:  # Show first 10
            materials = ", ".join([f"{mat}: {amt}" for mat, amt in data["materials"].items()])
            recipe_text += f"**{name}** (Lvl {data['level_req']}, Area {data['area_req']})\n"
            recipe_text += f"ATK: {data['attack']} | DEF: {data['defense']}\n"
            recipe_text += f"Materials: {materials}\n\n"
        embed.add_field(name="Available Recipes", value=recipe_text[:1024], inline=False)

    elif category == "void":
        embed = discord.Embed(title="🌌 Void Forge Recipes (THE TOP)", color=0x4b0082)
        recipe_text = ""
        for name, data in list(VOID_FORGE_RECIPES.items())[:8]:
            materials = ", ".join([f"{mat}: {amt}" for mat, amt in data["materials"].items()])
            recipe_text += f"**{name}** (Area {data['area_req']})\n"
            recipe_text += f"ATK: {data['attack']} | DEF: {data['defense']}\n"
            recipe_text += f"Materials: {materials}\n\n"
        embed.add_field(name="Available Recipes", value=recipe_text[:1024], inline=False)

    elif category == "cook":
        embed = discord.Embed(title="🍳 Cooking Recipes", color=0xffa500)
        recipe_text = ""
        for name, data in COOKING_RECIPES.items():
            materials = ", ".join([f"{mat}: {amt}" for mat, amt in data["materials"].items()])
            recipe_text += f"**{name}**\n"
            recipe_text += f"Effect: {data['description']}\n"
            recipe_text += f"Ingredients: {materials}\n\n"
        embed.add_field(name="Available Recipes", value=recipe_text, inline=False)

    else:
        embed = discord.Embed(title="🔨 Basic Craft Recipes", color=0x00ff00)
        recipe_text = ""
        for name, data in list(CRAFT_RECIPES.items())[:12]:  # Show first 12
            materials = ", ".join([f"{mat}: {amt}" for mat, amt in data["materials"].items()])
            recipe_text += f"**{name}** (Lvl {data['level_req']})\n"
            recipe_text += f"ATK: {data['attack']} | DEF: {data['defense']}\n"
            recipe_text += f"Materials: {materials}\n\n"
        embed.add_field(name="Available Recipes", value=recipe_text[:1024], inline=False)
        embed.add_field(name="Other Categories",
                        value="`rpg recipes forge` - Forge recipes\n`rpg recipes void` - Void forge recipes\n`rpg recipes cook` - Cooking recipes",
                        inline=False)

    await ctx.send(embed=embed)


@bot.command(name='enchant')
async def enchant(ctx, *, item_name=None):
    player = get_player(ctx.author.id)

    max_area = player.get("max_area_reached", player["area"])
    if not check_command_unlocked(player["area"], "enchant", max_area):
        await ctx.send("🔒 Enchanting is unlocked in Area 2!")
        return

    if not item_name:
        await ctx.send("Please specify an item to enchant! Example: `rpg enchant Wooden Sword`")
        return

    # Find item in inventory
    item_found = None
    for item in player["inventory"]:
        if item.lower() == item_name.lower():
            item_found = item
            break

    if not item_found or player["inventory"][item_found] <= 0:
        await ctx.send("You don't have this item!")
        return

    # Check if item is a weapon or armor
    is_weapon = item_found in WEAPONS or any(
        item_found == name for name in CRAFT_RECIPES if CRAFT_RECIPES[name]["type"] == "weapon")
    is_armor = any(item_found == name for name in CRAFT_RECIPES if CRAFT_RECIPES[name]["type"] == "armor")

    if not (is_weapon or is_armor):
        await ctx.send("You can only enchant weapons and armor!")
        return

    enchant_cost = player["level"] * 100
    if player["coins"] < enchant_cost:
        await ctx.send(f"You need {enchant_cost} coins to enchant this item!")
        return

    player["coins"] -= enchant_cost

    # Apply enchantment
    if item_found not in player["enchants"]:
        player["enchants"][item_found] = {"attack": 0, "defense": 0}

    if is_weapon:
        enchant_bonus = random.randint(1, 5) + (player["area"] // 2)
        player["enchants"][item_found]["attack"] += enchant_bonus
        embed = discord.Embed(title="✨ Enchantment Success!", color=0x9932cc)
        embed.add_field(name="Item", value=item_found, inline=True)
        embed.add_field(name="Attack Bonus", value=f"+{enchant_bonus}", inline=True)
    else:
        enchant_bonus = random.randint(1, 5) + (player["area"] // 2)
        player["enchants"][item_found]["defense"] += enchant_bonus
        embed = discord.Embed(title="✨ Enchantment Success!", color=0x9932cc)
        embed.add_field(name="Item", value=item_found, inline=True)
        embed.add_field(name="Defense Bonus", value=f"+{enchant_bonus}", inline=True)

    embed.add_field(name="Cost", value=f"{enchant_cost} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='training')
async def training(ctx):
    player = get_player(ctx.author.id)

    max_area = player.get("max_area_reached", player["area"])
    if not check_command_unlocked(player["area"], "training", max_area):
        await ctx.send("🔒 Training is unlocked in Area 2!")
        return

    training_cost = 500
    if player["coins"] < training_cost:
        await ctx.send(f"You need {training_cost} coins for training!")
        return

    player["coins"] -= training_cost

    # Training gives stats boost
    hp_gain = random.randint(10, 30)
    player["max_hp"] += hp_gain
    player["hp"] = player["max_hp"]

    embed = discord.Embed(title="💪 Training Complete!", color=0xff6600)
    embed.add_field(name="HP Increase", value=f"+{hp_gain}", inline=True)
    embed.add_field(name="Cost", value=f"{training_cost} coins", inline=True)
    embed.add_field(name="New Max HP", value=player["max_hp"], inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='axe')
async def axe(ctx):
    player = get_player(ctx.author.id)

    max_area = player.get("max_area_reached", player["area"])
    if not check_command_unlocked(player["area"], "axe", max_area):
        await ctx.send("🔒 Axe is unlocked in Area 3!")
        return

    # Enhanced chopping with axe - better amounts
    drops_received = []
    area = player["area"]

    # Axe amounts: Wooden Log 3-6, Epic Log 2-3, Super Log 2, others same as chop
    axe_multipliers = {
        "Wooden Log": [3, 6],
        "Epic Log": [2, 3],
        "Super Log": [2, 2],
        "Mega Log": [1, 1],
        "HYPER Log": [1, 1],
        "ULTRA Log": [1, 1],
        "ULTIMATE Log": [1, 1]
    }

    # Roll for each possible log type with axe bonuses
    for log_type, drop_data in CHOPPING_DROPS.items():
        chance = 0

        # Determine chance based on area (same as chop)
        if log_type == "Wooden Log":
            chance = drop_data["area_1"]["chance"]
        elif log_type == "Epic Log":
            if area == 1:
                chance = drop_data["area_1"]["chance"]
            else:
                chance = drop_data["area_2_plus"]["chance"]
        elif log_type == "Super Log":
            if area >= 2:
                if area <= 3:
                    chance = drop_data["area_2_3"]["chance"]
                else:
                    chance = drop_data["area_4_plus"]["chance"]
        elif log_type == "Mega Log":
            if area >= 4:
                if area <= 5:
                    chance = drop_data["area_4_5"]["chance"]
                else:
                    chance = drop_data["area_6_plus"]["chance"]
        elif log_type == "HYPER Log":
            if area >= 6:
                if area <= 8:
                    chance = drop_data["area_6_8"]["chance"]
                else:
                    chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTRA Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTIMATE Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]

        # Roll for drop with axe amounts
        if chance > 0 and random.random() * 100 < chance:
            amount_range = axe_multipliers.get(log_type, [1, 1])
            quantity = random.randint(amount_range[0], amount_range[1])
            if log_type not in player["inventory"]:
                player["inventory"][log_type] = 0
            player["inventory"][log_type] += quantity
            drops_received.append(f"{log_type} x{quantity}")

    exp_gain = random.randint(15, 35)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🪓 Axe Chopping Result", color=0x8b4513)

    if drops_received:
        embed.add_field(name="Chopped", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No logs obtained this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Axe gives more materials!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='net')
async def net(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "net"):
        await ctx.send("🔒 Net is unlocked in Area 3!")
        return

    # Enhanced fishing with net - better amounts and chances
    drops_received = []
    area = player["area"]

    # Net amounts: Normie Fish 3-7, Golden Fish 2-4, others 1
    net_amounts = {
        "Normie Fish": [3, 7],
        "Golden Fish": [2, 4],
        "EPIC Fish": [1, 1],
        "SUPER Fish": [1, 1]
    }

    # Net has slightly better EPIC Fish chances
    if area == 1:
        drop_table = FISHING_DROPS["area_1"]
    else:
        # Modified chances for net
        drop_table = {
            "Normie Fish": {"chance": 72, "amount": [3, 7]},
            "Golden Fish": {"chance": 27.4, "amount": [2, 4]},
            "EPIC Fish": {"chance": 0.6, "amount": [1, 1]},
            "SUPER Fish": {"chance": 0.02, "amount": [1, 1]}
        }

    # Roll for each fish type
    for fish_type, drop_data in drop_table.items():
        if random.random() * 100 < drop_data["chance"]:
            amount_range = net_amounts.get(fish_type, drop_data["amount"])
            quantity = random.randint(amount_range[0], amount_range[1])
            if fish_type not in player["inventory"]:
                player["inventory"][fish_type] = 0
            player["inventory"][fish_type] += quantity

            # Mark rare fish
            if fish_type in ["EPIC Fish", "SUPER Fish"]:
                drops_received.append(f"🌟 {fish_type} x{quantity}")
            else:
                drops_received.append(f"{fish_type} x{quantity}")

    exp_gain = random.randint(12, 30)
    coin_gain = random.randint(8, 25)
    player["exp"] += exp_gain
    player["coins"] += coin_gain

    embed = discord.Embed(title="🕸️ Net Fishing Result", color=0x4169e1)

    if drops_received:
        embed.add_field(name="Caught", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="Nothing caught this time", inline=True)

    embed.add_field(name="Rewards", value=f"EXP: +{exp_gain}\nCoins: +{coin_gain}", inline=True)
    embed.add_field(name="Bonus", value="Net catches more fish!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='help', aliases=['helps'])
async def help_command(ctx, category=None):
    """Beautiful comprehensive help system with categories"""
    player = get_player(ctx.author.id)

    if player is None:
        embed = discord.Embed(
            title="🎮 Welcome to disRPG!",
            description="**The Ultimate Discord RPG Experience**\n\nEmbark on an epic adventure through 21 areas, battle mighty dragons, craft legendary equipment, and become the ultimate hero!",
            color=0x00ff88
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/1234567890123456789.png")  # You can replace with actual emoji URL
        embed.add_field(
            name="🚀 **Get Started**",
            value="```\nrpgs start  or  /start\n```\nCreate your adventure account and begin your journey!",
            inline=False
        )
        embed.add_field(
            name="💡 **Need Help?**",
            value="Use `rpgs help` after creating your account to see all available commands!",
            inline=False
        )
        embed.set_footer(text="✨ Your adventure awaits! ✨")
        await ctx.send(embed=embed)
        return

    # Main help menu
    if category is None:
        embed = discord.Embed(
            title="⚔️ disRPG Command Center",
            description=f"**Welcome back, {ctx.author.display_name}!**\n\nChoose a category below to explore commands\n\n🔹 Prefix: `rpgs` or `/` (slash commands)\n🔹 Your Area: **{player['area']}** - {AREAS[player['area']]['name']}\n🔹 Level: **{player['level']}**",
            color=0x7289da
        )
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        categories = [
            ("🏅", "**Progress**", "`rpgs help progress`", "Stats, inventory, profile, leaderboards"),
            ("⚔️", "**Combat**", "`rpgs help combat`", "Hunt, adventure, dungeons, healing"),
            ("💰", "**Economy**", "`rpgs help economy`", "Shop, trading, lootboxes, buying"),
            ("🔧", "**Working**", "`rpgs help working`", "Fishing, chopping, mining, farming"),
            ("🎲", "**Gambling**", "`rpgs help gambling`", "Blackjack, slots, dice games"),
            ("🏰", "**Guild**", "`rpgs help guild`", "Guild management, raids, shop"),
            ("⏰", "**Advanced**", "`rpgs help advanced`", "Time travel, forging, enchanting"),
            ("🎁", "**Rewards**", "`rpgs help rewards`", "Daily rewards, achievements, bonuses")
        ]

        for emoji, name, command, desc in categories:
            embed.add_field(
                name=f"{emoji} {name}",
                value=f"**{command}**\n*{desc}*",
                inline=True
            )

        # Show unlocked commands for current area
        unlocked_commands = get_unlocked_commands(player["area"])
        if unlocked_commands:
            embed.add_field(
                name="🔓 **Your Unlocked Commands**",
                value=f"```\n{', '.join(unlocked_commands[:8])}\n```",
                inline=False
            )

        # Show next area unlock
        if player["area"] + 1 in AREA_UNLOCKS:
            next_unlocks = AREA_UNLOCKS[player["area"] + 1]
            embed.add_field(
                name=f"🔒 **Next Unlock (Area {player['area'] + 1})**",
                value=f"```\n{', '.join(next_unlocks)}\n```",
                inline=False
            )

        embed.set_footer(text="💡 Use 'rpgs help <category>' for detailed command lists | Example: rpgs help combat")
        await ctx.send(embed=embed)
        return

    # Category-specific help
    category = category.lower()

    if category in ['progress', 'prog', 'stats']:
        embed = discord.Embed(
            title="📊 Progress Commands",
            description="Track your character's growth and achievements",
            color=0xffd700
        )
        commands = [
            ("👤 **profile** `[user]`", "View detailed character profile"),
            ("📊 **stats**", "Quick view of your character stats"),
            ("🎒 **inventory**", "View your items and materials"),
            ("🏆 **leaderboard** `[type]`", "View top players (level, coins, tt)"),
            ("🔥 **cooldowns**", "Check command cooldowns"),
            ("✅ **ready**", "See which commands are ready"),
            ("🎯 **title** `[action]`", "Manage your titles"),
            ("🗺️ **area** `[move] [number]`", "View or change areas"),
        ]

    elif category in ['combat', 'fight', 'battle']:
        embed = discord.Embed(
            title="⚔️ Combat Commands",
            description="Battle monsters and become stronger!",
            color=0xff4444
        )
        commands = [
            ("🗡️ **hunt** `[hardmode]`", "Fight monsters in your area"),
            ("🗺️ **adventure** `[hardmode]`", "Challenging adventures for better rewards"),
            ("🏰 **dungeon** `[number]`", "Fight powerful dragon bosses"),
            ("💊 **heal**", "Restore your health"),
            ("⚔️ **duel** `<user> <bet>`", "Challenge other players"),
            ("🏟️ **arena**", "Compete in arena battles"),
            ("👹 **miniboss**", "Face mini-boss challenges"),
        ]

    elif category in ['economy', 'eco', 'money']:
        embed = discord.Embed(
            title="💰 Economy Commands",
            description="Manage your wealth and resources",
            color=0x00ff00
        )
        commands = [
            ("🏪 **shop** `[page]`", "Browse items for sale"),
            ("⭐ **epicshop** `[category]`", "Premium Epic Coin shop"),
            ("💳 **buy** `<item> [amount]`", "Purchase items"),
            ("💸 **sell** `<item> [amount]`", "Sell your items"),
            ("🎁 **lootbox** `[type]`", "View available lootboxes"),
            ("📦 **open** `<lootbox> [amount]`", "Open lootboxes for rewards"),
            ("🔄 **trade** `[id] [amount]`", "Trade resources"),
            ("💊 **use** `<item>`", "Use consumable items"),
        ]

    elif category in ['working', 'work', 'jobs']:
        embed = discord.Embed(
            title="🔧 Working Commands",
            description="Gather resources and materials",
            color=0x8b4513
        )
        commands = [
            ("🎣 **fish**", "Catch fish and sea creatures"),
            ("🪚 **net**", "Fish with net (better rates)"),
            ("⛵ **boat**", "Fish with boat (even better)"),
            ("🚢 **bigboat**", "Fish with big boat (best rates)"),
            ("🪓 **chop**", "Chop wood for logs"),
            ("🪚 **axe**", "Chop with axe (more logs)"),
            ("🪚 **bowsaw**", "Chop with bowsaw (even more)"),
            ("⛏️ **mine**", "Mine for coins and rubies"),
            ("⛏️ **pickaxe**", "Mine with pickaxe (better rates)"),
            ("🔩 **drill**", "Mine with drill (even better)"),
            ("🌱 **farm**", "Plant seeds for crops"),
            ("🍎 **pickup**", "Gather fruits"),
        ]

    elif category in ['gambling', 'gamble', 'games']:
        embed = discord.Embed(
            title="🎲 Gambling Commands",
            description="Test your luck and win big!",
            color=0x9932cc
        )
        commands = [
            ("🃏 **blackjack** `<bet>`", "Classic card game"),
            ("🪙 **coinflip** `<h/t> <bet>`", "Heads or tails"),
            ("🎰 **slots** `<bet>`", "Spin the slot machine"),
            ("🎲 **multidice** `<user> <bet>`", "Dice duel with another player"),
            ("🎡 **wheel** `<bet>`", "Spin the wheel of fortune"),
            ("🎲 **bigdice** `<bet>`", "High stakes dice game"),
        ]

    elif category in ['guild', 'guilds']:
        embed = discord.Embed(
            title="🏰 Guild Commands",
            description="Join forces with other players!",
            color=0x9932cc
        )
        commands = [
            ("🏰 **guild**", "View your guild info"),
            ("🆕 **guild create** `<name>`", "Create a new guild"),
            ("👥 **guild invite** `<user>`", "Invite a player"),
            ("🚪 **guild leave**", "Leave your guild"),
            ("👢 **guild kick** `<user>`", "Kick a member (owner only)"),
            ("⚔️ **guild raid**", "Raid other guilds"),
            ("🔧 **guild upgrade**", "Upgrade guild stealth"),
            ("🏪 **guild shop**", "Browse guild shop"),
            ("💍 **guild buy** `<item>`", "Buy from guild shop"),
            ("📋 **guild list**", "List all guilds"),
        ]

    elif category in ['advanced', 'adv', 'special']:
        embed = discord.Embed(
            title="⏰ Advanced Commands",
            description="Master the most powerful features",
            color=0x4b0082
        )
        commands = [
            ("⏰ **timetravel**", "Reset with permanent bonuses"),
            ("🌌 **supertimetravel**", "Ultimate reset with special rewards"),
            ("🔨 **craft** `<item>`", "Craft weapons and armor"),
            ("⚒️ **forge** `<item>`", "Forge powerful equipment"),
            ("🌌 **voidforge** `<item>`", "Create ultimate gear"),
            ("✨ **enchant** `<item>`", "Enchant your equipment"),
            ("🍳 **cook** `<item>`", "Cook food for bonuses"),
            ("🔧 **dismantle** `<item>`", "Break down materials"),
            ("📜 **recipes** `[category]`", "View crafting recipes"),
        ]

    elif category in ['rewards', 'reward', 'daily']:
        embed = discord.Embed(
            title="🎁 Rewards Commands",
            description="Claim your daily bonuses and achievements",
            color=0xffa500
        )
        commands = [
            ("📅 **daily**", "Claim daily rewards"),
            ("📊 **weekly**", "Weekly guild challenges"),
            ("🗳️ **vote**", "Vote for the bot and get rewards"),
            ("🏆 **achievements**", "View your achievements"),
            ("💎 **code** `<code>`", "Redeem special codes"),
            ("💝 **donate**", "Support the bot development"),
            ("🔍 **drops** `[category]`", "View drop information"),
        ]

    else:
        embed = discord.Embed(
            title="❌ Unknown Category",
            description=f"Category `{category}` not found!",
            color=0xff0000
        )
        embed.add_field(
            name="Available Categories",
            value="progress, combat, economy, working, gambling, guild, advanced, rewards",
            inline=False
        )
        await ctx.send(embed=embed)
        return

    # Add commands to embed
    for i, (name, desc) in enumerate(commands):
        embed.add_field(name=name, value=desc, inline=True)
        if (i + 1) % 2 == 0:  # Add spacing every 2 commands
            embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.set_footer(text=f"💡 Use 'rpgs help' to return to main menu | Your current area: {player['area']}")
    await ctx.send(embed=embed)


@bot.command(name='guild')
async def guild_command(ctx, action=None, *, target=None):
    """Guild management system"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Check if guild is unlocked
    if not check_command_unlocked(player["area"], "guild") and player.get("time_travels", 0) == 0:
        await ctx.send("🔒 Guild is unlocked in Area 4!")
        return

    # Initialize guild data if not exists
    if "guild" not in player:
        player["guild"] = None
    if "guild_rings" not in player:
        player["guild_rings"] = 0

    # Ensure guild_data is loaded
    global guild_data
    if guild_data is None:
        guild_data = load_guild_data()

    if action is None:
        # Show guild info
        if player["guild"]:
            guild = guild_data.get(player["guild"])
            if guild:
                embed = discord.Embed(title=f"🏰 Guild: {guild['name']}", color=0x9932cc)
                embed.add_field(name="Level", value=guild["level"], inline=True)
                embed.add_field(name="Experience", value=f"{guild['exp']}/{guild['level'] * 1000}", inline=True)
                embed.add_field(name="Energy", value=guild["energy"], inline=True)
                embed.add_field(name="Stealth", value=guild["stealth"], inline=True)
                embed.add_field(name="Members", value=f"{len(guild['members'])}/10", inline=True)

                members_list = []
                for member_id in guild["members"]:
                    user = bot.get_user(int(member_id))
                    if user:
                        role = "👑 Owner" if member_id == guild["owner"] else "👤 Member"
                        members_list.append(f"{role} {user.display_name}")
                    else:
                        role = "👑 Owner" if member_id == guild["owner"] else "👤 Member"
                        members_list.append(f"{role} Unknown User")

                embed.add_field(name="Members List", value="\n".join(members_list) if members_list else "No members",
                                inline=False)
                embed.add_field(name="Your Guild Rings", value=player["guild_rings"], inline=True)

                await ctx.send(embed=embed)
            else:
                player["guild"] = None
                await ctx.send("Your guild no longer exists!")
        else:
            embed = discord.Embed(title="🏰 Guild System", description="You are not in a guild", color=0x9932cc)
            embed.add_field(name="Available Commands",
                            value="`rpg guild create <name>` - Create a guild\n`rpg guild join <name>` - Join a guild\n`rpg guild list` - List all guilds",
                            inline=False)
            embed.add_field(name="Guild Benefits",
                            value="• 2% extra XP and coins per guild level in duels\n• Weekly rewards based on energy ranking\n• Access to guild shop with exclusive items",
                            inline=False)
            await ctx.send(embed=embed)

    elif action == "create":
        if player["guild"]:
            await ctx.send("You are already in a guild! Leave your current guild first.")
            return

        if not target:
            await ctx.send("Please provide a guild name! Example: `rpg guild create MyGuild`")
            return

        guild_name = target
        if len(guild_name) < 2 or len(guild_name) > 12:
            await ctx.send("Guild name must be 2-12 characters long!")
            return

        # Check if guild name already exists
        for guild_id, guild in guild_data.items():
            if guild["name"].lower() == guild_name.lower():
                await ctx.send("A guild with this name already exists!")
                return

        # Create new guild
        guild_id = str(len(guild_data) + 1)
        guild_data[guild_id] = {
            "name": guild_name,
            "owner": str(ctx.author.id),
            "members": [str(ctx.author.id)],
            "level": 1,
            "exp": 0,
            "energy": 100,
            "stealth": 10,
            "last_raid": 0,
            "weekly_tasks": {},
            "created_at": time.time()
        }

        player["guild"] = guild_id

        embed = discord.Embed(title="🏰 Guild Created!", color=0x00ff00)
        embed.add_field(name="Guild Name", value=guild_name, inline=True)
        embed.add_field(name="Owner", value=ctx.author.display_name, inline=True)
        embed.add_field(name="Status", value="You are now the guild owner!", inline=False)

        save_guild_data()
        save_player_data()
        await ctx.send(embed=embed)

    elif action == "invite":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        guild = guild_data.get(player["guild"])
        if not guild:
            await ctx.send("Your guild no longer exists!")
            return

        if str(ctx.author.id) != guild["owner"]:
            await ctx.send("Only the guild owner can invite members!")
            return

        if len(guild["members"]) >= 10:
            await ctx.send("Guild is full! Maximum 10 members allowed.")
            return

        # Parse mention or user ID
        if not target:
            await ctx.send("Please mention a user to invite!")
            return

        # Try to get user from mention
        user = None
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            try:
                user_id = int(target.strip('<@!>'))
                user = bot.get_user(user_id)
            except:
                await ctx.send("Invalid user mention or ID!")
                return

        if not user:
            await ctx.send("User not found!")
            return

        target_player = get_player(user.id)
        if not target_player:
            await ctx.send("This user hasn't started their adventure yet!")
            return

        if target_player.get("guild"):
            await ctx.send("This user is already in a guild!")
            return

        # Add to guild
        guild["members"].append(str(user.id))
        target_player["guild"] = player["guild"]

        embed = discord.Embed(title="🏰 Guild Invitation", color=0x00ff00)
        embed.add_field(name="New Member", value=user.display_name, inline=True)
        embed.add_field(name="Guild", value=guild["name"], inline=True)
        embed.add_field(name="Members", value=f"{len(guild['members'])}/10", inline=True)

        save_guild_data()
        save_player_data()
        await ctx.send(embed=embed)

    elif action == "leave":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        guild = guild_data.get(player["guild"])
        if not guild:
            await ctx.send("Your guild no longer exists!")
            return

        if str(ctx.author.id) == guild["owner"]:
            await ctx.send("Guild owners cannot leave! Transfer ownership or delete the guild first.")
            return

        # Remove from guild
        if str(ctx.author.id) in guild["members"]:
            guild["members"].remove(str(ctx.author.id))
        player["guild"] = None

        embed = discord.Embed(title="🏰 Left Guild", color=0xff6600)
        embed.add_field(name="Guild", value=guild["name"], inline=True)
        embed.add_field(name="Status", value="You have left the guild", inline=True)

        save_guild_data()
        save_player_data()
        await ctx.send(embed=embed)

    elif action == "kick":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        guild = guild_data.get(player["guild"])
        if not guild:
            await ctx.send("Your guild no longer exists!")
            return

        if str(ctx.author.id) != guild["owner"]:
            await ctx.send("Only the guild owner can kick members!")
            return

        # Parse mention or user ID
        if not target:
            await ctx.send("Please mention a user to kick!")
            return

        user = None
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            try:
                user_id = int(target.strip('<@!>'))
                user = bot.get_user(user_id)
            except:
                await ctx.send("Invalid user mention or ID!")
                return

        if not user:
            await ctx.send("User not found!")
            return

        if str(user.id) not in guild["members"]:
            await ctx.send("This user is not in your guild!")
            return

        if str(user.id) == guild["owner"]:
            await ctx.send("You cannot kick yourself!")
            return

        # Remove from guild
        guild["members"].remove(str(user.id))
        target_player = get_player(user.id)
        if target_player:
            target_player["guild"] = None

        embed = discord.Embed(title="🏰 Member Kicked", color=0xff0000)
        embed.add_field(name="Kicked", value=user.display_name, inline=True)
        embed.add_field(name="Guild", value=guild["name"], inline=True)

        save_guild_data()
        save_player_data()
        await ctx.send(embed=embed)

    elif action == "raid":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        guild = guild_data.get(player["guild"])
        if not guild:
            await ctx.send("Your guild no longer exists!")
            return

        # Check cooldown (2 hours)
        if time.time() - guild.get("last_raid", 0) < 7200:
            remaining = 7200 - (time.time() - guild.get("last_raid", 0))
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await ctx.send(f"Guild raid is on cooldown! Wait {hours}h {minutes}m")
            return

        # Find target guild with lower stealth and higher energy
        target_guilds = []
        for gid, g in guild_data.items():
            if gid != player["guild"] and g["energy"] > 0:
                if g["stealth"] <= guild["stealth"] and g["energy"] >= guild["energy"] * 0.5:
                    target_guilds.append((gid, g))

        if not target_guilds:
            await ctx.send("No suitable guilds to raid!")
            return

        target_guild_id, target_guild = random.choice(target_guilds)

        # Simulate raid
        success_chance = max(20, min(80, 50 + (guild["stealth"] - target_guild["stealth"]) * 2))
        raid_success = random.randint(1, 100) <= success_chance

        guild["last_raid"] = time.time()

        if raid_success:
            # Calculate energy stolen (30-65% of target's energy, minimum 1)
            stolen_percentage = random.randint(30, 65)
            stolen_energy = max(1, int(target_guild["energy"] * stolen_percentage / 100))
            energy_lost = max(1, int(stolen_energy * 0.25))

            guild["energy"] += stolen_energy
            target_guild["energy"] = max(0, target_guild["energy"] - energy_lost)
            guild["exp"] += random.randint(20, 50)

            embed = discord.Embed(title="⚔️ Raid Successful!", color=0x00ff00)
            embed.add_field(name="Target", value=target_guild["name"], inline=True)
            embed.add_field(name="Energy Stolen", value=stolen_energy, inline=True)
            embed.add_field(name="Guild EXP", value=f"+{random.randint(20, 50)}", inline=True)
            embed.add_field(name="Your Guild Energy", value=guild["energy"], inline=True)
        else:
            # Failed raid - still get some energy and exp
            failed_energy = random.randint(0, 10)
            guild["energy"] += failed_energy
            guild["exp"] += random.randint(5, 15)

            embed = discord.Embed(title="💀 Raid Failed!", color=0xff0000)
            embed.add_field(name="Target", value=target_guild["name"], inline=True)
            embed.add_field(name="Energy Gained", value=failed_energy, inline=True)
            embed.add_field(name="Guild EXP", value=f"+{random.randint(5, 15)}", inline=True)

        # Check for guild level up
        exp_needed = guild["level"] * 1000
        if guild["exp"] >= exp_needed:
            guild["level"] += 1
            guild["exp"] -= exp_needed
            embed.add_field(name="🎊 Guild Level Up!", value=f"Guild reached level {guild['level']}!", inline=False)

        save_guild_data()
        await ctx.send(embed=embed)

    elif action == "upgrade":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        guild = guild_data.get(player["guild"])
        if not guild:
            await ctx.send("Your guild no longer exists!")
            return

        # Check cooldown (same as raid - 2 hours)
        if time.time() - guild.get("last_raid", 0) < 7200:
            remaining = 7200 - (time.time() - guild.get("last_raid", 0))
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await ctx.send(f"Guild upgrade is on cooldown! Wait {hours}h {minutes}m")
            return

        guild["last_raid"] = time.time()

        # Calculate stealth gain (1-7, higher stealth = lower gains)
        current_stealth = guild["stealth"]
        if current_stealth >= 95:
            await ctx.send("Your guild has maximum stealth!")
            return

        max_gain = max(1, 8 - int(current_stealth / 15))
        stealth_gain = random.randint(1, max_gain)

        # Chance to fail at high stealth
        if current_stealth > 80:
            fail_chance = (current_stealth - 80) * 2
            if random.randint(1, 100) <= fail_chance:
                stealth_gain = 0

        guild["stealth"] = min(95, guild["stealth"] + stealth_gain)
        guild["exp"] += random.randint(10, 30)

        embed = discord.Embed(title="🔧 Guild Upgrade", color=0x0099ff)
        embed.add_field(name="Stealth Gained", value=f"+{stealth_gain}", inline=True)
        embed.add_field(name="Current Stealth", value=guild["stealth"], inline=True)
        embed.add_field(name="Guild EXP", value=f"+{random.randint(10, 30)}", inline=True)

        if stealth_gain == 0:
            embed.add_field(name="Note", value="Upgrade failed due to high stealth level!", inline=False)

        save_guild_data()
        await ctx.send(embed=embed)

    elif action == "buy":
        if not player["guild"]:
            await ctx.send("You are not in a guild!")
            return

        if not target:
            await ctx.send("Please specify an item to buy! Use `rpg guild shop` to see available items.")
            return

        item_name = target
        item_found = None
        for item, data in GUILD_SHOP_ITEMS.items():
            if item.lower() == item_name.lower():
                item_found = item
                break

        if not item_found:
            await ctx.send("Item not found! Use `rpg guild shop` to see available items.")
            return

        item_data = GUILD_SHOP_ITEMS[item_found]
        cost = item_data["cost"]

        if player["guild_rings"] < cost:
            await ctx.send(f"You need {cost} guild rings to buy {item_found}!")
            return

        player["guild_rings"] -= cost

        # Handle different items
        if item_found == "EPIC lootbox":
            if "EPIC lootbox" not in player["inventory"]:
                player["inventory"]["EPIC lootbox"] = 0
            player["inventory"]["EPIC lootbox"] += 1
        elif item_found == "EDGY lootbox":
            if "EDGY lootbox" not in player["inventory"]:
                player["inventory"]["EDGY lootbox"] = 0
            player["inventory"]["EDGY lootbox"] += 1
        elif item_found == "Special seed":
            special_seeds = ["Carrot seed", "Potato seed", "Bread seed"]
            seed = random.choice(special_seeds)
            if seed not in player["inventory"]:
                player["inventory"][seed] = 0
            player["inventory"][seed] += 1

        embed = discord.Embed(title="🛒 Guild Shop Purchase", color=0x00ff00)
        embed.add_field(name="Item", value=item_found, inline=True)
        embed.add_field(name="Cost", value=f"{cost} guild rings", inline=True)
        embed.add_field(name="Remaining Rings", value=player["guild_rings"], inline=True)

        save_player_data()
        await ctx.send(embed=embed)

    elif action == "shop":
        embed = discord.Embed(title="🏪 Guild Shop", color=0xffd700)

        shop_text = ""
        for item, data in GUILD_SHOP_ITEMS.items():
            shop_text += f"**{item}** - {data['cost']} rings\n{data['description']}\n\n"

        embed.add_field(name="Available Items", value=shop_text, inline=False)
        embed.add_field(name="Your Guild Rings", value=player.get("guild_rings", 0), inline=True)
        embed.add_field(name="Usage", value="Use `rpg guild buy <item>` to purchase", inline=False)

        await ctx.send(embed=embed)

    elif action == "list":
        if not guild_data:
            await ctx.send("No guilds exist yet!")
            return

        embed = discord.Embed(title="🏰 Guild List", color=0x9932cc)

        guild_list = ""
        sorted_guilds = sorted(guild_data.items(), key=lambda x: x[1]["level"], reverse=True)

        for i, (guild_id, guild) in enumerate(sorted_guilds[:10]):
            guild_list += f"{i + 1}. **{guild['name']}** (Level {guild['level']})\n"
            guild_list += f"   Members: {len(guild['members'])}/10 | Energy: {guild['energy']}\n\n"

        embed.add_field(name="Top Guilds", value=guild_list if guild_list else "No guilds found", inline=False)
        embed.add_field(name="Usage", value="`rpg guild create <name>` to create a guild", inline=False)

        await ctx.send(embed=embed)

    else:
        await ctx.send("Invalid guild action! Use `rpg guild` to see available commands.")


@bot.command(name='titles')
async def titles_command(ctx, action=None, *, title_name=None):
    """Manage player titles"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    if "titles" not in player:
        player["titles"] = []
    if "active_title" not in player:
        player["active_title"] = None

    if action == "set":
        if not title_name:
            await ctx.send("Please specify a title to set! Use `rpg titles` to see available titles.")
            return

        if title_name not in player["titles"]:
            await ctx.send("You don't have this title!")
            return

        player["active_title"] = title_name

        embed = discord.Embed(title="🏆 Title Set", color=0xffd700)
        embed.add_field(name="Active Title", value=title_name, inline=True)

        save_player_data()
        await ctx.send(embed=embed)

    elif action == "remove":
        player["active_title"] = None

        embed = discord.Embed(title="🏆 Title Removed", color=0xff6600)
        embed.add_field(name="Status", value="No active title", inline=True)

        save_player_data()
        await ctx.send(embed=embed)

    else:
        # Show titles
        embed = discord.Embed(title="🏆 Your Titles", color=0xffd700)

        if player["titles"]:
            titles_text = ""
            for title in player["titles"]:
                if title == player["active_title"]:
                    titles_text += f"⭐ **{title}** (Active)\n"
                else:
                    titles_text += f"• {title}\n"
            embed.add_field(name="Owned Titles", value=titles_text, inline=False)
        else:
            embed.add_field(name="Owned Titles", value="No titles yet", inline=False)

        # Show how to get more titles
        tt_count = player.get("time_travels", 0)
        next_title_tt = None
        for tt_req, title in TT_TITLES.items():
            if tt_req > tt_count:
                next_title_tt = tt_req
                next_title = title
                break

        if next_title_tt:
            embed.add_field(name="Next Title", value=f"**{next_title}** (Time Travel {next_title_tt})", inline=False)

        embed.add_field(name="Commands",
                        value="`rpg titles set <title>` - Set active title\n`rpg titles remove` - Remove active title",
                        inline=False)

        await ctx.send(embed=embed)


# Lootbox rewards system
LOOTBOX_REWARDS = {
    "common lootbox": {
        "common": ["Wooden Log", "Normie Fish", "Epic Log", "Golden Fish", "Wolf Skin"],
        "uncommon": [],
        "rare": [],
        "item_range": [1, 2],
        "coin_range": [100, 500]
    },
    "uncommon lootbox": {
        "common": ["Wooden Log", "Normie Fish", "Epic Log", "Golden Fish", "Wolf Skin"],
        "uncommon": ["Zombie Eye", "Super Log", "common lootbox"],
        "rare": [],
        "item_range": [3, 5],
        "coin_range": [500, 1500]
    },
    "rare lootbox": {
        "common": ["Wooden Log", "Normie Fish", "Apple", "Epic Log", "Golden Fish", "Banana"],
        "uncommon": ["Wolf Skin", "Zombie Eye", "Super Log", "Unicorn Horn", "Mega Log"],
        "rare": ["uncommon lootbox"],
        "item_range": [7, 10],
        "coin_range": [2000, 8000]
    },
    "EPIC lootbox": {
        "common": ["Apple", "Epic Log", "Golden Fish", "Banana"],
        "uncommon": ["Wolf Skin", "Zombie Eye", "Unicorn Horn", "Ruby", "Super Log", "Mermaid Hair"],
        "rare": ["Mega Log", "HYPER Log", "rare lootbox"],
        "item_range": [12, 17],
        "coin_range": [10000, 25000]
    },
    "EDGY lootbox": {
        "common": ["Epic Log", "Golden Fish", "Banana", "Ruby"],
        "uncommon": ["Wolf Skin", "Zombie Eye", "Unicorn Horn", "Mermaid Hair", "Chip", "Super Log"],
        "rare": ["Mega Log", "EPIC Fish", "HYPER Log", "ULTRA Log", "EPIC lootbox"],
        "item_range": [19, 26],
        "coin_range": [25000, 100000]
    },
    "OMEGA lootbox": {
        "common": ["Mega Log", "EPIC Fish", "HYPER Log"],
        "uncommon": ["Dragon Scale", "ULTRA Log"],
        "rare": [],
        "item_range": [31, 44],
        "coin_range": [100000, 500000]
    },
    "GODLY lootbox": {
        "common": ["Dragon Scale", "ULTRA Log"],
        "uncommon": ["ULTIMATE Log"],
        "rare": [],
        "item_range": [500, 800],
        "coin_range": [1000000, 5000000]
    },
    "VOID lootbox": {
        "common": ["Dark Energy", "Watermelon", "SUPER Fish"],
        "uncommon": ["ULTIMATE Log"],
        "rare": [],
        "item_range": [4200, 10000],
        "coin_range": [5000000, 25000000]
    }
}


@bot.command(name='open')
async def open_lootbox(ctx, *, lootbox_name=None, amount=1):
    """Open lootboxes from inventory"""
    if not lootbox_name:
        await ctx.send("Please specify a lootbox to open! Example: `rpg open common lootbox`")
        return

    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    # Handle amount
    lootbox_parts = lootbox_name.split()
    if lootbox_parts[-1].isdigit():
        amount = int(lootbox_parts[-1])
        lootbox_name = " ".join(lootbox_parts[:-1])

    try:
        amount = int(amount)
        if amount <= 0:
            amount = 1
    except:
        amount = 1

    # Find lootbox in inventory (check aliases)
    lootbox_aliases = {
        "c lb": "common lootbox",
        "u lb": "uncommon lootbox",
        "r lb": "rare lootbox",
        "ep lb": "EPIC lootbox",
        "ed lb": "EDGY lootbox",
        "o lb": "OMEGA lootbox",
        "g lb": "GODLY lootbox",
        "v lb": "VOID lootbox"
    }

    lootbox_key = lootbox_name.lower()
    if lootbox_key in lootbox_aliases:
        lootbox_key = lootbox_aliases[lootbox_key]

    # Find exact match in inventory
    found_lootbox = None
    for item in player["inventory"]:
        if item.lower() == lootbox_key:
            found_lootbox = item
            break

    if not found_lootbox or player["inventory"][found_lootbox] < amount:
        await ctx.send(f"You don't have {amount} {lootbox_name}!")
        return

    if found_lootbox not in LOOTBOX_REWARDS:
        await ctx.send("This lootbox cannot be opened!")
        return

    # Open lootboxes
    all_rewards = []
    total_coins = 0

    for _ in range(amount):
        rewards = open_single_lootbox(player, found_lootbox)
        all_rewards.extend(rewards["items"])
        total_coins += rewards["coins"]

    # Consume lootboxes
    player["inventory"][found_lootbox] -= amount
    if player["inventory"][found_lootbox] <= 0:
        del player["inventory"][found_lootbox]

    # Add coins
    player["coins"] += total_coins

    # Create result message
    embed = discord.Embed(title="🎁 Lootbox Opened!", color=0xffd700)
    embed.add_field(name="Opened", value=f"{found_lootbox} x{amount}", inline=True)

    if total_coins > 0:
        embed.add_field(name="Coins", value=f"+{total_coins:,}", inline=True)

    if all_rewards:
        # Group same items
        reward_counts = {}
        for item in all_rewards:
            reward_counts[item] = reward_counts.get(item, 0) + 1

        rewards_text = ""
        for item, count in reward_counts.items():
            rewards_text += f"{item} x{count}\n"

        embed.add_field(name="Items Received", value=rewards_text[:1024], inline=False)
    else:
        embed.add_field(name="Items", value="No items received", inline=False)

    # Check for lootbox event (small chance)
    if amount == 1 and random.random() * 100 < 1:
        embed.add_field(name="🎊 Lootbox Event!", value="The lootbox got stuck and triggered a special event!",
                        inline=False)

    save_player_data()
    await ctx.send(embed=embed)


def open_single_lootbox(player, lootbox_name):
    """Open a single lootbox and return rewards"""
    if lootbox_name not in LOOTBOX_REWARDS:
        return {"items": [], "coins": 0}

    rewards_data = LOOTBOX_REWARDS[lootbox_name]
    rewards = {"items": [], "coins": 0}

    # Generate coins
    coin_min, coin_max = rewards_data["coin_range"]
    coins = random.randint(coin_min, coin_max)
    rewards["coins"] = coins

    # Generate items
    item_min, item_max = rewards_data["item_range"]
    num_items = random.randint(item_min, item_max)

    max_area = max(player.get("max_area_reached", player["area"]), player["area"])

    for _ in range(num_items):
        # Determine rarity (common 70%, uncommon 25%, rare 5%)
        rarity_roll = random.random() * 100

        if rarity_roll < 70 and rewards_data["common"]:
            item_pool = rewards_data["common"]
        elif rarity_roll < 95 and rewards_data["uncommon"]:
            item_pool = rewards_data["uncommon"]
        elif rewards_data["rare"]:
            item_pool = rewards_data["rare"]
        else:
            item_pool = rewards_data["common"] + rewards_data["uncommon"]

        if item_pool:
            item = random.choice(item_pool)

            # Check area restrictions (except for logs and fish)
            if item not in ["Wooden Log", "Epic Log", "Super Log", "Mega Log", "HYPER Log", "ULTRA Log", "ULTIMATE Log",
                            "Normie Fish", "Golden Fish", "EPIC Fish", "SUPER Fish"]:
                # Simple area check for other items - only skip if area requirement not met
                skip_item = False
                if "Apple" in item and max_area < 3:
                    skip_item = True
                elif "Zombie Eye" in item and max_area < 3:
                    skip_item = True
                elif "Ruby" in item and max_area < 4:
                    skip_item = True
                elif "Unicorn Horn" in item and max_area < 5:
                    skip_item = True
                elif "Mermaid Hair" in item and max_area < 7:
                    skip_item = True
                elif "Chip" in item and max_area < 9:
                    skip_item = True
                elif "Dragon Scale" in item and max_area < 11:
                    skip_item = True

                if skip_item:
                    continue

            # Add item to inventory
            if item not in player["inventory"]:
                player["inventory"][item] = 0
            player["inventory"][item] += 1
            rewards["items"].append(item)

    return rewards


@bot.command(name='use')
async def use_item(ctx, *, item_name=None):
    """Use consumable items from inventory"""
    if not item_name:
        await ctx.send("Please specify an item to use! Example: `rpg use life potion`")
        return

    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpg start` to create your adventure account first!")
        return

    item_name_lower = item_name.lower()

    if item_name_lower == "life potion":
        if player["inventory"].get("life potion", 0) <= 0:
            await ctx.send("You don't have any life potions! Buy them with `rpg buy life potion`")
            return

        if player["hp"] >= player["max_hp"]:
            await ctx.send("You're already at full health!")
            return

        # Use life potion
        player["inventory"]["life potion"] -= 1
        if player["inventory"]["life potion"] <= 0:
            del player["inventory"]["life potion"]

        player["hp"] = player["max_hp"]

        # Check for heal event (0.75% chance in area 6+)
        if player["area"] >= 6 and random.random() * 100 < 0.75:
            await handle_heal_event(ctx, player)
            save_player_data()
            return

        embed = discord.Embed(title="💊 Life Potion Used", color=0x00ff00)
        embed.add_field(name="Result", value=f"HP restored to {player['max_hp']}", inline=False)
        embed.add_field(name="Life Potions Remaining", value=player["inventory"].get("life potion", 0), inline=False)

        save_player_data()
        await ctx.send(embed=embed)

    else:
        await ctx.send("Unknown item or item cannot be used!")


@bot.command(name='title')
async def title_command(ctx, action=None, *, title_name=None):
    """Manage player titles"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if "titles" not in player:
        player["titles"] = []
    if "active_title" not in player:
        player["active_title"] = None

    if action == "use":
        if not title_name:
            await ctx.send("Please specify a title to use! Use `rpgs title list` to see available titles.")
            return

        if title_name not in player["titles"]:
            await ctx.send("You don't have this title!")
            return

        player["active_title"] = title_name

        embed = discord.Embed(title="🏆 Title Set", color=0xffd700)
        embed.add_field(name="Active Title", value=title_name, inline=True)

        save_player_data()
        await ctx.send(embed=embed)

    elif action == "remove":
        player["active_title"] = None

        embed = discord.Embed(title="🏆 Title Removed", color=0xff6600)
        embed.add_field(name="Status", value="No active title", inline=True)

        save_player_data()
        await ctx.send(embed=embed)

    elif action == "list":
        # Show titles
        embed = discord.Embed(title="🏆 Your Titles", color=0xffd700)

        if player["titles"]:
            titles_text = ""
            for title in player["titles"]:
                if title == player["active_title"]:
                    titles_text += f"⭐ **{title}** (Active)\n"
                else:
                    titles_text += f"• {title}\n"
            embed.add_field(name="Owned Titles", value=titles_text, inline=False)
        else:
            embed.add_field(name="Owned Titles", value="No titles yet", inline=False)

        # Show how to get more titles
        tt_count = player.get("time_travels", 0)
        next_title_tt = None
        for tt_req, title in TT_TITLES.items():
            if tt_req > tt_count:
                next_title_tt = tt_req
                next_title = title
                break

        if next_title_tt:
            embed.add_field(name="Next Title", value=f"**{next_title}** (Time Travel {next_title_tt})", inline=False)

        embed.add_field(name="Commands",
                        value="`rpgs title use <title>` - Set active title\n`rpgs title remove` - Remove active title",
                        inline=False)

        await ctx.send(embed=embed)
    else:
        # Show title info
        embed = discord.Embed(title="🏆 Title System", color=0xffd700)

        current_title = player.get("active_title", "None")
        embed.add_field(name="Current Title", value=current_title, inline=True)
        embed.add_field(name="Titles Owned", value=len(player.get("titles", [])), inline=True)

        embed.add_field(name="Commands",
                        value="`rpgs title list` - View your titles\n`rpgs title use <title>` - Set active title\n`rpgs title remove` - Remove active title",
                        inline=False)

        await ctx.send(embed=embed)


# Gambling system
def calculate_coin_cap(time_travels, max_area):
    """Calculate coin cap for multidice and give commands"""
    return 500000000 * (time_travels ** 4) + 100000 * (max_area ** 2)


@bot.command(name='blackjack', aliases=['bj'])
async def blackjack(ctx, bet_amount=None):
    """Play blackjack"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not bet_amount:
        await ctx.send("Please specify a bet amount! Example: `rpgs bj 100`")
        return

    try:
        bet = int(bet_amount)
        if bet <= 0:
            await ctx.send("Bet amount must be positive!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    # Simple blackjack simulation
    def card_value():
        return random.randint(1, 11)

    player_cards = [card_value(), card_value()]
    dealer_cards = [card_value(), card_value()]

    player_total = sum(player_cards)
    dealer_total = sum(dealer_cards)

    # Check for instant 21 (achievement trigger)
    instant_21 = player_total == 21

    # Simple AI for dealer
    while dealer_total < 17:
        dealer_cards.append(card_value())
        dealer_total = sum(dealer_cards)

    # Determine winner
    result = ""
    multiplier = 0

    if player_total > 21:
        result = "💥 **BUST!** You went over 21!"
        multiplier = 0
    elif dealer_total > 21:
        result = "🎉 **DEALER BUST!** Dealer went over 21!"
        multiplier = 2
    elif player_total == 21 and len(player_cards) == 2:
        result = "🃏 **BLACKJACK!** Perfect 21!"
        multiplier = 2.5
    elif player_total > dealer_total:
        result = "🎉 **YOU WIN!** Your hand beats the dealer!"
        multiplier = 2
    elif player_total == dealer_total:
        result = "🤝 **TIE!** Same value as dealer!"
        multiplier = 1
    else:
        result = "💸 **DEALER WINS!** Dealer's hand is higher!"
        multiplier = 0

    # Calculate winnings
    if multiplier == 1:  # Tie
        winnings = 0
    else:
        winnings = int(bet * multiplier) - bet

    player["coins"] += winnings

    embed = discord.Embed(title="🃏 Blackjack", color=0x000000)
    embed.add_field(name="Your Cards", value=f"{player_cards} = **{player_total}**", inline=True)
    embed.add_field(name="Dealer Cards", value=f"{dealer_cards} = **{dealer_total}**", inline=True)
    embed.add_field(name="Result", value=result, inline=False)

    if winnings > 0:
        embed.add_field(name="Winnings", value=f"+{winnings:,} coins", inline=True)
    elif winnings < 0:
        embed.add_field(name="Loss", value=f"{winnings:,} coins", inline=True)
    else:
        embed.add_field(name="Result", value="No change", inline=True)

    embed.add_field(name="Balance", value=f"{player['coins']:,} coins", inline=True)

    if instant_21:
        embed.add_field(name="🏆 Achievement!", value="**ez** - Got an instant 21!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='coinflip', aliases=['cf'])
async def coinflip(ctx, choice=None, bet_amount=None):
    """Flip a coin - heads or tails"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not choice or not bet_amount:
        await ctx.send("Usage: `rpgs cf h/t <amount>` (h=heads, t=tails)")
        return

    if choice.lower() not in ['h', 't', 'heads', 'tails']:
        await ctx.send("Choose 'h' for heads or 't' for tails!")
        return

    try:
        bet = int(bet_amount)
        if bet <= 0:
            await ctx.send("Bet amount must be positive!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    # Flip coin
    result = random.choice(['heads', 'tails'])
    player_choice = 'heads' if choice.lower() in ['h', 'heads'] else 'tails'

    embed = discord.Embed(title="🪙 Coinflip", color=0xffd700)
    embed.add_field(name="Your Choice", value=player_choice.title(), inline=True)
    embed.add_field(name="Result", value=result.title(), inline=True)

    if result == player_choice:
        # Win - double the bet
        winnings = bet
        player["coins"] += winnings
        embed.add_field(name="🎉 You Win!", value=f"+{winnings:,} coins", inline=False)
        embed.color = 0x00ff00
    else:
        # Lose
        player["coins"] -= bet
        embed.add_field(name="💸 You Lose!", value=f"-{bet:,} coins", inline=False)
        embed.color = 0xff0000

    embed.add_field(name="Balance", value=f"{player['coins']:,} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='slots')
async def slots(ctx, bet_amount=None):
    """Play slot machine"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not bet_amount:
        await ctx.send("Please specify a bet amount! Example: `rpgs slots 100`")
        return

    try:
        bet = int(bet_amount)
        if bet <= 0:
            await ctx.send("Bet amount must be positive!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    # Slot symbols and their weights
    symbols = ['💎', '💯', '🍀', '🎁', '✨']
    weights = [2, 4, 6, 8, 10]  # Lower weight = rarer

    # Generate 5 symbols
    result = []
    for _ in range(5):
        result.append(random.choices(symbols, weights=weights)[0])

    # Check for wins
    multiplier = 0
    win_type = ""

    # Count consecutive symbols from left
    consecutive_count = 1
    for i in range(1, 5):
        if result[i] == result[0]:
            consecutive_count += 1
        else:
            break

    # Calculate multiplier based on symbol and count
    if consecutive_count >= 3:
        symbol = result[0]
        if consecutive_count == 5:
            # 5 in a row
            if symbol == '💎':
                multiplier = 20
            elif symbol == '💯':
                multiplier = 17.5
            elif symbol == '🍀':
                multiplier = 15
            elif symbol == '🎁':
                multiplier = 12.5
            elif symbol == '✨':
                multiplier = 10
            win_type = f"5 in a row: {symbol}"
        elif consecutive_count == 4:
            # 4 in a row
            if symbol == '💎':
                multiplier = 5.5
            elif symbol == '💯':
                multiplier = 4.8125
            elif symbol == '🍀':
                multiplier = 4.125
            elif symbol == '🎁':
                multiplier = 3.4375
            elif symbol == '✨':
                multiplier = 2.75
            win_type = f"4 in a row: {symbol}"
        elif consecutive_count == 3:
            # 3 in a row
            if symbol == '💎':
                multiplier = 2.0
            elif symbol == '💯':
                multiplier = 1.75
            elif symbol == '🍀':
                multiplier = 1.5
            elif symbol == '🎁':
                multiplier = 1.25
            elif symbol == '✨':
                multiplier = 1.0
            win_type = f"3 in a row: {symbol}"

    embed = discord.Embed(title="🎰 Slots", color=0xff6600)
    embed.add_field(name="Result", value=" ".join(result), inline=False)

    if multiplier > 0:
        winnings = int(bet * multiplier)
        profit = winnings - bet
        player["coins"] += profit

        embed.add_field(name="🎉 Win!", value=win_type, inline=True)
        embed.add_field(name="Multiplier", value=f"{multiplier}x", inline=True)
        embed.add_field(name="Winnings", value=f"+{profit:,} coins", inline=True)
        embed.color = 0x00ff00
    else:
        player["coins"] -= bet
        embed.add_field(name="💸 No Win", value="Better luck next time!", inline=False)
        embed.add_field(name="Loss", value=f"-{bet:,} coins", inline=True)
        embed.color = 0xff0000

    embed.add_field(name="Balance", value=f"{player['coins']:,} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='multidice')
async def multidice(ctx, target_user: discord.User = None, bet_amount=None):
    """Play dice with another player"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not check_command_unlocked(player["area"], "multidice"):
        await ctx.send("🔒 Multidice is unlocked in Area 5!")
        return

    if not target_user or not bet_amount:
        await ctx.send("Usage: `rpgs multidice @user <amount>`")
        return

    if target_user.id == ctx.author.id:
        await ctx.send("You can't play against yourself!")
        return

    target_player = get_player(target_user.id)
    if not target_player:
        await ctx.send(f"{target_user.display_name} doesn't have an account!")
        return

    try:
        bet = int(bet_amount)
        if bet <= 0:
            await ctx.send("Bet amount must be positive!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    # Check coin caps
    player_max_area = max(player.get("max_area_reached", player["area"]), player["area"])
    target_max_area = max(target_player.get("max_area_reached", target_player["area"]), target_player["area"])

    player_cap = calculate_coin_cap(player.get("time_travels", 0), player_max_area)
    target_cap = calculate_coin_cap(target_player.get("time_travels", 0), target_max_area)

    if player["coins"] + bet > player_cap:
        await ctx.send(f"This bet would exceed your coin cap of {player_cap:,}!")
        return

    if target_player["coins"] + bet > target_cap:
        await ctx.send(f"This bet would exceed {target_user.display_name}'s coin cap of {target_cap:,}!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    if target_player["coins"] < bet:
        await ctx.send(f"{target_user.display_name} doesn't have {bet:,} coins!")
        return

    # Roll dice
    player_roll = random.randint(1, 6)
    target_roll = random.randint(1, 6)

    embed = discord.Embed(title="🎲 Multidice", color=0x9932cc)
    embed.add_field(name=ctx.author.display_name, value=f"🎲 {player_roll}", inline=True)
    embed.add_field(name=target_user.display_name, value=f"🎲 {target_roll}", inline=True)

    if player_roll > target_roll:
        # Player wins
        player["coins"] += bet
        target_player["coins"] -= bet
        embed.add_field(name="🎉 Winner", value=ctx.author.display_name, inline=False)
        embed.color = 0x00ff00
    elif target_roll > player_roll:
        # Target wins
        player["coins"] -= bet
        target_player["coins"] += bet
        embed.add_field(name="🎉 Winner", value=target_user.display_name, inline=False)
        embed.color = 0xff0000
    else:
        # Tie
        embed.add_field(name="🤝 Result", value="It's a tie! No coins exchanged.", inline=False)
        embed.color = 0xffff00

    embed.add_field(name="Bet Amount", value=f"{bet:,} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='wheel')
async def wheel(ctx, bet_amount=None):
    """Spin the wheel (Area 8+)"""
    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not check_command_unlocked(player["area"], "wheel"):
        await ctx.send("🔒 Wheel is unlocked in Area 8!")
        return

    if not bet_amount:
        await ctx.send("Please specify a bet amount! Minimum: 25,000 coins")
        return

    try:
        bet = int(bet_amount)
        if bet < 25000:
            await ctx.send("Minimum bet is 25,000 coins!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    # Wheel segments: 4 blue, 4 brown, 4 orange, 1 purple, 1 red, 1 green, 1 yellow
    segments = ['blue'] * 4 + ['brown'] * 4 + ['orange'] * 4 + ['purple', 'red', 'green', 'yellow']
    result = random.choice(segments)

    embed = discord.Embed(title="🎡 Wheel Spin", color=0x9932cc)

    segment_colors = {
        'blue': 0x0000ff,
        'brown': 0x8b4513,
        'orange': 0xffa500,
        'purple': 0x800080,
        'red': 0xff0000,
        'green': 0x00ff00,
        'yellow': 0xffff00
    }

    embed.color = segment_colors.get(result, 0x9932cc)
    embed.add_field(name="Result", value=f"🎯 {result.upper()}", inline=False)

    if result == 'blue':
        # Lose 100%
        loss = bet
        player["coins"] -= loss
        embed.add_field(name="💸 Result", value=f"Lost {loss:,} coins", inline=True)
    elif result == 'brown':
        # Lose 90%
        loss = int(bet * 0.9)
        player["coins"] -= loss
        embed.add_field(name="💸 Result", value=f"Lost {loss:,} coins", inline=True)
    elif result == 'orange':
        # Lose 75%
        loss = int(bet * 0.75)
        player["coins"] -= loss
        embed.add_field(name="💸 Result", value=f"Lost {loss:,} coins", inline=True)
    elif result == 'red':
        # Lose 100% but get life potion
        loss = bet
        player["coins"] -= loss
        if "life potion" not in player["inventory"]:
            player["inventory"]["life potion"] = 0
        player["inventory"]["life potion"] += 1
        embed.add_field(name="💸 Result", value=f"Lost {loss:,} coins", inline=True)
        embed.add_field(name="🎁 Bonus", value="Gained 1 Life Potion!", inline=True)
    elif result == 'yellow':
        # Lose 100% but get lottery ticket
        loss = bet
        player["coins"] -= loss
        embed.add_field(name="💸 Result", value=f"Lost {loss:,} coins", inline=True)
        embed.add_field(name="🎁 Bonus", value="Gained 1 Lottery Ticket!", inline=True)
    elif result == 'green':
        # Win 100%
        winnings = bet
        player["coins"] += winnings
        embed.add_field(name="🎉 Result", value=f"Won {winnings:,} coins!", inline=True)
    elif result == 'purple':
        # Win 10x
        winnings = bet * 10
        player["coins"] += winnings
        embed.add_field(name="🎉 JACKPOT!", value=f"Won {winnings:,} coins! (10x)", inline=True)

    embed.add_field(name="Balance", value=f"{player['coins']:,} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='bigdice')
async def big_dice(ctx, bet_amount=None):
    """Roll the big dice (Area 14+)"""
    global big_dice_pot

    player = get_player(ctx.author.id)
    if player is None:
        await ctx.send("🎮 Welcome to disRPG! Please use `rpgs start` to create your adventure account first!")
        return

    if not check_command_unlocked(player["area"], "big dice"):
        await ctx.send("🔒 Big Dice is unlocked in Area 14!")
        return

    if not bet_amount:
        await ctx.send("Please specify a bet amount! Example: `rpgs bigdice 1000000`")
        return

    try:
        bet = int(bet_amount)
        if bet <= 0:
            await ctx.send("Bet amount must be positive!")
            return
    except ValueError:
        await ctx.send("Invalid bet amount!")
        return

    if player["coins"] < bet:
        await ctx.send(f"You don't have {bet:,} coins!")
        return

    # Calculate dice sides based on bet amount and pot size
    # More bet = fewer sides, larger pot = more sides
    base_sides = 100
    bet_factor = max(0.5, 1 - (bet / 10000000))  # Reduce sides for larger bets
    pot_factor = 1 + (big_dice_pot / 1000000000)  # Increase sides for larger pot

    dice_sides = int(base_sides * bet_factor * pot_factor)
    dice_sides = max(10, min(dice_sides, 1000))  # Keep between 10-1000

    # Roll dice
    roll = random.randint(1, dice_sides)

    embed = discord.Embed(title="🎲 Big Dice", color=0x8b0000)
    embed.add_field(name="Dice Sides", value=f"{dice_sides}", inline=True)
    embed.add_field(name="Your Roll", value=f"🎲 {roll}", inline=True)
    embed.add_field(name="Current Pot", value=f"{big_dice_pot:,} coins", inline=True)

    if 1 <= roll <= 6:
        # Win the pot!
        winnings = big_dice_pot
        profit = winnings - bet
        player["coins"] += profit
        big_dice_pot = 0  # Reset pot

        embed.add_field(name="🎉 JACKPOT!", value=f"You won the pot!", inline=False)
        embed.add_field(name="Pot Won", value=f"{winnings:,} coins", inline=True)
        embed.add_field(name="Net Profit", value=f"{profit:,} coins", inline=True)
        embed.color = 0x00ff00
    else:
        # Lose - add half bet to pot
        player["coins"] -= bet
        pot_addition = bet // 2
        big_dice_pot += pot_addition

        embed.add_field(name="💸 No Win", value="Roll 1-6 to win the pot!", inline=False)
        embed.add_field(name="Lost", value=f"{bet:,} coins", inline=True)
        embed.add_field(name="Added to Pot", value=f"{pot_addition:,} coins", inline=True)
        embed.color = 0xff0000

    embed.add_field(name="New Pot Size", value=f"{big_dice_pot:,} coins", inline=True)
    embed.add_field(name="Your Balance", value=f"{player['coins']:,} coins", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


# Add fruit drops for pickup commands
FRUIT_DROPS = {
    "area_3_plus": {
        "Apple": {"chance": 60, "amount": [1, 3]},
        "Banana": {"chance": 40, "amount": [1, 2]},
        "Watermelon": {"chance": 5, "amount": [1, 1]}  # Rare drop
    }
}

# Mining drops
MINING_DROPS = {
    "Ruby": {
        "mine": {"chance": 2, "amount": [1, 1]},
        "pickaxe": {"chance": 3, "amount": [1, 1]},
        "drill": {"chance": 5, "amount": [1, 1]},
        "dynamite": {"chance": 8, "amount": [1, 1]}
    }
}


@bot.command(name='bowsaw')
async def bowsaw(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "bowsaw"):
        await ctx.send("🔒 Bowsaw is unlocked in Area 6!")
        return

    # Enhanced chopping with bowsaw - even better amounts
    drops_received = []
    area = player["area"]

    # Bowsaw amounts: Wooden Log 6-10, Epic Log 3-5, Super Log 2-3, Mega Log 1-2, others 1
    bowsaw_multipliers = {
        "Wooden Log": [6, 10],
        "Epic Log": [3, 5],
        "Super Log": [2, 3],
        "Mega Log": [1, 2],
        "HYPER Log": [1, 1],
        "ULTRA Log": [1, 1],
        "ULTIMATE Log": [1, 1]
    }

    # Roll for each possible log type with bowsaw bonuses
    for log_type, drop_data in CHOPPING_DROPS.items():
        chance = 0

        # Determine chance based on area (same as other chop commands)
        if log_type == "Wooden Log":
            chance = drop_data["area_1"]["chance"]
        elif log_type == "Epic Log":
            if area == 1:
                chance = drop_data["area_1"]["chance"]
            else:
                chance = drop_data["area_2_plus"]["chance"]
        elif log_type == "Super Log":
            if area >= 2:
                if area <= 3:
                    chance = drop_data["area_2_3"]["chance"]
                else:
                    chance = drop_data["area_4_plus"]["chance"]
        elif log_type == "Mega Log":
            if area >= 4:
                if area <= 5:
                    chance = drop_data["area_4_5"]["chance"]
                else:
                    chance = drop_data["area_6_plus"]["chance"]
        elif log_type == "HYPER Log":
            if area >= 6:
                if area <= 8:
                    chance = drop_data["area_6_8"]["chance"]
                else:
                    chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTRA Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTIMATE Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]

        # Roll for drop with bowsaw amounts
        if chance > 0 and random.random() * 100 < chance:
            amount_range = bowsaw_multipliers.get(log_type, [1, 1])
            quantity = random.randint(amount_range[0], amount_range[1])
            if log_type not in player["inventory"]:
                player["inventory"][log_type] = 0
            player["inventory"][log_type] += quantity
            drops_received.append(f"{log_type} x{quantity}")

    exp_gain = random.randint(20, 45)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🪚 Bowsaw Chopping Result", color=0x8b4513)

    if drops_received:
        embed.add_field(name="Chopped", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No logs obtained this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Bowsaw gives even more materials!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='chainsaw')
async def chainsaw(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "chainsaw"):
        await ctx.send("🔒 Chainsaw is unlocked in Area 9!")
        return

    # Enhanced chopping with chainsaw - maximum amounts
    drops_received = []
    area = player["area"]

    # Chainsaw amounts: Wooden Log 8-15, Epic Log 4-7, Super Log 3-5, Mega Log 2, others 1
    chainsaw_multipliers = {
        "Wooden Log": [8, 15],
        "Epic Log": [4, 7],
        "Super Log": [3, 5],
        "Mega Log": [2, 2],
        "HYPER Log": [1, 1],
        "ULTRA Log": [1, 1],
        "ULTIMATE Log": [1, 1]
    }

    # Roll for each possible log type with chainsaw bonuses
    for log_type, drop_data in CHOPPING_DROPS.items():
        chance = 0

        # Determine chance based on area (same as other chop commands)
        if log_type == "Wooden Log":
            chance = drop_data["area_1"]["chance"]
        elif log_type == "Epic Log":
            if area == 1:
                chance = drop_data["area_1"]["chance"]
            else:
                chance = drop_data["area_2_plus"]["chance"]
        elif log_type == "Super Log":
            if area >= 2:
                if area <= 3:
                    chance = drop_data["area_2_3"]["chance"]
                else:
                    chance = drop_data["area_4_plus"]["chance"]
        elif log_type == "Mega Log":
            if area >= 4:
                if area <= 5:
                    chance = drop_data["area_4_5"]["chance"]
                else:
                    chance = drop_data["area_6_plus"]["chance"]
        elif log_type == "HYPER Log":
            if area >= 6:
                if area <= 8:
                    chance = drop_data["area_6_8"]["chance"]
                else:
                    chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTRA Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]
        elif log_type == "ULTIMATE Log":
            if area >= 9:
                chance = drop_data["area_9_plus"]["chance"]

        # Roll for drop with chainsaw amounts
        if chance > 0 and random.random() * 100 < chance:
            amount_range = chainsaw_multipliers.get(log_type, [1, 1])
            quantity = random.randint(amount_range[0], amount_range[1])
            if log_type not in player["inventory"]:
                player["inventory"][log_type] = 0
            player["inventory"][log_type] += quantity

            # Add emojis for different log types
            log_emojis = {
                "Wooden Log": "🪵",
                "Epic Log": "📜",
                "Super Log": "🟫",
                "Mega Log": "🟤",
                "HYPER Log": "🟨",
                "ULTRA Log": "🟪",
                "ULTIMATE Log": "⭐"
            }
            emoji = log_emojis.get(log_type, "🪵")
            drops_received.append(f"{emoji} **{log_type}** x{quantity}")

    exp_gain = random.randint(25, 55)
    player["exp"] += exp_gain

    # Create beautiful result message with chainsaw intensity
    result_message = f"**{ctx.author.display_name}** is chopping with **THREE CHAINSAW**! One of them in each hand, and the last one in their mouth\n"

    if drops_received:
        result_message += f"**{ctx.author.display_name}** got {', '.join(drops_received)}\n"
    else:
        result_message += f"**{ctx.author.display_name}** didn't find any usable wood this time\n"

    result_message += f"Earned **{exp_gain:,}** XP"

    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='boat')
async def boat(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "boat"):
        await ctx.send("🔒 Boat is unlocked in Area 6!")
        return

    # Enhanced fishing with boat - better amounts and chances
    drops_received = []
    area = player["area"]

    # Boat amounts: Normie Fish 6-11, Golden Fish 3-7, others 1
    boat_amounts = {
        "Normie Fish": [6, 11],
        "Golden Fish": [3, 7],
        "EPIC Fish": [1, 1],
        "SUPER Fish": [1, 1]
    }

    # Boat has even better EPIC Fish chances
    if area == 1:
        drop_table = FISHING_DROPS["area_1"]
    else:
        # Modified chances for boat
        drop_table = {
            "Normie Fish": {"chance": 72, "amount": [6, 11]},
            "Golden Fish": {"chance": 27.1, "amount": [3, 7]},
            "EPIC Fish": {"chance": 0.9, "amount": [1, 1]},
            "SUPER Fish": {"chance": 0.03, "amount": [1, 1]}
        }

    # Roll for each fish type
    for fish_type, drop_data in drop_table.items():
        if random.random() * 100 < drop_data["chance"]:
            amount_range = boat_amounts.get(fish_type, drop_data["amount"])
            quantity = random.randint(amount_range[0], amount_range[1])
            if fish_type not in player["inventory"]:
                player["inventory"][fish_type] = 0
            player["inventory"][fish_type] += quantity

            # Mark rare fish
            if fish_type in ["EPIC Fish", "SUPER Fish"]:
                drops_received.append(f"🌟 {fish_type} x{quantity}")
            else:
                drops_received.append(f"{fish_type} x{quantity}")

    exp_gain = random.randint(18, 40)
    coin_gain = random.randint(12, 35)
    player["exp"] += exp_gain
    player["coins"] += coin_gain

    embed = discord.Embed(title="⛵ Boat Fishing Result", color=0x4169e1)

    if drops_received:
        embed.add_field(name="Caught", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="Nothing caught this time", inline=True)

    embed.add_field(name="Rewards", value=f"EXP: +{exp_gain}\nCoins: +{coin_gain}", inline=True)
    embed.add_field(name="Bonus", value="Boat catches even more fish!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='bigboat')
async def bigboat(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "bigboat"):
        await ctx.send("🔒 Big Boat is unlocked in Area 9!")
        return

    # Enhanced fishing with bigboat - maximum amounts and chances
    drops_received = []
    area = player["area"]

    # Bigboat amounts: Normie Fish 8-16, Golden Fish 5-9, others 1
    bigboat_amounts = {
        "Normie Fish": [8, 16],
        "Golden Fish": [5, 9],
        "EPIC Fish": [1, 1],
        "SUPER Fish": [1, 1]
    }

    # Bigboat has best EPIC Fish chances
    if area == 1:
        drop_table = FISHING_DROPS["area_1"]
    else:
        # Modified chances for bigboat
        drop_table = {
            "Normie Fish": {"chance": 72, "amount": [8, 16]},
            "Golden Fish": {"chance": 26.8, "amount": [5, 9]},
            "EPIC Fish": {"chance": 1.2, "amount": [1, 1]},
            "SUPER Fish": {"chance": 0.04, "amount": [1, 1]}
        }

    # Roll for each fish type
    for fish_type, drop_data in drop_table.items():
        if random.random() * 100 < drop_data["chance"]:
            amount_range = bigboat_amounts.get(fish_type, drop_data["amount"])
            quantity = random.randint(amount_range[0], amount_range[1])
            if fish_type not in player["inventory"]:
                player["inventory"][fish_type] = 0
            player["inventory"][fish_type] += quantity

            # Mark rare fish
            if fish_type in ["EPIC Fish", "SUPER Fish"]:
                drops_received.append(f"🌟 {fish_type} x{quantity}")
            else:
                drops_received.append(f"{fish_type} x{quantity}")

    exp_gain = random.randint(25, 50)
    coin_gain = random.randint(18, 45)
    player["exp"] += exp_gain
    player["coins"] += coin_gain

    embed = discord.Embed(title="🚢 Big Boat Fishing Result", color=0x4169e1)

    if drops_received:
        embed.add_field(name="Caught", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="Nothing caught this time", inline=True)

    embed.add_field(name="Rewards", value=f"EXP: +{exp_gain}\nCoins: +{coin_gain}", inline=True)
    embed.add_field(name="Bonus", value="Big Boat catches maximum fish!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='pickup')
async def pickup(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "pickup"):
        await ctx.send("🔒 Pickup is unlocked in Area 3!")
        return

    # Fruit gathering
    drops_received = []

    # Roll for each fruit type
    for fruit_type, drop_data in FRUIT_DROPS["area_3_plus"].items():
        if random.random() * 100 < drop_data["chance"]:
            quantity = random.randint(drop_data["amount"][0], drop_data["amount"][1])
            if fruit_type not in player["inventory"]:
                player["inventory"][fruit_type] = 0
            player["inventory"][fruit_type] += quantity

            if fruit_type == "Watermelon":
                drops_received.append(f"🍉 {fruit_type} x{quantity} (RARE!)")
            else:
                drops_received.append(f"{fruit_type} x{quantity}")

    exp_gain = random.randint(10, 25)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🍎 Fruit Pickup Result", color=0xff6347)

    if drops_received:
        embed.add_field(name="Collected", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No fruits found this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='ladder')
async def ladder(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "ladder"):
        await ctx.send("🔒 Ladder is unlocked in Area 4!")
        return

    # Enhanced fruit gathering with ladder
    drops_received = []

    # Ladder gives 1.5x more fruits
    for fruit_type, drop_data in FRUIT_DROPS["area_3_plus"].items():
        if random.random() * 100 < drop_data["chance"]:
            base_amount = random.randint(drop_data["amount"][0], drop_data["amount"][1])
            quantity = int(base_amount * 1.5) + 1
            if fruit_type not in player["inventory"]:
                player["inventory"][fruit_type] = 0
            player["inventory"][fruit_type] += quantity

            if fruit_type == "Watermelon":
                drops_received.append(f"🍉 {fruit_type} x{quantity} (RARE!)")
            else:
                drops_received.append(f"{fruit_type} x{quantity}")

    exp_gain = random.randint(15, 35)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🪜 Ladder Fruit Pickup Result", color=0xff6347)

    if drops_received:
        embed.add_field(name="Collected", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No fruits found this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Ladder gets more fruits!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='tractor')
async def tractor(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "tractor"):
        await ctx.send("🔒 Tractor is unlocked in Area 8!")
        return

    # Enhanced fruit gathering with tractor
    drops_received = []

    # Tractor gives 2x more fruits
    for fruit_type, drop_data in FRUIT_DROPS["area_3_plus"].items():
        if random.random() * 100 < drop_data["chance"]:
            base_amount = random.randint(drop_data["amount"][0], drop_data["amount"][1])
            quantity = base_amount * 2 + 1
            if fruit_type not in player["inventory"]:
                player["inventory"][fruit_type] = 0
            player["inventory"][fruit_type] += quantity

            if fruit_type == "Watermelon":
                drops_received.append(f"🍉 {fruit_type} x{quantity} (RARE!)")
            else:
                drops_received.append(f"{fruit_type} x{quantity}")

    exp_gain = random.randint(20, 45)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🚜 Tractor Fruit Collection Result", color=0xff6347)

    if drops_received:
        embed.add_field(name="Collected", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No fruits found this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Tractor collects even more fruits!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='greenhouse')
async def greenhouse(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "greenhouse"):
        await ctx.send("🔒 Greenhouse is unlocked in Area 11!")
        return

    # Enhanced fruit gathering with greenhouse - maximum
    drops_received = []

    # Greenhouse gives 3x more fruits
    for fruit_type, drop_data in FRUIT_DROPS["area_3_plus"].items():
        if random.random() * 100 < drop_data["chance"]:
            base_amount = random.randint(drop_data["amount"][0], drop_data["amount"][1])
            quantity = base_amount * 3 + 2
            if fruit_type not in player["inventory"]:
                player["inventory"][fruit_type] = 0
            player["inventory"][fruit_type] += quantity

            if fruit_type == "Watermelon":
                drops_received.append(f"🍉 {fruit_type} x{quantity} (RARE!)")
            else:
                drops_received.append(f"{fruit_type} x{quantity}")

    exp_gain = random.randint(30, 60)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🏡 Greenhouse Fruit Collection Result", color=0xff6347)

    if drops_received:
        embed.add_field(name="Collected", value="\n".join(drops_received), inline=True)
    else:
        embed.add_field(name="Result", value="No fruits found this time", inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Greenhouse gives maximum fruits!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='mine')
async def mine_command(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "mine"):
        await ctx.send("🔒 Mine is unlocked in Area 5!")
        return

    # Mining for coins and rubies
    drops_received = []

    # Base coin reward
    coin_gain = random.randint(50, 150) + (player["area"] * 10)
    player["coins"] += coin_gain

    # Check for ruby drop
    ruby_data = MINING_DROPS["Ruby"]["mine"]
    if random.random() * 100 < ruby_data["chance"]:
        quantity = random.randint(ruby_data["amount"][0], ruby_data["amount"][1])
        if "Ruby" not in player["inventory"]:
            player["inventory"]["Ruby"] = 0
        player["inventory"]["Ruby"] += quantity
        drops_received.append(f"💎 **Ruby** x{quantity}")

    exp_gain = random.randint(15, 30)
    player["exp"] += exp_gain

    # Create beautiful result message
    actions = [
        "is mining deep in the cave! Their pickaxe strikes the rock with determination",
        "swings their pickaxe with power! Sparks fly as metal meets stone",
        "is working hard in the mines! The sound of mining echoes through the tunnels",
        "digs deeper into the earth! Precious materials await in the darkness"
    ]
    action = random.choice(actions)

    result_message = f"**{ctx.author.display_name}** {action}\n"
    result_message += f"**{ctx.author.display_name}** found **{coin_gain:,}** 🪙 coins"

    if drops_received:
        result_message += f" and {', '.join(drops_received)}"

    result_message += f"\nEarned **{exp_gain:,}** XP"

    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='pickaxe')
async def pickaxe(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "pickaxe"):
        await ctx.send("🔒 Pickaxe is unlocked in Area 6!")
        return

    # Enhanced mining with pickaxe
    drops_received = []

    # Better coin reward
    coin_gain = random.randint(80, 200) + (player["area"] * 15)
    player["coins"] += coin_gain

    # Better ruby chance
    ruby_data = MINING_DROPS["Ruby"]["pickaxe"]
    if random.random() * 100 < ruby_data["chance"]:
        quantity = random.randint(ruby_data["amount"][0], ruby_data["amount"][1])
        if "Ruby" not in player["inventory"]:
            player["inventory"]["Ruby"] = 0
        player["inventory"]["Ruby"] += quantity
        drops_received.append(f"💎 Ruby x{quantity}")

    exp_gain = random.randint(20, 40)
    player["exp"] += exp_gain

    embed = discord.Embed(title="⛏️ Pickaxe Mining Result", color=0x8b4513)
    embed.add_field(name="Coins Found", value=f"{coin_gain} coins", inline=True)

    if drops_received:
        embed.add_field(name="Rare Drops", value="\n".join(drops_received), inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Pickaxe finds more coins and rubies!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='drill')
async def drill(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "drill"):
        await ctx.send("🔒 Drill is unlocked in Area 10!")
        return

    # Enhanced mining with drill
    drops_received = []

    # Even better coin reward
    coin_gain = random.randint(120, 300) + (player["area"] * 25)
    player["coins"] += coin_gain

    # Even better ruby chance
    ruby_data = MINING_DROPS["Ruby"]["drill"]
    if random.random() * 100 < ruby_data["chance"]:
        quantity = random.randint(ruby_data["amount"][0], ruby_data["amount"][1])
        if "Ruby" not in player["inventory"]:
            player["inventory"]["Ruby"] = 0
        player["inventory"]["Ruby"] += quantity
        drops_received.append(f"💎 Ruby x{quantity}")

    exp_gain = random.randint(30, 50)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🔩 Drill Mining Result", color=0x8b4513)
    embed.add_field(name="Coins Found", value=f"{coin_gain} coins", inline=True)

    if drops_received:
        embed.add_field(name="Rare Drops", value="\n".join(drops_received), inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Drill finds even more coins and rubies!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='dynamite')
async def dynamite(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "dynamite"):
        await ctx.send("🔒 Dynamite is unlocked in Area 12!")
        return

    # Maximum mining with dynamite
    drops_received = []

    # Maximum coin reward
    coin_gain = random.randint(200, 500) + (player["area"] * 40)
    player["coins"] += coin_gain

    # Best ruby chance
    ruby_data = MINING_DROPS["Ruby"]["dynamite"]
    if random.random() * 100 < ruby_data["chance"]:
        quantity = random.randint(ruby_data["amount"][0], ruby_data["amount"][1])
        if "Ruby" not in player["inventory"]:
            player["inventory"]["Ruby"] = 0
        player["inventory"]["Ruby"] += quantity
        drops_received.append(f"💎 Ruby x{quantity}")

    exp_gain = random.randint(40, 70)
    player["exp"] += exp_gain

    embed = discord.Embed(title="🧨 Dynamite Mining Result", color=0x8b4513)
    embed.add_field(name="Coins Found", value=f"{coin_gain} coins", inline=True)

    if drops_received:
        embed.add_field(name="Rare Drops", value="\n".join(drops_received), inline=True)

    embed.add_field(name="EXP Gained", value=exp_gain, inline=True)
    embed.add_field(name="Bonus", value="Dynamite finds maximum coins and rubies!", inline=False)

    if level_up_check(player):
        embed.add_field(name="Level Up!", value=f"🎊 You reached level {player['level']}!", inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='farm')
async def farm(ctx):
    player = get_player(ctx.author.id)

    if not check_command_unlocked(player["area"], "farm"):
        await ctx.send("🔒 Farm is unlocked in Area 4!")
        return

    # Check if player has seeds
    if player["inventory"].get("seed", 0) <= 0:
        await ctx.send("You need seeds to farm! Buy them from the shop with `rpg buy seed`")
        return

    # Consume one seed
    player["inventory"]["seed"] -= 1
    if player["inventory"]["seed"] <= 0:
        del player["inventory"]["seed"]

    # Farm results
    drops_received = []

    # Potato is most common
    if random.random() * 100 < 70:
        quantity = random.randint(12, 20)
        if "Potato" not in player["inventory"]:
            player["inventory"]["Potato"] = 0
        player["inventory"]["Potato"] += quantity
        drops_received.append(f"🥔 **Potato** x{quantity}")

    # Carrot is less common
    if random.random() * 100 < 30:
        quantity = random.randint(5, 12)
        if "Carrot" not in player["inventory"]:
            player["inventory"]["Carrot"] = 0
        player["inventory"]["Carrot"] += quantity
        drops_received.append(f"🥕 **Carrot** x{quantity}")

    # Bread is rare
    if random.random() * 100 < 10:
        quantity = random.randint(1, 3)
        if "Bread" not in player["inventory"]:
            player["inventory"]["Bread"] = 0
        player["inventory"]["Bread"] += quantity
        drops_received.append(f"🍞 **Bread** x{quantity}")

    exp_gain = random.randint(15, 35)
    player["exp"] += exp_gain

    # Create beautiful result message
    result_message = f"**{ctx.author.display_name}** plants 🌱 **seed** in the ground...\n"

    if drops_received:
        total_items = len([item for item in drops_received])
        result_message += f"**{total_items}** 🥔 potato have grown from the seed\n"
        result_message += f"Earned **{exp_gain:,}** XP"
    else:
        result_message += f"The seed didn't grow anything this time\nEarned **{exp_gain:,}** XP"

    if level_up_check(player):
        result_message += f"\n🎊 **LEVEL UP!** You reached level **{player['level']}**!"

    save_player_data()
    await ctx.send(result_message)


@bot.command(name='unlocks')
async def unlocks(ctx):
    player = get_player(ctx.author.id)

    embed = discord.Embed(title="🔓 Command Unlocks", description=f"Your current area: {player['area']}", color=0x9932cc)

    # Show unlocked commands
    unlocked_commands = get_unlocked_commands(player["area"])
    if unlocked_commands:
        embed.add_field(name="✅ Unlocked Commands", value=", ".join(unlocked_commands), inline=False)

    # Show next few unlocks
    next_unlocks_text = ""
    for area in range(player["area"] + 1, min(player["area"] + 4, 16)):
        if area in AREA_UNLOCKS:
            commands = ", ".join(AREA_UNLOCKS[area])
            next_unlocks_text += f"**Area {area}:** {commands}\n"

    if next_unlocks_text:
        embed.add_field(name="🔒 Upcoming Unlocks", value=next_unlocks_text, inline=False)

    embed.add_field(name="Progress", value=f"Keep advancing areas to unlock more commands!", inline=False)

    await ctx.send(embed=embed)


# Time Travel System
def calculate_tt_bonuses(tt_count):
    """Calculate time travel bonuses"""
    if tt_count == 0:
        return {"exp": 0, "duel_exp": 0, "drops": 0, "working": 0}

    exp_bonus = (99 + tt_count) * tt_count // 2
    duel_exp_bonus = (99 + tt_count) * tt_count // 4
    drops_bonus = (49 + tt_count) * tt_count // 2
    working_bonus = (49 + tt_count) * tt_count // 2

    return {
        "exp": exp_bonus,
        "duel_exp": duel_exp_bonus,
        "drops": drops_bonus,
        "working": working_bonus
    }


def calculate_stt_score(player):
    """Calculate Super Time Travel score"""
    score = 0
    inventory = player["inventory"]

    # Level score (including stats from levels)
    score += player["level"]

    # Item scores
    score += inventory.get("Ruby", 0) // 25
    score += inventory.get("Dragon Scale", 0) // 2
    score += inventory.get("Chip", 0) // 4
    score += inventory.get("Mermaid Hair", 0)
    score += inventory.get("Unicorn Horn", 0) // 7
    score += inventory.get("Zombie Eye", 0) // 10
    score += inventory.get("Wolf Skin", 0) // 20
    score += inventory.get("Watermelon", 0) // 12
    score += inventory.get("Bread", 0) // 25
    score += inventory.get("Carrot", 0) // 30
    score += inventory.get("Potato", 0) // 35
    score += inventory.get("Seeds", 0) // 2500

    # Lootbox scores
    score += inventory.get("Common Lootbox", 0) * 0.05
    score += inventory.get("Uncommon Lootbox", 0) * 0.1
    score += inventory.get("Rare Lootbox", 0) * 0.15
    score += inventory.get("EPIC Lootbox", 0) * 0.2
    score += inventory.get("EDGY Lootbox", 0) * 0.25
    score += inventory.get("OMEGA Lootbox", 0) * 2.5
    score += inventory.get("GODLY Lootbox", 0) * 25

    # Ultra-Omega gear bonus
    if "ULTRA-OMEGA Sword" in inventory or "ULTRA-OMEGA Armor" in inventory:
        score += 155.5

    return int(score)


def get_tt_titles(tt_count):
    """Get available titles based on time travel count"""
    titles = []
    if tt_count >= 1:
        titles.append("Time traveler")
    if tt_count >= 2:
        titles.append("One time wasn't enough")
    if tt_count >= 5:
        titles.append("I spend too much time here")
    if tt_count >= 10:
        titles.append("OOF")
    if tt_count >= 25:
        titles.append("OOFMEGA")
    if tt_count >= 50:
        titles.append("GOOFDLY")
    if tt_count >= 75:
        titles.append("VOOFID")
    return titles


def get_max_dungeon(tt_count):
    """Get maximum dungeon based on time travel count"""
    if tt_count == 0:
        return 10
    elif tt_count <= 2:
        return 11
    elif tt_count <= 4:
        return 12
    elif tt_count <= 9:
        return 13
    elif tt_count <= 24:
        return 14
    else:
        return 15


@bot.command(name='timetravel', aliases=['tt'])
async def time_travel(ctx, confirm=None):
    player = get_player(ctx.author.id)

    # Check if time travel is unlocked
    if player["area"] < 11:
        await ctx.send("🔒 Time Travel is unlocked when you first reach Area 11!")
        return

    # Determine minimum area required for time travel based on TT count
    tt_count = player.get("time_travels", 0)
    if tt_count == 0:
        min_area = 11
    elif tt_count <= 2:
        min_area = 12
    elif tt_count <= 4:
        min_area = 13
    elif tt_count <= 9:
        min_area = 14
    elif tt_count <= 24:
        min_area = 15
    else:
        min_area = 16

    if player["area"] < min_area:
        await ctx.send(f"You need to reach Area {min_area} to time travel with {tt_count} previous time travels!")
        return

    if confirm != "confirm":
        # Show time travel info
        current_bonuses = calculate_tt_bonuses(tt_count)
        next_bonuses = calculate_tt_bonuses(tt_count + 1)

        embed = discord.Embed(title="⏰ Time Travel", description=f"Current Time Travels: {tt_count}", color=0x9932cc)

        # Current bonuses
        if tt_count > 0:
            embed.add_field(name="Current Bonuses",
                            value=f"EXP: +{current_bonuses['exp']}%\nDrop Chance: +{current_bonuses['drops']}%\nWorking Items: +{current_bonuses['working']}%",
                            inline=True)

        # Next bonuses
        embed.add_field(name="Next TT Bonuses",
                        value=f"EXP: +{next_bonuses['exp']}%\nDrop Chance: +{next_bonuses['drops']}%\nWorking Items: +{next_bonuses['working']}%",
                        inline=True)

        # What gets reset
        embed.add_field(name="⚠️ Gets Reset",
                        value="• Level (back to 1)\n• Area (back to 1)\n• Equipment\n• Most inventory items\n• HP/Stats",
                        inline=False)

        # What stays
        embed.add_field(name="✅ Stays",
                        value="• Coins (all types)\n• Horse\n• Professions\n• Pets\n• Dragon Essences\n• Arena Cookies\n• Epic Shop items",
                        inline=False)

        # Max dungeon access
        max_dungeon = get_max_dungeon(tt_count + 1)
        embed.add_field(name="Dungeon Access", value=f"After TT: Max Dungeon {max_dungeon}", inline=True)

        # Titles
        available_titles = get_tt_titles(tt_count + 1)
        if available_titles:
            embed.add_field(name="Titles Available", value=", ".join(available_titles), inline=False)

        embed.add_field(name="⚠️ Warning",
                        value="This action cannot be undone!\nUse `rpg tt confirm` to proceed",
                        inline=False)

        await ctx.send(embed=embed)
        return

    # Execute time travel
    # Save what stays
    coins = player["coins"]
    horse = player.get("horse", None)
    professions = player.get("job_levels", {"mining": 1, "fishing": 1, "woodcutting": 1, "crafter": 1})
    pets = player.get("pets", {})
    dragon_essences = player["inventory"].get("Dragon Essence", 0)
    time_dragon_essences = player["inventory"].get("Time Dragon Essence", 0)
    arena_cookies = player.get("arena_cookies", 0)
    epic_shop_items = player.get("epic_shop_items", {})

    # Reset player
    player["level"] = 1
    player["exp"] = 0
    player["hp"] = 100
    player["max_hp"] = 100
    player["area"] = 1
    player["weapon"] = "Wooden Sword"
    player["armor"] = None
    player["inventory"] = {"Wooden Sword": 1, "Wooden Log": 50, "Normie Fish": 20, "Apple": 10}
    player["last_hunt"] = 0
    player["last_adventure"] = 0
    player["enchants"] = {}
    player["cooking_boosts"] = {"attack_boost": 0, "defense_boost": 0, "hp_boost": 0}

    # Restore what stays
    player["coins"] = coins
    if horse:
        player["horse"] = horse
    player["job_levels"] = professions
    if pets:
        player["pets"] = pets
    if dragon_essences > 0:
        player["inventory"]["Dragon Essence"] = dragon_essences
    if time_dragon_essences > 0:
        player["inventory"]["Time Dragon Essence"] = time_dragon_essences
    if arena_cookies > 0:
        player["arena_cookies"] = arena_cookies
    if epic_shop_items:
        player["epic_shop_items"] = epic_shop_items

    # Increment time travel count
    player["time_travels"] = tt_count + 1

    # Check for new titles
    if "titles" not in player:
        player["titles"] = []

    new_title = None
    if player["time_travels"] in TT_TITLES:
        title = TT_TITLES[player["time_travels"]]
        if title not in player["titles"]:
            player["titles"].append(title)
            new_title = title

    # Show result
    new_bonuses = calculate_tt_bonuses(player["time_travels"])

    embed = discord.Embed(title="⏰ Time Travel Complete!", color=0x00ff00)
    embed.add_field(name="Time Travels", value=f"{player['time_travels']}", inline=True)
    embed.add_field(name="New Bonuses",
                    value=f"EXP: +{new_bonuses['exp']}%\nDrop Chance: +{new_bonuses['drops']}%\nWorking Items: +{new_bonuses['working']}%",
                    inline=True)

    max_dungeon = get_max_dungeon(player["time_travels"])
    embed.add_field(name="Max Dungeon", value=f"Dungeon {max_dungeon}", inline=True)

    if new_title:
        embed.add_field(name="🏆 New Title Unlocked!", value=f"**{new_title}**", inline=False)

    available_titles = [title for tt, title in TT_TITLES.items() if player["time_travels"] >= tt]
    if available_titles:
        embed.add_field(name="Available Titles", value=", ".join(available_titles[-3:]), inline=False)

    embed.add_field(name="Status",
                    value="You are back at Level 1, Area 1. Your adventure begins anew with permanent bonuses!",
                    inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='supertimetravel', aliases=['stt'])
async def super_time_travel(ctx, confirm=None):
    player = get_player(ctx.author.id)

    # Check if STT is unlocked
    if player.get("time_travels", 0) < 25 or "TIME KEY" not in player["inventory"]:
        await ctx.send("🔒 Super Time Travel requires 25+ Time Travels and the TIME KEY from Dungeon 15!")
        return

    if confirm != "confirm":
        # Show STT options and score
        score = calculate_stt_score(player)

        embed = discord.Embed(title="🌌 Super Time Travel", description=f"Your STT Score: {score}", color=0x4b0082)

        # STT Rewards
        rewards_text = """**Life** - Start with +25 HP (50 points)
**AT** - Start with +50 ATK (400 points)
**DEF** - Start with +50 DEF (400 points)
**Area 2** - Start in Area 2 (2000 points)
**Area 3** - Start in Area 3 (4500 points)
**Ultra Logs** - Start with 10 Ultra Logs (1750 points)
**Drops** - Start with 35 of each Mob Drop (400 points)
**OMEGA Lootbox** - Start with OMEGA Lootbox (500 points)
**GODLY Lootbox** - Start with GODLY Lootbox (6500 points)
**Pet I** - Start with TIER I pet (300 points)
**Pet III** - Start with TIER III pet (1500 points)
**Skilled Pet** - Start with TIER I pet + skill (4500 points)"""

        embed.add_field(name="Available Rewards", value=rewards_text, inline=False)

        embed.add_field(name="⚠️ Important",
                        value="• You must choose ONE reward\n• Your inventory will be used for score calculation\n• This cannot be undone!\nUse `rpg stt confirm` to proceed",
                        inline=False)

        await ctx.send(embed=embed)
        return

    # For now, execute basic STT (reward selection can be added later)
    score = calculate_stt_score(player)

    # Reset everything like regular TT but with score benefits
    coins = player["coins"]
    horse = player.get("horse", None)
    professions = player.get("job_levels", {"mining": 1, "fishing": 1, "woodcutting": 1, "crafter": 1})
    pets = player.get("pets", {})
    time_travels = player.get("time_travels", 0)

    # Reset player
    player["level"] = 1
    player["exp"] = 0
    player["hp"] = 100
    player["max_hp"] = 100
    player["area"] = 1
    player["weapon"] = "Wooden Sword"
    player["armor"] = None
    player["inventory"] = {"Wooden Sword": 1, "Wooden Log": 50, "Normie Fish": 20, "Apple": 10}
    player["last_hunt"] = 0
    player["last_adventure"] = 0
    player["enchants"] = {}
    player["cooking_boosts"] = {"attack_boost": 0, "defense_boost": 0, "hp_boost": 0}

    # Restore persistent items
    player["coins"] = coins
    if horse:
        player["horse"] = horse
    player["job_levels"] = professions
    if pets:
        player["pets"] = pets
    player["time_travels"] = time_travels + 1
    player["stt_score"] = score

    embed = discord.Embed(title="🌌 Super Time Travel Complete!", color=0x4b0082)
    embed.add_field(name="STT Score Used", value=f"{score}", inline=True)
    embed.add_field(name="Time Travels", value=f"{player['time_travels']}", inline=True)
    embed.add_field(name="Status", value="Super Time Travel completed! Your adventure begins with enhanced benefits!",
                    inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='drops')
async def drops_info(ctx, category=None):
    player = get_player(ctx.author.id)

    if category == "hunt" or category == "mob":
        embed = discord.Embed(title="🗡️ Hunt Drops", description=f"Base hunt drop chance: 7%", color=0xff0000)

        hunt_drops_text = ""
        for mob, drop_data in MOB_DROPS.items():
            hunt_drops_text += f"**{mob}** → {drop_data['item']}\n"
            hunt_drops_text += f"Chance: {drop_data['chance']}% | Sell: {drop_data['sell_price']:,} coins\n\n"

        embed.add_field(name="Mob Drops", value=hunt_drops_text, inline=False)

        if player["area"] >= 16:
            embed.add_field(name="Special Drop (Areas 16-20)",
                            value=f"**Dark Energy**\nChance: {DARK_ENERGY_DROP['chance']}% | Sell: {DARK_ENERGY_DROP['sell_price']:,} coins",
                            inline=False)

    elif category == "boss":
        embed = discord.Embed(title="🐉 Boss Drops", color=0x8b0000)

        boss_drops_text = ""
        for drop_item, drop_data in BOSS_DROPS.items():
            dungeons = ", ".join([str(d) for d in drop_data["dungeons"]])
            boss_drops_text += f"**{drop_item}**\n"
            boss_drops_text += f"Chance: {drop_data['chance']}% | Dungeons: {dungeons}\n\n"

        embed.add_field(name="Available Drops", value=boss_drops_text, inline=False)
        embed.add_field(name="Note", value="Boss drop chances can be increased with fighter pets!", inline=False)

    elif category == "chop" or category == "wood":
        embed = discord.Embed(title="🪓 Chopping Drops", color=0x8b4513)

        chop_info = "**Log Drop Chances by Area:**\n\n"
        chop_info += "🪵 **Wooden Log:** 70% (All areas)\n"
        chop_info += "📜 **Epic Log:** 30% (Area 1) → 22% (Area 2+)\n"
        chop_info += "🟫 **Super Log:** 8% (Area 2-3) → 7% (Area 4+)\n"
        chop_info += "🟤 **Mega Log:** 1% (Area 4-5) → 0.7% (Area 6+)\n"
        chop_info += "🟨 **HYPER Log:** 0.3% (Area 6-8) → 0.26% (Area 9+)\n"
        chop_info += "🟪 **ULTRA Log:** 0.04% (Area 9+)\n"
        chop_info += "⭐ **ULTIMATE Log:** 0.01% (Area 9+)\n"

        embed.add_field(name="Drop Rates", value=chop_info, inline=False)
        embed.add_field(name="Commands",
                        value="• `chop` - Base amounts\n• `axe` - More quantity\n• `bowsaw` - Even more\n• `chainsaw` - Maximum",
                        inline=False)

    elif category == "fish":
        embed = discord.Embed(title="🎣 Fishing Drops", color=0x4169e1)

        fish_info = "**Area 1:**\n"
        fish_info += "🐟 Normie Fish: 72%\n"
        fish_info += "🥇 Golden Fish: 28%\n\n"
        fish_info += "**Area 2+:**\n"
        fish_info += "🐟 Normie Fish: 72%\n"
        fish_info += "🥇 Golden Fish: 27.7% (varies by command)\n"
        fish_info += "🌟 EPIC Fish: 0.3% (varies by command)\n"
        fish_info += "⭐ SUPER Fish: ~0.01%\n"

        embed.add_field(name="Drop Rates", value=fish_info, inline=False)
        embed.add_field(name="Commands",
                        value="• `fish` - Base rates\n• `net` - Better EPIC Fish chance\n• `boat` - Even better\n• `bigboat` - Best rates",
                        inline=False)

    else:
        embed = discord.Embed(title="📋 Drop Information", description="Choose a category to view detailed drop rates",
                              color=0x9932cc)
        embed.add_field(name="Available Categories",
                        value="`rpg drops hunt` - Mob drops from hunting\n`rpg drops boss` - Boss drops from dungeons\n`rpg drops chop` - Wood from chopping\n`rpg drops fish` - Fish from fishing",
                        inline=False)
        embed.add_field(name="Your Area", value=f"Area {player['area']} - {AREAS[player['area']]['name']}",
                        inline=False)

    await ctx.send(embed=embed)


@bot.command(name='dungeon', aliases=['dung'])
async def dungeon_command(ctx, dungeon_num=None):
    player = get_player(ctx.author.id)

    if dungeon_num:
        try:
            dungeon_id = int(dungeon_num)
            if dungeon_id not in DUNGEONS:
                await ctx.send("Dungeon not found! Available dungeons: 1-5")
                return

            dungeon = DUNGEONS[dungeon_id]

            # Check if player has enough coins for dungeon key
            if player["coins"] < dungeon["key_price"]:
                await ctx.send(f"You need {dungeon['key_price']:,} coins to buy a dungeon key!")
                return

            # Check if player meets area requirements
            if player["area"] < dungeon_id:
                await ctx.send(f"You need to be in Area {dungeon_id} to fight this dungeon!")
                return

            # Consume dungeon key cost
            player["coins"] -= dungeon["key_price"]

            # Simulate dungeon fight
            dragon_hp = dungeon["hp_per_player"]
            dragon_max_hp = dragon_hp

            # Player weapon stats
            weapon = WEAPONS.get(player["weapon"], {"attack": 5})
            player_attack = weapon["attack"]

            # Battle simulation
            turns = 0

            while dragon_hp > 0 and turns < 20:
                turns += 1

                # Player chooses best attack
                if dragon_hp <= player_attack * 1.2:
                    chosen_attack = "bite"
                else:
                    chosen_attack = "power"

                attack_data = dungeon["commands"][chosen_attack]

                # Check if attack hits
                if random.randint(1, 100) <= attack_data["chance"]:
                    if "damage" in attack_data:
                        damage = int(player_attack * (attack_data["damage"] / 100))
                        dragon_hp -= damage

                if dragon_hp <= 0:
                    break

                # Dragon attacks back
                dragon_damage = random.randint(dungeon["attack"] - 10, dungeon["attack"] + 10)
                player["hp"] -= dragon_damage

                if player["hp"] <= 0:
                    break

            # Determine outcome
            embed = discord.Embed(title=f"🐉 Dungeon {dungeon_id}: {dungeon['name']}", color=0x8b0000)

            if dragon_hp <= 0:
                # Victory!
                reward = random.randint(dungeon["reward_min"], dungeon["reward_max"])
                player["coins"] += reward

                # Check for boss drops
                boss_drops = []
                for drop_item, drop_data in BOSS_DROPS.items():
                    if dungeon_id in drop_data["dungeons"]:
                        # Base 25% chance, can be improved with fighter pets later
                        if random.random() * 100 < drop_data["chance"]:
                            if drop_item not in player["inventory"]:
                                player["inventory"][drop_item] = 0
                            player["inventory"][drop_item] += 1
                            boss_drops.append(drop_item)

                # Advance to next area if this is their current area
                if player["area"] == dungeon_id and player["area"] < 21:
                    old_area = player["area"]
                    player["area"] += 1

                    # Update max area reached
                    if "max_area_reached" not in player:
                        player["max_area_reached"] = old_area
                    player["max_area_reached"] = max(player["max_area_reached"], player["area"])

                    # Check for newly unlocked commands
                    newly_unlocked = []
                    if player["area"] in AREA_UNLOCKS:
                        newly_unlocked = AREA_UNLOCKS[player["area"]]

                    embed.color = 0x00ff00
                    embed.add_field(name="🎉 Victory!", value=f"You defeated the {dungeon['name']}!", inline=False)
                    embed.add_field(name="Reward", value=f"{reward:,} coins", inline=True)

                    if boss_drops:
                        embed.add_field(name="🎁 Boss Drops!", value="\n".join([f"💎 {drop}" for drop in boss_drops]),
                                        inline=False)

                    embed.add_field(name="Area Progress",
                                    value=f"Advanced from Area {old_area} to Area {player['area']}!", inline=False)

                    if newly_unlocked:
                        embed.add_field(name="🎊 New Commands Unlocked!", value=", ".join(newly_unlocked), inline=False)
                else:
                    embed.color = 0x00ff00
                    embed.add_field(name="🎉 Victory!", value=f"You defeated the {dungeon['name']}!", inline=False)
                    embed.add_field(name="Reward", value=f"{reward:,} coins", inline=True)

                    if boss_drops:
                        embed.add_field(name="🎁 Boss Drops!", value="\n".join([f"💎 {drop}" for drop in boss_drops]),
                                        inline=False)

            else:
                # Defeat
                player["hp"] = 1
                embed.color = 0xff0000
                embed.add_field(name="💀 Defeat!", value=f"The {dungeon['name']} was too strong!", inline=False)
                embed.add_field(name="Result", value="You survived but are at 1 HP. Use `rpg heal` to recover.",
                                inline=False)

            save_player_data()
            await ctx.send(embed=embed)
            return

        except ValueError:
            await ctx.send("Please provide a valid dungeon number!")
            return

    # Show all available dungeons with dragons
    embed = discord.Embed(title="🏰 Available Dungeons", color=0x8b0000)

    dungeon_list = ""
    for dungeon_id, dungeon in DUNGEONS.items():
        area_req = f"Area {dungeon_id}" if player["area"] >= dungeon_id else f"🔒 Area {dungeon_id}"
        dungeon_list += f"**{dungeon_id}.** {dungeon['name']} - {area_req}\n"
        dungeon_list += f"💰 Key: {dungeon['key_price']:,} coins | ⚔️ Attack: {dungeon['attack']}\n\n"

    embed.add_field(name="Dragons to Fight", value=dungeon_list, inline=False)
    embed.add_field(name="Usage", value=f"`rpg dung <number>` - Fight a dungeon\nYour current area: {player['area']}",
                    inline=False)
    embed.add_field(name="Note", value="Defeating dungeons advances you to the next area!", inline=False)

    await ctx.send(embed=embed)


# Slash command versions
@bot.tree.command(name="start", description="Register a new player account")
async def slash_start(interaction: discord.Interaction):
    await interaction.response.defer()

    existing_player = get_player(interaction.user.id)
    if existing_player is not None:
        embed = discord.Embed(title="🎮 Account Exists",
                              description="You already have an account! Your adventure continues...", color=0x00ff00)
        await interaction.followup.send(embed=embed)
        return

    # Create new player
    player = create_player(interaction.user.id)

    embed = discord.Embed(title="🎮 Welcome to disRPG!",
                          description=f"Welcome, {interaction.user.display_name}! Your adventure begins now!",
                          color=0x00ff00)
    embed.add_field(name="Starting Stats",
                    value=f"Level: {player['level']}\nHP: {player['hp']}/{player['max_hp']}\nCoins: {player['coins']}\nArea: {player['area']}",
                    inline=True)
    embed.add_field(name="Starting Equipment", value=f"Weapon: {player['weapon']}\nStarting materials included!",
                    inline=True)
    embed.add_field(name="Get Started",
                    value="Use `/commands` to see all available commands\nTry `/hunt` to start your first battle!",
                    inline=False)
    embed.add_field(name="Tip", value="Use `/profile` to view your stats anytime", inline=False)

    save_player_data()
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="hunt", description="Hunt monsters in your current area")
async def slash_hunt(interaction: discord.Interaction, mode: str = None):
    await interaction.response.defer()

    # Create a proper context-like object for hunt
    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await hunt(ctx, mode)


@bot.tree.command(name="stats", description="View your character stats")
async def slash_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    player = get_player(interaction.user.id)
    if player is None:
        embed = discord.Embed(title="🎮 No Account",
                              description="Welcome to disRPG! Please use `/start` to create your adventure account first!",
                              color=0xff0000)
        await interaction.followup.send(embed=embed)
        return

    area_name = AREAS[player["area"]]["name"]
    embed = discord.Embed(title=f"📊 {interaction.user.display_name}'s Stats", color=0x0099ff)
    embed.add_field(name="Level", value=player["level"], inline=True)
    embed.add_field(name="EXP", value=f"{player['exp']}/{player['level'] * 100}", inline=True)
    embed.add_field(name="HP", value=f"{player['hp']}/{player['max_hp']}", inline=True)
    embed.add_field(name="Coins", value=f"{player['coins']:,}", inline=True)
    embed.add_field(name="Current Area", value=f"{player['area']} - {area_name}", inline=True)
    embed.add_field(name="Weapon", value=player["weapon"], inline=True)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="profile", description="View your character profile")
async def slash_profile(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    target_user = user or interaction.user

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await profile(ctx, target_user)


@bot.tree.command(name="inventory", description="View your inventory")
async def slash_inventory(interaction: discord.Interaction):
    await interaction.response.defer()
    player = get_player(interaction.user.id)
    if player is None:
        embed = discord.Embed(title="🎮 No Account",
                              description="Welcome to disRPG! Please use `/start` to create your adventure account first!",
                              color=0xff0000)
        await interaction.followup.send(embed=embed)
        return

    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}'s Inventory", color=0xffd700)

    if player["inventory"]:
        inv_text = ""
        for item, quantity in player["inventory"].items():
            inv_text += f"{item}: {quantity}\n"
        embed.add_field(name="Items", value=inv_text, inline=False)
    else:
        embed.add_field(name="Items", value="Empty", inline=False)

    embed.add_field(name="Coins", value=player["coins"], inline=True)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="heal", description="Heal your character for 50 coins")
async def slash_heal(interaction: discord.Interaction):
    await interaction.response.defer()

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await heal(ctx)


@bot.tree.command(name="daily", description="Claim your daily reward")
async def slash_daily(interaction: discord.Interaction):
    await interaction.response.defer()

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await daily(ctx)


@bot.tree.command(name="help", description="View all available commands and help")
async def slash_help(interaction: discord.Interaction, category: str = None):
    await interaction.response.defer()

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await help_command(ctx, category)


@bot.tree.command(name="shop", description="View the weapon shop")
async def slash_shop(interaction: discord.Interaction, page: str = None):
    await interaction.response.defer()

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await shop(ctx, page)


@bot.tree.command(name="fish", description="Fish for materials")
async def slash_fish(interaction: discord.Interaction):
    await interaction.response.defer()

    # Check if player exists first
    player = get_player(interaction.user.id)
    if player is None:
        embed = discord.Embed(title="🎮 No Account",
                              description="Welcome to disRPG! Please use `/start` to create your adventure account first!",
                              color=0xff0000)
        await interaction.followup.send(embed=embed)
        return

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await fish(ctx)


@bot.tree.command(name="chop", description="Chop wood for materials")
async def slash_chop(interaction: discord.Interaction):
    await interaction.response.defer()

    # Check if player exists first
    player = get_player(interaction.user.id)
    if player is None:
        embed = discord.Embed(title="🎮 No Account",
                              description="Welcome to disRPG! Please use `/start` to create your adventure account first!",
                              color=0xff0000)
        await interaction.followup.send(embed=embed)
        return

    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    ctx = SlashContext(interaction)
    await chop(ctx)


# Helper function to create context wrapper for slash commands
def create_slash_context(interaction):
    class SlashContext:
        def __init__(self, interaction):
            self.author = interaction.user
            self.interaction = interaction

        async def send(self, content=None, *, embed=None):
            if embed:
                await self.interaction.followup.send(embed=embed)
            else:
                await self.interaction.followup.send(content)

    return SlashContext(interaction)


# Info slash commands
@bot.tree.command(name="info", description="View bot features and statistics")
async def slash_info(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await bot_info(ctx)


@bot.tree.command(name="about", description="View bot information and credits")
async def slash_about(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await about_command(ctx)


# Key slash commands - these are the most important ones
@bot.tree.command(name="adventure", description="Go on a challenging adventure")
async def slash_adventure(interaction: discord.Interaction, mode: str = None):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await adventure(ctx, mode)


@bot.tree.command(name="area", description="View current area information")
async def slash_area(interaction: discord.Interaction, action: str = None, area_num: str = None):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await area_command(ctx, action, area_num)


@bot.tree.command(name="buy", description="Buy items from the shop")
async def slash_buy(interaction: discord.Interaction, item: str):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await buy(ctx, item_name=item)


@bot.tree.command(name="cooldowns", description="Check your command cooldowns")
async def slash_cooldowns(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await cooldowns(ctx, user)


@bot.tree.command(name="leaderboard", description="View the top players")
async def slash_leaderboard(interaction: discord.Interaction, board_type: str = "level", page: int = 1):
    await interaction.response.defer()
    ctx = create_slash_context(interaction)
    await leaderboard(ctx, board_type, page)


@bot.command(name='info')
async def bot_info(ctx):
    """Display beautiful bot information and features"""
    embed = discord.Embed(
        title="⚔️ disRPG - The Ultimate Discord RPG",
        description="**Experience the most comprehensive RPG adventure on Discord!**",
        color=0x7289da
    )

    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)

    # Core Features
    embed.add_field(
        name="🌟 **Core Features**",
        value="```\n• 21 Unique Areas to Explore\n• Dragon Boss Dungeons\n• Time Travel System\n• Guild Wars & Cooperation\n• Comprehensive Crafting```",
        inline=True
    )

    # Combat System
    embed.add_field(
        name="⚔️ **Combat System**",
        value="```\n• Hunt Monsters\n• Epic Adventures\n• Hardmode Challenges\n• PvP Duels\n• Arena Battles```",
        inline=True
    )

    # Economy
    embed.add_field(
        name="💰 **Economy**",
        value="```\n• Dynamic Trading\n• Lootbox System\n• Epic Shop\n• Resource Management\n• Gambling Games```",
        inline=True
    )

    # Working & Crafting
    embed.add_field(
        name="🔧 **Working & Crafting**",
        value="```\n• Fishing & Chopping\n• Mining Operations\n• Farming System\n• Weapon/Armor Crafting\n• Enchanting & Forging```",
        inline=True
    )

    # Advanced Features
    embed.add_field(
        name="🌌 **Advanced Features**",
        value="```\n• Time Travel Bonuses\n• Super Time Travel\n• Void Forging\n• Achievement System\n• Title Collection```",
        inline=True
    )

    # Social Features
    embed.add_field(
        name="👥 **Social Features**",
        value="```\n• Guild Creation\n• Guild Raids\n• Leaderboards\n• Player Trading\n• Multiplayer Games```",
        inline=True
    )

    # Statistics
    total_players = len(player_data)
    total_guilds = len(guild_data) if guild_data else 0

    embed.add_field(
        name="📊 **Server Statistics**",
        value=f"```\n👥 Players: {total_players}\n🏰 Guilds: {total_guilds}\n🌍 Areas: 21\n🐉 Dungeons: 15\n⚔️ Weapons: 50+```",
        inline=False
    )

    embed.add_field(
        name="🚀 **Get Started**",
        value="```\nrpgs start    # Create your character\nrpgs help     # View all commands\nrpgs hunt     # Start your first battle!```",
        inline=False
    )

    embed.set_footer(text="🎮 Join thousands of adventurers in the ultimate Discord RPG experience!")

    await ctx.send(embed=embed)


@bot.command(name='about')
async def about_command(ctx):
    """Display bot version and credits"""
    embed = discord.Embed(
        title="ℹ️ About disRPG",
        description="The most feature-rich Discord RPG bot",
        color=0x00ff88
    )

    embed.add_field(
        name="🎮 **Bot Information**",
        value="```\nVersion: 2.0.0\nLanguage: Python 3.11\nLibrary: discord.py\nUptime: Online```",
        inline=True
    )

    embed.add_field(
        name="⚡ **Performance**",
        value="```\nLatency: Low\nCommands: 100+\nAreas: 21\nReal-time Saving```",
        inline=True
    )

    embed.add_field(
        name="🔗 **Commands**",
        value="Use `rpgs help` for all commands\nUse `rpgs info` for features overview",
        inline=False
    )

    embed.set_footer(text="Made with ❤️ for the Discord RPG community")

    await ctx.send(embed=embed)


# Owner-only commands
@bot.command(name='give')
async def give_item(ctx, user: discord.User, item_name, amount=1):
    """Owner only: Give items to players"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    try:
        amount = int(amount)
    except ValueError:
        await ctx.send("Invalid amount!")
        return

    player = get_player(user.id)
    if player is None:
        await ctx.send(f"{user.display_name} doesn't have an account!")
        return

    if item_name not in player["inventory"]:
        player["inventory"][item_name] = 0
    player["inventory"][item_name] += amount

    embed = discord.Embed(title="🎁 Item Given", color=0x00ff00)
    embed.add_field(name="Recipient", value=user.display_name, inline=True)
    embed.add_field(name="Item", value=f"{item_name} x{amount}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='setlevel')
async def set_level(ctx, user: discord.User, level):
    """Owner only: Set player level"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    try:
        level = int(level)
    except ValueError:
        await ctx.send("Invalid level!")
        return

    player = get_player(user.id)
    if player is None:
        await ctx.send(f"{user.display_name} doesn't have an account!")
        return

    old_level = player["level"]
    player["level"] = level
    player["max_hp"] = 100 + (level - 1) * 20
    player["hp"] = player["max_hp"]

    embed = discord.Embed(title="📊 Level Set", color=0x9932cc)
    embed.add_field(name="Player", value=user.display_name, inline=True)
    embed.add_field(name="Level", value=f"{old_level} → {level}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='setarea')
async def set_area(ctx, user: discord.User, area):
    """Owner only: Set player area"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    try:
        area = int(area)
        if area < 1 or area > 21:
            await ctx.send("Area must be between 1 and 21!")
            return
    except ValueError:
        await ctx.send("Invalid area!")
        return

    player = get_player(user.id)
    if player is None:
        await ctx.send(f"{user.display_name} doesn't have an account!")
        return

    old_area = player["area"]
    player["area"] = area

    embed = discord.Embed(title="🗺️ Area Set", color=0x9932cc)
    embed.add_field(name="Player", value=user.display_name, inline=True)
    embed.add_field(name="Area", value=f"{old_area} → {area}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='addcoins')
async def add_coins(ctx, user: discord.User, amount):
    """Owner only: Add coins to player"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    try:
        amount = int(amount)
    except ValueError:
        await ctx.send("Invalid amount!")
        return

    player = get_player(user.id)
    if player is None:
        await ctx.send(f"{user.display_name} doesn't have an account!")
        return

    old_coins = player["coins"]
    player["coins"] += amount

    embed = discord.Embed(title="💰 Coins Added", color=0xffd700)
    embed.add_field(name="Player", value=user.display_name, inline=True)
    embed.add_field(name="Amount", value=f"+{amount:,}", inline=True)
    embed.add_field(name="Total", value=f"{player['coins']:,}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='resetplayer')
async def reset_player(ctx, user: discord.User, confirm=None):
    """Owner only: Reset a player's account"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    if confirm != "confirm":
        await ctx.send(
            f"⚠️ This will completely reset {user.display_name}'s account!\nUse `rpgs resetplayer {user.mention} confirm` to proceed.")
        return

    if str(user.id) in player_data:
        del player_data[str(user.id)]
        save_player_data()

        embed = discord.Embed(title="🔄 Player Reset", color=0xff6600)
        embed.add_field(name="Player", value=user.display_name, inline=True)
        embed.add_field(name="Status", value="Account completely reset", inline=True)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{user.display_name} doesn't have an account!")


@bot.command(name='settimetravel')
async def set_time_travel(ctx, user: discord.User, amount):
    """Owner only: Set player time travel count"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    try:
        amount = int(amount)
        if amount < 0:
            await ctx.send("Time travel amount must be 0 or positive!")
            return
    except ValueError:
        await ctx.send("Invalid time travel amount!")
        return

    player = get_player(user.id)
    if player is None:
        await ctx.send(f"{user.display_name} doesn't have an account!")
        return

    old_tt = player.get("time_travels", 0)
    player["time_travels"] = amount

    # Calculate new bonuses
    new_bonuses = calculate_tt_bonuses(amount)

    embed = discord.Embed(title="⏰ Time Travels Set", color=0x9932cc)
    embed.add_field(name="Player", value=user.display_name, inline=True)
    embed.add_field(name="Time Travels", value=f"{old_tt} → {amount}", inline=True)
    embed.add_field(name="New Bonuses",
                    value=f"EXP: +{new_bonuses['exp']}%\nDrops: +{new_bonuses['drops']}%\nWorking: +{new_bonuses['working']}%",
                    inline=False)

    save_player_data()
    await ctx.send(embed=embed)


@bot.command(name='allitemname')
async def all_items_name(ctx):
    """Owner only: List all available item names"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    all_items = set()

    # Add weapons
    all_items.update(WEAPONS.keys())

    # Add craft recipes
    all_items.update(CRAFT_RECIPES.keys())

    # Add forge recipes
    all_items.update(FORGE_RECIPES.keys())

    # Add void forge recipes
    all_items.update(VOID_FORGE_RECIPES.keys())

    # Add shop items
    for category in SHOP_ITEMS.values():
        all_items.update(category.keys())

    # Add mob drops
    for drop_data in MOB_DROPS.values():
        all_items.add(drop_data["item"])

    # Add boss drops
    all_items.update(BOSS_DROPS.keys())

    # Add working drops
    all_items.update(CHOPPING_DROPS.keys())
    all_items.update(["Normie Fish", "Golden Fish", "EPIC Fish", "SUPER Fish"])
    all_items.update(["Apple", "Banana", "Watermelon"])
    all_items.update(["Ruby"])

    # Add material conversions
    all_items.update(MATERIAL_CONVERSION.keys())

    # Add cooking recipes
    all_items.update(COOKING_RECIPES.keys())

    # Add special items
    all_items.update(["Dark Energy", "life potion", "Dragon Essence", "Time Dragon Essence"])

    # Add dungeon keys
    for i in range(1, 16):
        all_items.add(f"Dungeon {i} Key")

    # Sort and create pages
    sorted_items = sorted(list(all_items))
    items_per_page = 50
    total_pages = (len(sorted_items) + items_per_page - 1) // items_per_page

    for page in range(total_pages):
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(sorted_items))
        page_items = sorted_items[start_idx:end_idx]

        embed = discord.Embed(title=f"📋 All Item Names - Page {page + 1}/{total_pages}", color=0x9932cc)

        # Split items into chunks for better formatting
        chunk_size = 25
        for i in range(0, len(page_items), chunk_size):
            chunk = page_items[i:i + chunk_size]
            field_name = f"Items {i + 1 + start_idx}-{min(i + chunk_size + start_idx, len(sorted_items))}"
            embed.add_field(name=field_name, value="\n".join(chunk), inline=True)

        embed.add_field(name="Total Items", value=f"{len(sorted_items)} items found", inline=False)
        await ctx.send(embed=embed)


@bot.command(name='ownerhelp')
async def owner_help(ctx):
    """Owner only: Show owner commands"""
    if not is_owner(ctx.author.id):
        await ctx.send("❌ This command is owner-only!")
        return

    embed = discord.Embed(title="👑 Owner Commands", color=0x9932cc)
    embed.add_field(name="Player Management",
                    value="`give <user> <item> [amount]` - Give items\n`setlevel <user> <level>` - Set player level\n`setarea <user> <area>` - Set player area\n`addcoins <user> <amount>` - Add coins\n`settimetravel <user> <amount>` - Set time travels\n`resetplayer <user> confirm` - Reset account",
                    inline=False)
    embed.add_field(name="Information",
                    value="`allitemname` - List all available item names",
                    inline=False)
    embed.add_field(name="Note", value="All commands require exact Discord user mentions or IDs", inline=False)

    await ctx.send(embed=embed)


# Trading system - Enhanced trade rates by area
TRADE_RATES = {
    1: {
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 3},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 2}
    },
    2: {
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 5},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 3}
    },
    3: {
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 5},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 3},
        "C": {"from": "Apple", "to": "Wooden Log", "rate": 3},
        "D": {"from": "Wooden Log", "to": "Apple", "rate": 4}
    },
    4: {
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 7},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 4},
        "C": {"from": "Apple", "to": "Wooden Log", "rate": 4},
        "D": {"from": "Wooden Log", "to": "Apple", "rate": 5},
        "E": {"from": "Ruby", "to": "Wooden Log", "rate": 250},
        "F": {"from": "Wooden Log", "to": "Ruby", "rate": 350}
    },
    5: {
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 7},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 4},
        "C": {"from": "Apple", "to": "Wooden Log", "rate": 5},
        "D": {"from": "Wooden Log", "to": "Apple", "rate": 6},
        "E": {"from": "Ruby", "to": "Wooden Log", "rate": 300},
        "F": {"from": "Wooden Log", "to": "Ruby", "rate": 400}
    },
    15: {  # Default for areas 16-20
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 20},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 15},
        "C": {"from": "Apple", "to": "Wooden Log", "rate": 15},
        "D": {"from": "Wooden Log", "to": "Apple", "rate": 18},
        "E": {"from": "Ruby", "to": "Wooden Log", "rate": 1000},
        "F": {"from": "Wooden Log", "to": "Ruby", "rate": 1200}
    },
    21: {  # THE TOP
        "A": {"from": "Normie Fish", "to": "Wooden Log", "rate": 25},
        "B": {"from": "Wooden Log", "to": "Normie Fish", "rate": 20},
        "C": {"from": "Apple", "to": "Wooden Log", "rate": 20},
        "D": {"from": "Wooden Log", "to": "Apple", "rate": 25},
        "E": {"from": "Ruby", "to": "Wooden Log", "rate": 1500},
        "F": {"from": "Wooden Log", "to": "Ruby", "rate": 1800}
    }
}


@bot.command(name='trade')
async def trade(ctx, trade_id=None, amount=None):
    player = get_player(ctx.author.id)

    if not trade_id:
        # Show available trades and inventory
        area = player["area"]

        # Determine which trade rates to use
        if area <= 15:
            trade_area = min(area, 5)  # Use closest available rates
        elif area <= 20:
            trade_area = 15
        else:
            trade_area = 21

        # Find the closest available trade table
        while trade_area not in TRADE_RATES and trade_area > 0:
            trade_area -= 1

        if trade_area not in TRADE_RATES:
            trade_area = 1

        rates = TRADE_RATES[trade_area]

        embed = discord.Embed(title="💱 Trading Post", description=f"Area {area} Trade Rates", color=0xffd700)

        trades_text = ""
        for tid, trade_data in rates.items():
            trades_text += f"**{tid}:** {trade_data['from']} → {trade_data['to']} (1:{trade_data['rate']})\n"

        embed.add_field(name="Available Trades", value=trades_text, inline=False)

        # Show inventory
        inv_text = ""
        for item in ["Wooden Log", "Normie Fish", "Apple", "Ruby"]:
            count = player["inventory"].get(item, 0)
            inv_text += f"{item}: {count}\n"

        embed.add_field(name="Your Resources", value=inv_text, inline=True)
        embed.add_field(name="Usage", value="`rpg trade <ID> [amount]`\nUse 'all' for amount to trade everything",
                        inline=False)

        await ctx.send(embed=embed)
        return

    # Execute trade
    area = player["area"]

    # Determine which trade rates to use
    if area <= 15:
        trade_area = min(area, 5)
    elif area <= 20:
        trade_area = 15
    else:
        trade_area = 21

    # Find the closest available trade table
    while trade_area not in TRADE_RATES and trade_area > 0:
        trade_area -= 1

    if trade_area not in TRADE_RATES:
        trade_area = 1

    rates = TRADE_RATES[trade_area]

    trade_id = trade_id.upper()
    if trade_id not in rates:
        await ctx.send("Invalid trade ID! Use `rpg trade` to see available trades.")
        return

    trade_data = rates[trade_id]
    from_item = trade_data["from"]
    to_item = trade_data["to"]
    rate = trade_data["rate"]

    # Handle amount
    if amount == "all":
        trade_amount = player["inventory"].get(from_item, 0)
    else:
        try:
            trade_amount = int(amount) if amount else 1
        except ValueError:
            await ctx.send("Invalid amount! Use a number or 'all'")
            return

    if trade_amount <= 0:
        await ctx.send("You need to specify a positive amount!")
        return

    if player["inventory"].get(from_item, 0) < trade_amount:
        await ctx.send(f"You don't have {trade_amount} {from_item}!")
        return

    # Execute trade
    received_amount = trade_amount * rate

    player["inventory"][from_item] -= trade_amount
    if player["inventory"][from_item] <= 0:
        del player["inventory"][from_item]

    if to_item not in player["inventory"]:
        player["inventory"][to_item] = 0
    player["inventory"][to_item] += received_amount

    embed = discord.Embed(title="✅ Trade Complete!", color=0x00ff00)
    embed.add_field(name="Traded", value=f"{from_item} x{trade_amount}", inline=True)
    embed.add_field(name="Received", value=f"{to_item} x{received_amount}", inline=True)
    embed.add_field(name="Rate", value=f"1:{rate}", inline=True)

    save_player_data()
    await ctx.send(embed=embed)


# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("Please set your DISCORD_BOT_TOKEN in the Secrets tab!")
        print("Go to: https://discord.com/developers/applications")
        print("Create a bot and copy the token to your Replit secrets.")
    else:
        bot.run(token, log_handler=handler, log_level=logging.DEBUG)