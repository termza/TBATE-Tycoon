# items.py

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
    {"name": "Broken Beast Horn", "description": "A common material.", "price": 50, "tradeable": 1, "item_type": "material", "emoji": "🦴"},
    {"name": "Mana Infused Hide", "description": "A common material.", "price": 150, "tradeable": 1, "item_type": "material", "emoji": "🟫"},
    {"name": "Glow Moss", "description": "A common material.", "price": 100, "tradeable": 1, "item_type": "material", "emoji": "🌿"},
    {"name": "Iron Ore", "description": "A common material.", "price": 75, "tradeable": 1, "item_type": "material", "emoji": "🪨"},
    {"name": "Snapper Shell Fragment", "description": "A common material.", "price": 60, "tradeable": 1, "item_type": "material", "emoji": "🐢"},
    {"name": "Sunpetal Leaf", "description": "A common material.", "price": 80, "tradeable": 1, "item_type": "material", "emoji": "☀️"},
    {"name": "Goblin Ear", "description": "A common material.", "price": 25, "tradeable": 1, "item_type": "material", "emoji": "👂"},
    {"name": "Rat Tail", "description": "A common material.", "price": 10, "tradeable": 1, "item_type": "material", "emoji": "🐀"},
    {"name": "Slime Core", "description": "A common material.", "price": 30, "tradeable": 1, "item_type": "material", "emoji": "🟢"},
    {"name": "Copper Ore", "description": "A common material.", "price": 40, "tradeable": 1, "item_type": "material", "emoji": "🟤"},
    {"name": "Rough Quartz", "description": "A common material.", "price": 65, "tradeable": 1, "item_type": "material", "emoji": "⚪"},
    {"name": "Wild Berries", "description": "A common material.", "price": 15, "tradeable": 1, "item_type": "material", "emoji": "🍓"},
    {"name": "Cave Mushroom", "description": "A common material.", "price": 20, "tradeable": 1, "item_type": "material", "emoji": "🍄"},

    # Uncommon Materials
    {"name": "Silver Ore", "description": "An uncommon material.", "price": 250, "tradeable": 1, "item_type": "material", "emoji": "🪙"},
    {"name": "Moonshade Petal", "description": "An uncommon material.", "price": 200, "tradeable": 1, "item_type": "material", "emoji": "🌙"},
    {"name": "Griffin Feather", "description": "An uncommon material.", "price": 300, "tradeable": 1, "item_type": "material", "emoji": "🪶"},
    {"name": "Golem Shard", "description": "An uncommon material.", "price": 275, "tradeable": 1, "item_type": "material", "emoji": "🗿"},
    {"name": "Flawed Mana Crystal", "description": "An uncommon material.", "price": 400, "tradeable": 1, "item_type": "material", "emoji": "💎"},
    {"name": "Orc Tusk", "description": "An uncommon material.", "price": 180, "tradeable": 1, "item_type": "material", "emoji": "🦷"},
    {"name": "Harpy Talon", "description": "An uncommon material.", "price": 220, "tradeable": 1, "item_type": "material", "emoji": "🦅"},
    {"name": "Barghest Fang", "description": "An uncommon material.", "price": 240, "tradeable": 1, "item_type": "material", "emoji": "🐺"},
    {"name": "Cobalt Ore", "description": "An uncommon material.", "price": 350, "tradeable": 1, "item_type": "material", "emoji": "🔵"},
    {"name": "Obsidian Shard", "description": "An uncommon material.", "price": 320, "tradeable": 1, "item_type": "material", "emoji": "⚫"},
    {"name": "Sunstone", "description": "An uncommon material.", "price": 450, "tradeable": 1, "item_type": "material", "emoji": "🧡"},
    {"name": "Mana Bloom Petal", "description": "An uncommon material.", "price": 280, "tradeable": 1, "item_type": "material", "emoji": "🌺"},
    {"name": "Blood Root", "description": "An uncommon material.", "price": 260, "tradeable": 1, "item_type": "material", "emoji": "🩸"},

    # Rare Materials
    {"name": "Gold Ore", "description": "A rare material.", "price": 600, "tradeable": 1, "item_type": "material", "emoji": "💰"},
    {"name": "Wyvern Claw", "description": "A rare material.", "price": 750, "tradeable": 1, "item_type": "material", "emoji": "🐉"},
    {"name": "Elderwood Heart", "description": "A rare material.", "price": 800, "tradeable": 1, "item_type": "material", "emoji": "🌳"},
    {"name": "Dragon's Breath Blossom", "description": "A rare material.", "price": 700, "tradeable": 1, "item_type": "material", "emoji": "🌸"},
    {"name": "Pure Mana Crystal", "description": "A rare material.", "price": 1000, "tradeable": 1, "item_type": "material", "emoji": "💠"},
    {"name": "Basilisk Eye", "description": "A rare material.", "price": 900, "tradeable": 1, "item_type": "material", "emoji": "👁️"},
    {"name": "Minotaur Horn", "description": "A rare material.", "price": 850, "tradeable": 1, "item_type": "material", "emoji": "👿"},
    {"name": "Hydra Scale", "description": "A rare material.", "price": 950, "tradeable": 1, "item_type": "material", "emoji": "🐍"},
    {"name": "Orichalcum Ore", "description": "A rare material.", "price": 1200, "tradeable": 1, "item_type": "material", "emoji": "🔩"},
    {"name": "Adamantite Shard", "description": "A rare material.", "price": 1500, "tradeable": 1, "item_type": "material", "emoji": "⚙️"},
    {"name": "Flawless Emerald", "description": "A rare material.", "price": 1800, "tradeable": 1, "item_type": "material", "emoji": "💚"},
    {"name": "Golden Apple", "description": "A rare material.", "price": 1300, "tradeable": 1, "item_type": "material", "emoji": "🍎"},
    {"name": "Nightshade Blossom", "description": "A rare material.", "price": 1100, "tradeable": 1, "item_type": "material", "emoji": "💜"},

    # Epic Materials
    {"name": "Mithril Ore", "description": "An epic material.", "price": 2000, "tradeable": 1, "item_type": "material", "emoji": "⛓️"},
    {"name": "Glaudr Scale", "description": "An epic material.", "price": 2500, "tradeable": 1, "item_type": "material", "emoji": "🐲"},
    {"name": "Feywood Branch", "description": "An epic material.", "price": 2200, "tradeable": 1, "item_type": "material", "emoji": "🌿"},
    {"name": "Perfect Mana Crystal", "description": "An epic material.", "price": 5000, "tradeable": 1, "item_type": "material", "emoji": "✨"},
    {"name": "Phoenix Ash", "description": "An epic material.", "price": 4000, "tradeable": 1, "item_type": "material", "emoji": "🔥"},
    {"name": "Leviathan's Whisker", "description": "An epic material.", "price": 4500, "tradeable": 1, "item_type": "material", "emoji": "🌊"},
    {"name": "Asuran Steel Ingot", "description": "An epic material.", "price": 6000, "tradeable": 1, "item_type": "material", "emoji": "🛡️"},
    {"name": "Void-Touched Diamond", "description": "An epic material.", "price": 7500, "tradeable": 1, "item_type": "material", "emoji": "⚫"},
    {"name": "Dragon's Ivy", "description": "An epic material.", "price": 3000, "tradeable": 1, "item_type": "material", "emoji": "덩"},
    {"name": "Soul-Spore Dust", "description": "An epic material.", "price": 3500, "tradeable": 1, "item_type": "material", "emoji": "✨"},

    # Legendary Materials
    {"name": "Aetheric Crystal", "description": "A legendary material.", "price": 10000, "tradeable": 1, "item_type": "material", "emoji": "🔮"},
    {"name": "World-Tree Leaf", "description": "A legendary material.", "price": 25000, "tradeable": 1, "item_type": "material", "emoji": "🍃"},
    {"name": "Felled Asura's Feather", "description": "A legendary material.", "price": 50000, "tradeable": 0, "item_type": "material", "emoji": "🕊️"},
    
    # Equipment
    {"name": "Ring of Minor Vigor", "description": "+10 Max Energy.", "price": 5000, "tradeable": 1, "item_type": "equipment", "emoji": "💍", "stats": {"max_energy": 10}, "slot": "ring"},
    {"name": "Ring of the Apprentice", "description": "+2% XP Gain.", "price": 7500, "tradeable": 1, "item_type": "equipment", "emoji": "💍", "stats": {"xp_boost": 0.02}, "slot": "ring"},
    {"name": "Band of the Hoarder", "description": "+2% Gold Gain from selling.", "price": 7500, "tradeable": 1, "item_type": "equipment", "emoji": "💍", "stats": {"gold_boost": 0.02}, "slot": "ring"},
    {"name": "Adept's Ring", "description": "+5% XP Gain.", "price": 25000, "tradeable": 1, "item_type": "equipment", "emoji": "💍", "stats": {"xp_boost": 0.05}, "slot": "ring"},
    {"name": "Pendant of Stamina", "description": "+25 Max Energy.", "price": 12000, "tradeable": 1, "item_type": "equipment", "emoji": "🧿", "stats": {"max_energy": 25}, "slot": "amulet"},
    {"name": "Amulet of the Beastmaster", "description": "+5% Beast Core Drops.", "price": 15000, "tradeable": 1, "item_type": "equipment", "emoji": "🧿", "stats": {"core_boost": 0.05}, "slot": "amulet"},
    {"name": "Trainee's Blade", "description": "A basic blade. (No effect yet)", "price": 1000, "tradeable": 1, "item_type": "equipment", "emoji": "🗡️", "stats": {}, "slot": "weapon"},
    {"name": "Apprentice's Cloak", "description": "A simple cloak. (No effect yet)", "price": 1000, "tradeable": 1, "item_type": "equipment", "emoji": "🧥", "stats": {}, "slot": "cloak"},
]