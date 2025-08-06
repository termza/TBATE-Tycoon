# database.py

import sqlite3
import discord
import time
import random
from math import floor
from datetime import date
import items

# --- Game Configuration & Formulas ---
ENERGY_REGEN_RATE_SECONDS = 300
def calculate_xp_for_level(level): return int(100 * (level ** 1.5))
def calculate_max_energy(level): return 100 + ((level - 1) * 2)

CORE_STAGES = {
    1: ("⚫ Black Stage", discord.Color.dark_grey()),
    10: ("🔴 Dark Red Stage", discord.Color.dark_red()),
    20: ("🔴 Solid Red Stage", discord.Color.red()),
    30: ("🔴 Light Red Stage", discord.Color.from_rgb(255, 80, 80)),
    40: ("🟠 Dark Orange Stage", discord.Color.dark_orange()),
    50: ("🟠 Solid Orange Stage", discord.Color.orange()),
    60: ("🟠 Light Orange Stage", discord.Color.from_rgb(255, 191, 0)),
    70: ("🟡 Dark Yellow Stage", discord.Color.dark_gold()),
    80: ("🟡 Solid Yellow Stage", discord.Color.gold()),
    90: ("🟡 Light Yellow Stage", discord.Color.from_rgb(255, 255, 150)),
    100: ("⚪ Silver Stage", discord.Color.light_grey()),
    125: ("✨ White Stage (Integration)", discord.Color.from_rgb(240, 240, 240)),
    150: ("💜 Aether Core (Formation)", discord.Color.purple()),
    175: ("💜 Aether Core (Phase 1)", discord.Color.from_rgb(153, 50, 204)),
    200: ("💜 Aether Core (Phase 2)", discord.Color.from_rgb(147, 112, 219)),
    250: ("💜 Aether Core (Phase 3)", discord.Color.from_rgb(218, 112, 214))
}

# --- Database Setup ---
def setup_database():
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            core_level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            beast_cores INTEGER NOT NULL DEFAULT 0,
            gold INTEGER NOT NULL DEFAULT 0,
            energy INTEGER NOT NULL DEFAULT {calculate_max_energy(1)},
            last_energy_update INTEGER NOT NULL DEFAULT 0,
            last_daily_timestamp INTEGER NOT NULL DEFAULT 0,
            beast_lure_active INTEGER NOT NULL DEFAULT 0,
            expedition_cost_discount_active INTEGER NOT NULL DEFAULT 0,
            weapon_id INTEGER,
            cloak_id INTEGER,
            amulet_id INTEGER,
            ring1_id INTEGER,
            ring2_id INTEGER,
            FOREIGN KEY (weapon_id) REFERENCES items(item_id),
            FOREIGN KEY (cloak_id) REFERENCES items(item_id),
            FOREIGN KEY (amulet_id) REFERENCES items(item_id),
            FOREIGN KEY (ring1_id) REFERENCES items(item_id),
            FOREIGN KEY (ring2_id) REFERENCES items(item_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 100,
            tradeable INTEGER NOT NULL DEFAULT 1,
            item_type TEXT NOT NULL DEFAULT 'consumable',
            emoji TEXT,
            slot TEXT,
            max_energy REAL DEFAULT 0,
            xp_boost REAL DEFAULT 0,
            gold_boost REAL DEFAULT 0,
            core_boost REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id),
            UNIQUE(user_id, item_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marketplace_listings (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            listed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES players(user_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            type TEXT NOT NULL UNIQUE,
            target INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            is_claimed INTEGER NOT NULL DEFAULT 0,
            date_assigned DATE NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            crafted_item_id INTEGER NOT NULL,
            quantity_produced INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (crafted_item_id) REFERENCES items(item_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_materials (
            recipe_id INTEGER NOT NULL,
            material_item_id INTEGER NOT NULL,
            quantity_required INTEGER NOT NULL,
            PRIMARY KEY (recipe_id, material_item_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
            FOREIGN KEY (material_item_id) REFERENCES items(item_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonds (
            bond_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            rarity TEXT NOT NULL,
            emoji TEXT,
            bonus_type TEXT NOT NULL,
            bonus_value REAL NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_bonds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bond_id INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (bond_id) REFERENCES bonds(bond_id),
            UNIQUE(user_id, bond_id)
        )
    ''')
    
    if cursor.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
        items_to_insert = []
        for i in items.ALL_ITEMS:
            stats = i.get('stats', {})
            items_to_insert.append((
                i['name'], i['description'], i['price'], i['tradeable'],
                i['item_type'], i.get('emoji'), i.get('slot'),
                stats.get('max_energy', 0), stats.get('xp_boost', 0),
                stats.get('gold_boost', 0), stats.get('core_boost', 0)
            ))
        cursor.executemany("""
            INSERT INTO items (name, description, price, tradeable, item_type, emoji,
            slot, max_energy, xp_boost, gold_boost, core_boost) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items_to_insert)

    if cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        default_tasks = [("Go on 5 expeditions", "expedition", 5), ("Sell 100 beast cores", "sell_cores", 100), ("Win 2 minigames", "win_minigame", 2), ("Earn 1000 gold from selling", "earn_gold", 1000), ("Gain 500 XP", "gain_xp", 500), ("Craft an item", "craft_item", 1)]
        cursor.executemany("INSERT INTO tasks (description, type, target) VALUES (?, ?, ?)", default_tasks)
    if cursor.execute("SELECT COUNT(*) FROM recipes").fetchone()[0] == 0:
        recipes_to_add = {"Greater Stamina Potion": [("Stamina Potion", 2), ("Glow Moss", 5)], "Superior Stamina Potion": [("Greater Stamina Potion", 2), ("Moonshade Petal", 3)], "Beast Lure": [("Mana Infused Hide", 3), ("Broken Beast Horn", 10)], "Small XP Scroll": [("Pure Mana Crystal", 1), ("Glow Moss", 10)], "Medium XP Scroll": [("Small XP Scroll", 2), ("Griffin Feather", 5)], "Ring of Minor Vigor": [("Iron Ore", 20), ("Flawed Mana Crystal", 1)], "Amulet of the Beastmaster": [("Elderwood Heart", 1), ("Griffin Feather", 5), ("Pure Mana Crystal", 1)]}
        for crafted_item_name, materials in recipes_to_add.items():
            crafted_item_row = cursor.execute("SELECT item_id FROM items WHERE name = ?", (crafted_item_name,)).fetchone()
            if crafted_item_row:
                crafted_item_id = crafted_item_row[0]
                cursor.execute("INSERT INTO recipes (crafted_item_id) VALUES (?)", (crafted_item_id,))
                recipe_id = cursor.lastrowid
                for material_name, qty in materials:
                    material_item_row = cursor.execute("SELECT item_id FROM items WHERE name = ?", (material_name,)).fetchone()
                    if material_item_row:
                        material_item_id = material_item_row[0]
                        cursor.execute("INSERT INTO recipe_materials (recipe_id, material_item_id, quantity_required) VALUES (?, ?, ?)", (recipe_id, material_item_id, qty))
    if cursor.execute("SELECT COUNT(*) FROM bonds").fetchone()[0] == 0:
        default_bonds = [("Sylvie", "Epic", "🐲", "xp_boost", 0.05, "Boosts XP gain by 5%."), ("Regis", "Epic", "🐺", "gold_boost", 0.10, "Boosts Gold gain by 10%."), ("Caera's Companion", "Rare", "🦅", "energy_regen_boost", 0.10, "Boosts energy regen rate by 10%."),]
        cursor.executemany("INSERT INTO bonds (name, rarity, emoji, bonus_type, bonus_value, description) VALUES (?, ?, ?, ?, ?, ?)", default_bonds)
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)); player = cursor.fetchone()
    if player is None:
        current_timestamp = int(time.time()); base_max_energy = calculate_max_energy(1)
        cursor.execute(
            """INSERT INTO players (user_id, core_level, xp, beast_cores, gold, energy, last_energy_update, 
                                last_daily_timestamp, beast_lure_active, expedition_cost_discount_active,
                                weapon_id, cloak_id, amulet_id, ring1_id, ring2_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL)""",
            (user_id, 1, 0, 0, 0, base_max_energy, current_timestamp, 0, 0, 0))
        conn.commit(); cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)); player = cursor.fetchone()
    current_time = int(time.time()); last_update = player['last_energy_update']
    active_bond = get_active_bond(user_id)
    energy_regen_bonus = active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'energy_regen_boost' else 0.0
    current_regen_rate = ENERGY_REGEN_RATE_SECONDS * (1.0 - energy_regen_bonus)
    time_passed = current_time - last_update; energy_to_add = floor(time_passed / current_regen_rate)
    if energy_to_add > 0:
        equipped_items = get_equipped_items(user_id)
        max_energy_bonus = sum(item['max_energy'] for item in equipped_items)
        bond_energy_bonus = active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'max_energy_bonus' else 0
        current_energy = player['energy']; max_energy = calculate_max_energy(player['core_level']) + max_energy_bonus + bond_energy_bonus
        new_energy = min(int(max_energy), current_energy + energy_to_add)
        if new_energy > current_energy:
            time_used = (new_energy - current_energy) * current_regen_rate
            new_timestamp = int(last_update + time_used)
            update_player(user_id, energy=new_energy, last_energy_update=new_timestamp)
            cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)); player = cursor.fetchone()
    conn.close(); return player
def update_player(user_id, **kwargs):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    fields = ', '.join([f'{key} = ?' for key in kwargs]); values = list(kwargs.values()); values.append(user_id)
    query = f"UPDATE players SET {fields} WHERE user_id = ?"; cursor.execute(query, tuple(values)); conn.commit(); conn.close()
def get_leaderboard(limit=10):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT user_id, core_level FROM players ORDER BY core_level DESC LIMIT ?", (limit,))
    ld_data = cursor.fetchall(); conn.close(); return ld_data
def get_item_by_name(name):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE LOWER(name) = LOWER(?)", (name,))
    item = cursor.fetchone(); conn.close(); return item
def get_item_by_id(item_id):
    if item_id is None: return None
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
    item = cursor.fetchone(); conn.close(); return item
def get_all_items():
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM items"); items = cursor.fetchall(); conn.close(); return items
def get_inventory(user_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT i.*, inv.quantity FROM inventory inv JOIN items i ON inv.item_id = i.item_id WHERE inv.user_id = ? AND inv.quantity > 0 ORDER BY i.name", (user_id,))
    inventory = cursor.fetchall(); conn.close(); return inventory
def add_item_to_inventory(user_id, item_id, quantity=1):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?) ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?", (user_id, item_id, quantity, quantity))
    conn.commit(); conn.close()
def remove_item_from_inventory(user_id, item_id, quantity=1):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id)); conn.commit(); conn.close()
def delete_player(user_id):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM marketplace_listings WHERE seller_id = ?", (user_id,))
    cursor.execute("DELETE FROM daily_tasks WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM player_bonds WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM players WHERE user_id = ?", (user_id,)); conn.commit(); conn.close()
def get_core_stage_info(level):
    current_stage = ("Unknown", discord.Color.default())
    for lvl, info in CORE_STAGES.items():
        if level >= lvl: current_stage = info
    return current_stage
def create_listing(seller_id, item_id, quantity, price):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("INSERT INTO marketplace_listings (seller_id, item_id, quantity, price) VALUES (?, ?, ?, ?)", (seller_id, item_id, quantity, price)); conn.commit(); conn.close()
def get_listing_by_id(listing_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT l.*, i.name as item_name, i.emoji FROM marketplace_listings l JOIN items i ON l.item_id = i.item_id WHERE listing_id = ?", (listing_id,))
    listing = cursor.fetchone(); conn.close(); return listing
def get_paged_listings(page: int, per_page: int):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    offset = (page - 1) * per_page
    cursor.execute("SELECT l.*, i.name AS item_name, i.emoji FROM marketplace_listings l JOIN items i ON l.item_id = i.item_id ORDER BY l.listed_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    listings = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM marketplace_listings"); total = cursor.fetchone()[0]; conn.close(); return listings, total
def get_listings_by_seller(seller_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT l.*, i.name as item_name, i.emoji FROM marketplace_listings l JOIN items i ON l.item_id = i.item_id WHERE l.seller_id = ?", (seller_id,))
    listings = cursor.fetchall(); conn.close(); return listings
def delete_listing(listing_id):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("DELETE FROM marketplace_listings WHERE listing_id = ?", (listing_id,)); conn.commit(); conn.close()
def get_or_generate_daily_tasks(user_id):
    today = date.today(); conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT dt.*, t.description, t.type, t.target FROM daily_tasks dt JOIN tasks t ON dt.task_id = t.task_id WHERE user_id = ? AND date_assigned = ?", (user_id, today))
    tasks = cursor.fetchall()
    if not tasks:
        cursor.execute("DELETE FROM daily_tasks WHERE user_id = ? AND date_assigned < ?", (user_id, today))
        cursor.execute("SELECT task_id FROM tasks ORDER BY RANDOM() LIMIT 3")
        new_task_ids = [row[0] for row in cursor.fetchall()]
        for task_id in new_task_ids:
            cursor.execute("INSERT INTO daily_tasks (user_id, task_id, date_assigned) VALUES (?, ?, ?)", (user_id, task_id, today))
        conn.commit()
        cursor.execute("SELECT dt.*, t.description, t.type, t.target FROM daily_tasks dt JOIN tasks t ON dt.task_id = t.task_id WHERE user_id = ? AND date_assigned = ?", (user_id, today))
        tasks = cursor.fetchall()
    conn.close(); return tasks
def update_task_progress(user_id, task_type, amount):
    today = date.today(); conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("""
        UPDATE daily_tasks SET progress = progress + ? WHERE user_id = ? AND date_assigned = ? AND is_claimed = 0 AND task_id IN (
            SELECT task_id FROM tasks WHERE type = ?)""", (amount, user_id, today, task_type))
    conn.commit(); conn.close()
def claim_task_reward(daily_task_id):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("UPDATE daily_tasks SET is_claimed = 1 WHERE id = ?", (daily_task_id,)); conn.commit(); conn.close()
def get_all_recipes():
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("""
        SELECT r.recipe_id, ci.item_id as crafted_item_id, ci.name as crafted_item_name, ci.emoji as crafted_item_emoji, r.quantity_produced,
            GROUP_CONCAT(mi.name || ':' || rm.quantity_required, ';') as materials
        FROM recipes r
        JOIN items ci ON r.crafted_item_id = ci.item_id JOIN recipe_materials rm ON r.recipe_id = rm.recipe_id
        JOIN items mi ON rm.material_item_id = mi.item_id GROUP BY r.recipe_id
    """); recipes = cursor.fetchall(); conn.close(); return recipes
def get_all_bonds():
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM bonds"); bonds = cursor.fetchall(); conn.close(); return bonds
def get_player_bonds(user_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT pb.id, pb.is_active, b.* FROM player_bonds pb JOIN bonds b ON pb.bond_id = b.bond_id WHERE pb.user_id = ?", (user_id,))
    bonds = cursor.fetchall(); conn.close(); return bonds
def get_active_bond(user_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT b.* FROM player_bonds pb JOIN bonds b ON pb.bond_id = b.bond_id WHERE pb.user_id = ? AND pb.is_active = 1", (user_id,))
    active_bond = cursor.fetchone(); conn.close(); return active_bond
def set_active_bond(user_id, player_bond_id):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("UPDATE player_bonds SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE player_bonds SET is_active = 1 WHERE id = ? AND user_id = ?", (player_bond_id, user_id))
    conn.commit(); conn.close()
def add_bond_to_player(user_id, bond_id):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO player_bonds (user_id, bond_id) VALUES (?, ?)", (user_id, bond_id))
    conn.commit(); conn.close()
def get_equipped_items(user_id):
    conn = sqlite3.connect('players.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT weapon_id, cloak_id, amulet_id, ring1_id, ring2_id FROM players WHERE user_id = ?", (user_id,))
    slots = cursor.fetchone()
    equipped = []
    if slots:
        for slot_name in slots.keys():
            item_id = slots[slot_name]
            if item_id:
                item = get_item_by_id(item_id)
                if item: equipped.append(item)
    conn.close(); return equipped
def equip_item(user_id, item_id, slot):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {slot}_id = ? WHERE user_id = ?", (item_id, user_id))
    conn.commit(); conn.close()
def unequip_item(user_id, slot):
    conn = sqlite3.connect('players.db'); cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {slot}_id = NULL WHERE user_id = ?", (user_id,))
    conn.commit(); conn.close()