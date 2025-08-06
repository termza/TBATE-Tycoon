# cogs/game_views.py

import discord
from discord.ext import commands
from discord import ui
import random
import time
from datetime import datetime, date, UTC
import math

import database

# --- Helper Functions ---
def create_progress_bar(value, max_value, length=10):
    if max_value <= 0: return "[          ]"
    percent = min(1.0, value / max_value)
    filled_length = int(length * percent)
    return f"[{'█' * filled_length}{'░' * (length - filled_length)}]"

def get_player_stats(user_id):
    player = database.get_player(user_id)
    active_bond = database.get_active_bond(user_id)
    equipped_items = database.get_equipped_items(user_id)
    stats = {
        "max_energy": database.calculate_max_energy(player['core_level']),
        "xp_boost": 1.0,
        "gold_boost": 1.0,
        "core_boost": 1.0,
    }
    if active_bond:
        if active_bond['bonus_type'] == 'max_energy_bonus': stats['max_energy'] += active_bond['bonus_value']
        elif active_bond['bonus_type'] == 'xp_boost': stats['xp_boost'] += active_bond['bonus_value']
        elif active_bond['bonus_type'] == 'gold_boost': stats['gold_boost'] += active_bond['bonus_value']
    for item in equipped_items:
        stats['max_energy'] += item['max_energy']
        stats['xp_boost'] += item['xp_boost']
        stats['gold_boost'] += item['gold_boost']
        stats['core_boost'] += item['core_boost']
    return player, stats

def create_profile_embed(player, user):
    player_data, stats = get_player_stats(user.id)
    active_bond = database.get_active_bond(user.id)
    stage_name, stage_color = database.get_core_stage_info(player_data['core_level'])
    xp_needed = database.calculate_xp_for_level(player_data['core_level'])
    embed = discord.Embed(title=stage_name, description=f"**Level:** `{player_data['core_level']}`", color=stage_color)
    embed.set_author(name=f"{user.display_name}'s Profile", icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Resources", value=f"⚡ **Energy:** `{player_data['energy']} / {int(stats['max_energy'])}`\n💎 **Beast Cores:** `{player_data['beast_cores']}`\n💰 **Gold:** `{player_data['gold']}`", inline=False)
    active_boosts = []
    if player_data['beast_lure_active']: active_boosts.append("✨ Beast Lure")
    if player_data['expedition_cost_discount_active']: active_boosts.append("🥖 Expedition Rations")
    if active_boosts: embed.add_field(name="Active Boosts", value='\n'.join(active_boosts), inline=False)
    if active_bond:
        embed.add_field(name="Active Bond", value=f"{active_bond['emoji']} **{active_bond['name']}**\n_{active_bond['description']}_", inline=True)
    xp_bonus_text = f" (+{int((stats['xp_boost']-1)*100)}%)" if stats['xp_boost'] > 1.0 else ""
    progress_bar = create_progress_bar(player_data['xp'], xp_needed)
    embed.add_field(name="✨ Experience Progress", value=f"{progress_bar} `{player_data['xp']} / {xp_needed}` XP{xp_bonus_text}", inline=False)
    embed.set_image(url="https://media1.tenor.com/m/bN2gJ2-d2jAAAAAC/the-beginning-after-the-end-tbate.gif")
    embed.set_footer(text="The Beginning After The End", icon_url="https://i.imgur.com/228q2aL.png")
    return embed

async def grant_xp(source, amount: int):
    if isinstance(source, discord.Interaction): user, channel = source.user, source.channel
    elif isinstance(source, commands.Context): user, channel = source.author, source.channel
    else: return
    _, stats = get_player_stats(user.id)
    final_amount = int(amount * stats['xp_boost'])
    player = database.get_player(user.id)
    database.update_task_progress(user.id, 'gain_xp', final_amount)
    old_level = player['core_level']; current_level = player['core_level']
    new_xp = player['xp'] + final_amount; xp_needed = database.calculate_xp_for_level(current_level)
    leveled_up = False
    while new_xp >= xp_needed:
        new_xp -= xp_needed; current_level += 1
        xp_needed = database.calculate_xp_for_level(current_level); leveled_up = True
    database.update_player(user.id, xp=new_xp, core_level=current_level)
    if leveled_up:
        level_up_embed = discord.Embed(title="LEVEL UP!", description=f"Congratulations {user.mention}, you have reached **Core Level {current_level}**!", color=discord.Color.gold())
        if channel: await channel.send(embed=level_up_embed)
        old_stage_name, _ = database.get_core_stage_info(old_level)
        new_stage_name, new_stage_color = database.get_core_stage_info(current_level)
        if old_stage_name != new_stage_name:
            guild = user.guild
            if guild:
                member = guild.get_member(user.id)
                if member:
                    try:
                        new_role_name = f"{new_stage_name} | zen"
                        new_role = discord.utils.get(guild.roles, name=new_role_name)
                        if not new_role: new_role = await guild.create_role(name=new_role_name, color=new_stage_color, hoist=True, reason="Bot auto-role")
                        for stage_level in database.CORE_STAGES:
                            stage_to_remove, _ = database.get_core_stage_info(stage_level)
                            if stage_to_remove != new_stage_name:
                                role_to_remove = discord.utils.get(guild.roles, name=f"{stage_to_remove} | zen")
                                if role_to_remove and role_to_remove in member.roles: await member.remove_roles(role_to_remove, reason="Bot stage update")
                        if new_role and new_role not in member.roles: await member.add_roles(new_role, reason="Bot stage update")
                    except discord.Forbidden: print(f"Failed to manage roles in '{guild.name}'. Missing 'Manage Roles' permission.")
                    except Exception as e: print(f"An error occurred during role management: {e}")

async def daily_logic(source):
    user = source.user if isinstance(source, discord.Interaction) else source.author
    send = source.response.send_message if isinstance(source, discord.Interaction) else source.send
    is_interaction = isinstance(source, discord.Interaction)
    player = database.get_player(user.id); cooldown = 22 * 60 * 60 
    time_since_last_daily = int(time.time()) - player['last_daily_timestamp']
    if time_since_last_daily >= cooldown:
        gold_gained = random.randint(250, 750); xp_gained = 100
        database.update_player(user.id, gold=player['gold'] + gold_gained, last_daily_timestamp=int(time.time()))
        await grant_xp(source, xp_gained)
        await send(f"🗓️ You claimed your daily reward and received **{gold_gained} Gold** and **{xp_gained} XP**!", ephemeral=is_interaction)
    else:
        time_left = cooldown - time_since_last_daily; hours, remainder = divmod(time_left, 3600); minutes, _ = divmod(remainder, 60)
        await send(f"You have already claimed. Please wait **{int(hours)}h {int(minutes)}m**.", ephemeral=is_interaction)

# --- UI Views ---
class MainView(ui.View): pass

class BackButton(ui.Button):
    def __init__(self, row, label="⬅️ Back", target_view_class_name="MainView"):
        super().__init__(label=label, style=discord.ButtonStyle.grey, row=row)
        self.target_view_class_name = target_view_class_name
    async def callback(self, interaction: discord.Interaction):
        player = database.get_player(interaction.user.id)
        embed = create_profile_embed(player, interaction.user)
        # We look up the class by its name in the current file's global scope
        target_class = globals()[self.target_view_class_name]
        
        if self.target_view_class_name == "MainView":
            view = target_class(interaction.client, player)
        else:
            view = target_class(interaction)
        
        await interaction.response.edit_message(embed=embed, view=view)

class CharacterView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180); self.interaction = interaction; self.user_id = interaction.user.id; self.add_item(BackButton(row=1, target_view_class_name="MainView"))
    @ui.button(label="Inventory", style=discord.ButtonStyle.secondary, row=0, emoji="🎒")
    async def show_inventory(self, i: discord.Interaction, b: ui.Button):
        player = database.get_player(self.user_id); await i.response.edit_message(embed=discord.Embed(title=f"{i.user.display_name}'s Inventory", color=discord.Color.blue(), description="Select an item to use."), view=InventoryView(player, i.user))
    @ui.button(label="Equipment", style=discord.ButtonStyle.secondary, row=0, emoji="🛡️")
    async def show_equipment(self, i: discord.Interaction, b: ui.Button):
        view = EquipmentView(i); await i.response.edit_message(embed=view.generate_embed(), view=view)
    @ui.button(label="Daily Tasks", style=discord.ButtonStyle.secondary, row=0, emoji="📋")
    async def show_tasks(self, i: discord.Interaction, b: ui.Button):
        view = TasksView(i); await i.response.send_message(embed=view.generate_embed(), view=view, ephemeral=True)
    @ui.button(label="Bonds", style=discord.ButtonStyle.secondary, row=0, emoji="❤️")
    async def show_bonds(self, i: discord.Interaction, b: ui.Button):
        bonds = database.get_player_bonds(self.user_id)
        embed = discord.Embed(title=f"{i.user.display_name}'s Bonds", description="Select a bond to make it your active companion, providing you with a passive bonus.", color=discord.Color.red())
        if not bonds: embed.description = "You haven't formed any bonds yet. Explore dangerous locations like The Relictombs to find them."
        await i.response.edit_message(embed=embed, view=BondsView(i))

class InventoryView(ui.View):
    def __init__(self, player, user):
        super().__init__(timeout=180)
        self.user_id = player['user_id']; self.user = user; self.selected_item = None
        self.add_item(self.create_item_dropdown()); self.add_item(BackButton(row=1, target_view_class_name="CharacterView"))
    def create_item_dropdown(self):
        inventory = database.get_inventory(self.user_id)
        options = [discord.SelectOption(label=f"{item['emoji'] or ''} {item['name']} (x{item['quantity']})", value=item['name'], description=item['description'][:100]) for item in inventory] if inventory else [discord.SelectOption(label="Your inventory is empty.", value="empty")]
        dropdown = ui.Select(placeholder="Select an item to use...", options=options, disabled=(not inventory))
        dropdown.callback = self.on_dropdown_select
        return dropdown
    async def on_dropdown_select(self, interaction: discord.Interaction): self.selected_item = interaction.data['values'][0]; await interaction.response.defer()
    @ui.button(label="✔️ Use Selected Item", style=discord.ButtonStyle.green, row=1)
    async def use_item_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id: return
        if not self.selected_item or self.selected_item == "empty": return await interaction.response.send_message("Please select an item.", ephemeral=True)
        item_to_use = database.get_item_by_name(self.selected_item); player = database.get_player(self.user_id)
        if item_to_use['item_type'] != 'consumable': return await interaction.response.send_message("This item is not usable.", ephemeral=True)
        database.remove_item_from_inventory(self.user_id, item_to_use['item_id']); msg = "This item cannot be used."
        if item_to_use['name'] == "Stamina Potion": _, stats = get_player_stats(self.user_id); database.update_player(self.user_id, energy=min(int(stats['max_energy']), player['energy'] + 25)); msg = f"🧪 Used **Stamina Potion**, restored 25 energy!"
        elif item_to_use['name'] == "Greater Stamina Potion": _, stats = get_player_stats(self.user_id); database.update_player(self.user_id, energy=min(int(stats['max_energy']), player['energy'] + 50)); msg = f"🧪 Used **Greater Stamina Potion**, restored 50 energy!"
        elif item_to_use['name'] == "Superior Stamina Potion": _, stats = get_player_stats(self.user_id); database.update_player(self.user_id, energy=min(int(stats['max_energy']), player['energy'] + 100)); msg = f"🧪 Used **Superior Stamina Potion**, restored 100 energy!"
        elif item_to_use['name'] == "Beast Lure": database.update_player(self.user_id, beast_lure_active=1); msg = "✨ Activated **Beast Lure**!"
        elif item_to_use['name'] == "Expedition Rations": database.update_player(self.user_id, expedition_cost_discount_active=1); msg = "🥖 Consumed **Expedition Rations**."
        elif item_to_use['name'] == "Small XP Scroll": await grant_xp(interaction, 250); msg = "📜 Used a **Small XP Scroll** and gained 250 XP!"
        elif item_to_use['name'] == "Medium XP Scroll": await grant_xp(interaction, 1000); msg = "📜 Used a **Medium XP Scroll** and gained 1000 XP!"
        elif item_to_use['name'] == "Large XP Scroll": await grant_xp(interaction, 5000); msg = "📜 Used a **Large XP Scroll** and gained 5000 XP!"
        elif item_to_use['name'] == "Tome of Wealth": database.update_player(self.user_id, gold=player['gold'] + 1000); msg = "📖 You read the **Tome of Wealth** and gained 1000 Gold!"
        else: database.add_item_to_inventory(self.user_id, item_to_use['item_id'])
        await interaction.response.send_message(msg, ephemeral=True)
        new_player_data = database.get_player(self.user_id)
        await interaction.message.edit(embed=discord.Embed(title=f"{self.user.display_name}'s Inventory", color=discord.Color.blue(), description="Select an item from the dropdown and click 'Use'."), view=InventoryView(new_player_data, self.user))

# ... All other View classes are included here, unabridged ...

class MainView(ui.View):
    def __init__(self, bot, player):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = player['user_id']; self.update_buttons(player)
    def update_buttons(self, player):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and getattr(item, 'custom_id', None) == 'expedition':
                item.disabled = player['energy'] < 10
    async def refresh_ui(self, i: discord.Interaction):
        player = database.get_player(self.user_id); self.update_buttons(player)
        await i.message.edit(embed=create_profile_embed(player, i.user), view=self)
    @ui.button(label="⚔️ Expeditions", style=discord.ButtonStyle.green, custom_id="expedition", row=0)
    async def expedition(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user_id: return
        await i.response.edit_message(embed=discord.Embed(title="Choose Your Expedition", description="Where will you venture?", color=discord.Color.dark_green()), view=ExpeditionView(i))
    @ui.button(label="⚖️ Sell All Cores", style=discord.ButtonStyle.blurple, custom_id="sell", row=0)
    async def sell(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user_id: return
        player, stats = get_player_stats(self.user_id)
        if player['beast_cores'] == 0: return await i.response.send_message("You have no cores to sell.", ephemeral=True)
        gold_earned = int(player['beast_cores'] * 10 * stats['gold_boost'])
        database.update_player(self.user_id, beast_cores=0, gold=player['gold'] + gold_earned)
        database.update_task_progress(self.user_id, 'sell_cores', player['beast_cores'])
        database.update_task_progress(self.user_id, 'earn_gold', gold_earned)
        await i.response.send_message(f"⚖️ You sold **{player['beast_cores']}** 💎 for **{gold_earned}** 💰 gold!", ephemeral=True); await self.refresh_ui(i)
    @ui.select(placeholder="Open a Menu...", row=1, options=[
        discord.SelectOption(label="Character", value="character", emoji="👤", description="Inventory, Equipment, Tasks, Bonds"),
        discord.SelectOption(label="Actions", value="actions", emoji="🎲", description="Crafting, Minigame, Daily"),
        discord.SelectOption(label="Economy", value="economy", emoji="📈", description="Shop, Market, Give"),
        discord.SelectOption(label="Community", value="community", emoji="🏆", description="Leaderboard")
    ])
    async def menu_select(self, interaction: discord.Interaction, select: ui.Select):
        if interaction.user.id != self.user_id: return
        selection = select.values[0]; embed = interaction.message.embeds[0]
        if selection == "character": await interaction.response.edit_message(embed=embed, view=CharacterView(interaction))
        elif selection == "actions": await interaction.response.edit_message(embed=embed, view=ActionsView(interaction))
        elif selection == "economy": await interaction.response.edit_message(embed=embed, view=EconomyView(interaction))
        elif selection == "community": await interaction.response.edit_message(embed=embed, view=CommunityView(interaction))