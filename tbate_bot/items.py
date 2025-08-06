# items.py
# This file is the central source for all item definitions in the game.

ALL_ITEMS = [
    # Potions
    {"name": "Stamina Potion", "description": "Restores 25 energy.", "price": 500, "tradeable": 1, "item_type": "consumable", "emoji": "🧪"},
    {"name": "Greater Stamina Potion", "description": "A potent brew that restores 50 energy.", "price": 950, "tradeable": 1, "item_type": "consumable", "emoji": "🧪"},
    {"name": "Superior Stamina Potion", "description": "A masterful brew that restores 100 energy.", "price": 1800, "tradeable": 1, "item_type": "consumable", "emoji": "🧪"},
    
    # Scrolls
    {"name": "Small XP Scroll", "description": "A dusty scroll that grants 250 XP.", "price": 2000, "tradeable": 1, "item_type": "consumable", "emoji": "📜"},
    {"name": "Medium XP Scroll", "description": "A well-preserved scroll that grants 1000 XP.", "price": 7500, "tradeable": 1, "item_type": "consumable", "emoji": "📜"},
    {"name": "Large XP Scroll", "description": "A radiant scroll that grants 5000 XP.", "price": 35000, "tradeable": 1, "item_type": "consumable", "emoji": "📜"},
    {"name": "Tome of Wealth", "description": "A heavy book that grants 1000 Gold.", "price": 5000, "tradeable": 0, "item_type": "consumable", "emoji": "📖"},

    # Boosts
    {"name": "Beast Lure", "description": "Your next expedition will yield 50% more beast cores.", "price": 1200, "tradeable": 1, "item_type": "consumable", "emoji": "🍖"},
    {"name": "Expedition Rations", "description": "Reduces the energy cost of your next expedition by 50%.", "price": 800, "tradeable": 1, "item_type": "consumable", "emoji": "🥖"},
    
    # Common Materials
    {"name": "Broken Beast Horn", "description": "A common material dropped from beasts.", "price": 50, "tradeable": 1, "item_type": "material", "emoji": "🦴"},
    {"name": "Mana Infused Hide", "description": "A tough hide used in crafting.", "price": 150, "tradeable": 1, "item_type": "material", "emoji": "🟫"},
    {"name": "Glow Moss", "description": "A faintly glowing moss found in deep forests.", "price": 100, "tradeable": 1, "item_type": "material", "emoji": "🌿"},
    {"name": "Iron Ore", "description": "A chunk of raw iron.", "price": 75, "tradeable": 1, "item_type": "material", "emoji": "🪨"},
    {"name": "Snapper Shell Fragment", "description": "A sharp piece of a Snapper shell.", "price": 60, "tradeable": 1, "item_type": "material", "emoji": "🐢"},
    {"name": "Sunpetal Leaf", "description": "A common herb that grows in sunlight.", "price": 80, "tradeable": 1, "item_type": "material", "emoji": "☀️"},

    # Uncommon Materials
    {"name": "Silver Ore", "description": "A chunk of raw silver.", "price": 250, "tradeable": 1, "item_type": "material", "emoji": "🪙"},
    {"name": "Moonshade Petal", "description": "An herb that only blooms in moonlight.", "price": 200, "tradeable": 1, "item_type": "material", "emoji": "🌙"},
    {"name": "Griffin Feather", "description": "A sturdy feather from a griffin.", "price": 300, "tradeable": 1, "item_type": "material", "emoji": "🪶"},
    {"name": "Golem Shard", "description": "A piece of a lesser golem.", "price": 275, "tradeable": 1, "item_type": "material", "emoji": "🗿"},
    {"name": "Flawed Mana Crystal", "description": "A mana crystal with impurities.", "price": 400, "tradeable": 1, "item_type": "material", "emoji": "💎"},

    # Rare Materials
    {"name": "Gold Ore", "description": "A chunk of raw gold.", "price": 600, "tradeable": 1, "item_type": "material", "emoji": "💰"},
    {"name": "Wyvern Claw", "description": "A sharp claw from a lesser wyvern.", "price": 750, "tradeable": 1, "item_type": "material", "emoji": "🐉"},
    {"name": "Elderwood Heart", "description": "The resilient core of an ancient tree.", "price": 800, "tradeable": 1, "item_type": "material", "emoji": "🌳"},
    {"name": "Dragon's Breath Blossom", "description": "A flower that thrives in extreme heat.", "price": 700, "tradeable": 1, "item_type": "material", "emoji": "🌸"},
    {"name": "Pure Mana Crystal", "description": "A flawless mana crystal.", "price": 1000, "tradeable": 1, "item_type": "material", "emoji": "💠"},

    # Epic Materials
    {"name": "Mithril Ore", "description": "An incredibly rare and durable metal.", "price": 2000, "tradeable": 1, "item_type": "material", "emoji": "⛓️"},
    {"name": "Glaudr Scale", "description": "A scale from a mighty Glaudr.", "price": 2500, "tradeable": 1, "item_type": "material", "emoji": "🐲"},
    {"name": "Feywood Branch", "description": "A branch humming with otherworldly energy.", "price": 2200, "tradeable": 1, "item_type": "material", "emoji": "🌿"},
    {"name": "Perfect Mana Crystal", "description": "A vessel of immense, pure mana.", "price": 5000, "tradeable": 1, "item_type": "material", "emoji": "✨"},

    # Legendary Materials
    {"name": "Aetheric Crystal", "description": "A rare crystal humming with untapped potential.", "price": 10000, "tradeable": 1, "item_type": "material", "emoji": "🔮"},
    {"name": "World-Tree Leaf", "description": "A leaf that holds a fragment of the world's vitality.", "price": 25000, "tradeable": 1, "item_type": "material", "emoji": "🍃"},
    {"name": "Felled Asura's Feather", "description": "A feather that seems to defy gravity.", "price": 50000, "tradeable": 0, "item_type": "material", "emoji": "🕊️"},
]