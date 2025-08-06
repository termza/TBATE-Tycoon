# main.py

import discord
from discord.ext import commands
from discord import ui
import os
import random
import time
from datetime import datetime, date, UTC # BUG FIX: Import UTC
import math
from dotenv import load_dotenv

import database
import items

# --- Helper Functions ---
def create_progress_bar(value, max_value, length=10):
    if max_value <= 0: return "[          ]"
    percent = min(1.0, value / max_value)
    filled_length = int(length * percent)
    return f"[{'█' * filled_length}{'░' * (length - filled_length)}]"

def create_profile_embed(player, user):
    active_bond = database.get_active_bond(user.id)
    stage_name, stage_color = database.get_core_stage_info(player['core_level'])
    energy_bonus = active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'max_energy_bonus' else 0
    max_energy = database.calculate_max_energy(player['core_level']) + energy_bonus
    xp_needed = database.calculate_xp_for_level(player['core_level'])
    embed = discord.Embed(title=stage_name, description=f"**Level:** `{player['core_level']}`", color=stage_color)
    embed.set_author(name=f"{user.display_name}'s Profile", icon_url=user.display_avatar.url)
    embed.add_field(name="Resources", value=f"⚡ **Energy:** `{player['energy']} / {int(max_energy)}`\n💎 **Beast Cores:** `{player['beast_cores']}`\n💰 **Gold:** `{player['gold']}`", inline=False)
    active_boosts = []
    if player['beast_lure_active']: active_boosts.append("✨ Beast Lure")
    if player['expedition_cost_discount_active']: active_boosts.append("🥖 Expedition Rations")
    if active_boosts: embed.add_field(name="Active Boosts", value='\n'.join(active_boosts), inline=False)
    if active_bond:
        embed.add_field(name="Active Bond", value=f"{active_bond['emoji']} **{active_bond['name']}**\n_{active_bond['description']}_", inline=True)
    xp_bonus = 1.0 + active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'xp_boost' else 1.0
    progress_bar = create_progress_bar(player['xp'], xp_needed)
    embed.add_field(name="✨ Experience Progress", value=f"{progress_bar} `{player['xp']} / {xp_needed}` XP" + (f" (+{int((xp_bonus-1)*100)}%)" if xp_bonus > 1.0 else ""), inline=False)
    embed.set_footer(text="The Beginning After The End Tycoon | Use $profile")
    return embed

async def grant_xp(source, amount: int):
    if isinstance(source, discord.Interaction): user, channel = source.user, source.channel
    elif isinstance(source, commands.Context): user, channel = source.author, source.channel
    else: return
    active_bond = database.get_active_bond(user.id)
    xp_bonus = 1.0 + active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'xp_boost' else 1.0
    final_amount = int(amount * xp_bonus)
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

# --- UI Views ---
class MainView(ui.View): pass
class BackButton(ui.Button):
    def __init__(self, row):
        super().__init__(label="⬅️ Back", style=discord.ButtonStyle.grey, row=row)
    async def callback(self, interaction: discord.Interaction):
        player = database.get_player(interaction.user.id); embed = create_profile_embed(player, interaction.user)
        view = MainView(player); await interaction.response.edit_message(embed=embed, view=view)

class CharacterView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180); self.interaction = interaction; self.user_id = interaction.user.id; self.add_item(BackButton(row=1))
    @ui.button(label="Inventory", style=discord.ButtonStyle.secondary, row=0, emoji="🎒")
    async def show_inventory(self, i: discord.Interaction, b: ui.Button):
        player = database.get_player(self.user_id); await i.response.edit_message(embed=discord.Embed(title=f"{i.user.display_name}'s Inventory", color=discord.Color.blue(), description="Select an item to use."), view=InventoryView(player, i.user))
    @ui.button(label="Daily Tasks", style=discord.ButtonStyle.secondary, row=0, emoji="📋")
    async def show_tasks(self, i: discord.Interaction, b: ui.Button):
        view = TasksView(i); await i.response.send_message(embed=view.generate_embed(), view=view, ephemeral=True)
    @ui.button(label="Bonds", style=discord.ButtonStyle.secondary, row=0, emoji="❤️")
    async def show_bonds(self, i: discord.Interaction, b: ui.Button):
        bonds = database.get_player_bonds(self.user_id)
        embed = discord.Embed(title=f"{i.user.display_name}'s Bonds", description="Select a bond to make it your active companion, providing you with a passive bonus.", color=discord.Color.red())
        if not bonds: embed.description = "You haven't formed any bonds yet. Explore dangerous locations like The Relictombs to find them."
        await i.response.edit_message(embed=embed, view=BondsView(i))

# --- All other View classes go here ---
# (I will now fill in the rest of the classes completely)

class InventoryView(ui.View):
    def __init__(self, player, user):
        super().__init__(timeout=180)
        self.user_id = player['user_id']; self.user = user; self.selected_item = None
        self.add_item(self.create_item_dropdown()); self.add_item(BackButton(row=1))
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
        if item_to_use['name'] == "Stamina Potion": max_e = database.calculate_max_energy(player['core_level']); database.update_player(self.user_id, energy=min(int(max_e), player['energy'] + 25)); msg = f"🧪 Used **Stamina Potion**, restored 25 energy!"
        elif item_to_use['name'] == "Greater Stamina Potion": max_e = database.calculate_max_energy(player['core_level']); database.update_player(self.user_id, energy=min(int(max_e), player['energy'] + 50)); msg = f"🧪 Used **Greater Stamina Potion**, restored 50 energy!"
        elif item_to_use['name'] == "Superior Stamina Potion": max_e = database.calculate_max_energy(player['core_level']); database.update_player(self.user_id, energy=min(int(max_e), player['energy'] + 100)); msg = f"🧪 Used **Superior Stamina Potion**, restored 100 energy!"
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

class MinigameView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id; self.beasts = ["Snapper", "Grappler", "Glaudr"]; self.correct_answer = random.choice(self.beasts)
    async def check_answer(self, interaction: discord.Interaction, guess: str):
        if interaction.user.id != self.user_id: return
        for child in self.children: child.disabled = True
        if guess == self.correct_answer:
            database.update_task_progress(self.user_id, 'win_minigame', 1)
            loot_table = ["Stamina Potion", "Beast Lure", "Expedition Rations", "Broken Beast Horn", "Mana Infused Hide", "Small XP Scroll", "Glow Moss"]
            item_won_name = random.choice(loot_table)
            item_won = database.get_item_by_name(item_won_name); database.add_item_to_inventory(self.user_id, item_won['item_id'])
            xp_gained = 50; await grant_xp(interaction, xp_gained)
            embed = discord.Embed(title="Correct!", description=f"You received **1x {item_won['name']}** and **{xp_gained} XP**!", color=discord.Color.green())
        else: embed = discord.Embed(title="Incorrect!", description=f"The beast was **{self.correct_answer}**.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=self)
    @ui.button(label="Snapper")
    async def snapper_button(self, i, b): await self.check_answer(i, "Snapper")
    @ui.button(label="Grappler")
    async def grappler_button(self, i, b): await self.check_answer(i, "Grappler")
    @ui.button(label="Glaudr")
    async def glaudr_button(self, i, b): await self.check_answer(i, "Glaudr")

class ShopView(ui.View):
    def __init__(self, user_id, shop_items):
        super().__init__(timeout=300)
        self.user_id = user_id; self.shop_items = {item['name']: item for item in shop_items}; self.selected_item_name = None
        options = [discord.SelectOption(label=f"{item['emoji'] or ''} {item['name']} - {item['price']} Gold", value=item['name']) for item in shop_items]
        dropdown = ui.Select(placeholder="Select an item to purchase...", options=options); dropdown.callback = self.on_dropdown_select; self.add_item(dropdown)
    async def on_dropdown_select(self, interaction: discord.Interaction): self.selected_item_name = interaction.data['values'][0]; await interaction.response.defer()
    @ui.button(label="Buy Selected Item", style=discord.ButtonStyle.green)
    async def buy_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id: return
        if not self.selected_item_name: return await interaction.response.send_message("Please select an item to buy.", ephemeral=True)
        player = database.get_player(self.user_id); item_to_buy = self.shop_items.get(self.selected_item_name)
        if player['gold'] < item_to_buy['price']: return await interaction.response.send_message(f"You don't have enough gold! You need {item_to_buy['price']} gold.", ephemeral=True)
        database.update_player(self.user_id, gold=player['gold'] - item_to_buy['price']); database.add_item_to_inventory(self.user_id, item_to_buy['item_id'])
        await interaction.response.send_message(f"✅ You purchased **1x {item_to_buy['name']}** for {item_to_buy['price']} gold.", ephemeral=True)

class GiveModal(ui.Modal, title="Give to Another Player"):
    target_user_id = ui.TextInput(label="Recipient's User ID", required=True); item_name = ui.TextInput(label="Item Name (or 'gold')", required=True); amount = ui.TextInput(label="Amount / Quantity", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        initiator_id = interaction.user.id
        try: partner_id = int(self.target_user_id.value); amount_val = int(self.amount.value)
        except ValueError: return await interaction.response.send_message("❌ User ID and Amount must be numbers.", ephemeral=True)
        if partner_id == initiator_id: return await interaction.response.send_message("You can't give items to yourself.", ephemeral=True)
        partner = interaction.guild.get_member(partner_id)
        if not partner or partner.bot: return await interaction.response.send_message("❌ Could not find that user or they are a bot.", ephemeral=True)
        initiator_player = database.get_player(initiator_id); item_name_str = self.item_name.value
        if item_name_str.lower() == 'gold':
            if amount_val <= 0: return await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            if initiator_player['gold'] < amount_val: return await interaction.response.send_message("You don't have that much gold.", ephemeral=True)
            partner_player = database.get_player(partner_id)
            database.update_player(initiator_id, gold=initiator_player['gold'] - amount_val); database.update_player(partner_id, gold=partner_player['gold'] + amount_val)
            await interaction.response.send_message(f"✅ You gave **{amount_val} Gold** to {partner.display_name}.", ephemeral=True)
        else:
            item = database.get_item_by_name(item_name_str)
            if not item: return await interaction.response.send_message("That item doesn't exist.", ephemeral=True)
            if not item['tradeable']: return await interaction.response.send_message("This item cannot be traded.", ephemeral=True)
            if amount_val <= 0: return await interaction.response.send_message("Quantity must be positive.", ephemeral=True)
            inv = database.get_inventory(initiator_id); user_item = next((i for i in inv if i['name'].lower() == item_name_str.lower()), None)
            if not user_item or user_item['quantity'] < amount_val: return await interaction.response.send_message(f"You don't have {amount_val}x {item['name']}.", ephemeral=True)
            database.remove_item_from_inventory(initiator_id, item['item_id'], amount_val); database.add_item_to_inventory(partner_id, item['item_id'], amount_val)
            await interaction.response.send_message(f"✅ You gave **{amount_val}x {item['name']}** to {partner.display_name}.", ephemeral=True)

class MarketView(ui.View):
    def __init__(self, source, page: int = 1):
        super().__init__(timeout=300)
        if isinstance(source, discord.Interaction): self.bot = source.client; self.user = source.user
        else: self.bot = source.bot; self.user = source.author
        self.current_page = page; self.per_page = 5; self.listings, self.total_listings = database.get_paged_listings(page, self.per_page)
        self.total_pages = math.ceil(self.total_listings / self.per_page) or 1; self.update_components()
    def update_components(self):
        self.clear_items(); prev_button = ui.Button(label="⬅️", style=discord.ButtonStyle.grey, disabled=(self.current_page <= 1)); prev_button.callback = self.prev_page; self.add_item(prev_button)
        next_button = ui.Button(label="➡️", style=discord.ButtonStyle.grey, disabled=(self.current_page >= self.total_pages)); next_button.callback = self.next_page; self.add_item(next_button)
        if self.listings:
            # BUG FIX: Use safe key access
            options = [discord.SelectOption(label=f"Buy {l['quantity']}x {l['item_name']} ({l['price']} G)", value=str(l['listing_id']), emoji=(l['emoji'] if 'emoji' in l.keys() else None)) for l in self.listings if l['seller_id'] != self.user.id]
            if options:
                buy_dropdown = ui.Select(placeholder="Select a listing to purchase...", options=options); buy_dropdown.callback = self.buy_item; self.add_item(buy_dropdown)
    async def generate_embed(self):
        embed = discord.Embed(title="Player Marketplace", color=discord.Color.blue())
        if not self.listings: embed.description = "The marketplace is currently empty."
        else:
            description_lines = []
            for listing in self.listings:
                try: seller = await self.bot.fetch_user(listing['seller_id'])
                except discord.NotFound: seller_name = "Unknown Seller"
                else: seller_name = seller.display_name
                # BUG FIX: Use safe key access
                emoji = listing['emoji'] if 'emoji' in listing.keys() else ''
                description_lines.append(f"{emoji or ''} **{listing['quantity']}x {listing['item_name']}** for `{listing['price']}` Gold\n*Sold by: {seller_name}* (ID: `{listing['listing_id']}`)")
            embed.description = "\n\n".join(description_lines)
        embed.set_footer(text=f"Page {self.current_page} of {self.total_pages}"); return embed
    async def prev_page(self, i: discord.Interaction):
        self.current_page -= 1; self.listings, _ = database.get_paged_listings(self.current_page, self.per_page); self.update_components(); await i.response.edit_message(embed=await self.generate_embed(), view=self)
    async def next_page(self, i: discord.Interaction):
        self.current_page += 1; self.listings, _ = database.get_paged_listings(self.current_page, self.per_page); self.update_components(); await i.response.edit_message(embed=await self.generate_embed(), view=self)
    async def buy_item(self, i: discord.Interaction):
        listing_id = int(i.data['values'][0]); listing = database.get_listing_by_id(listing_id)
        if not listing: return await i.response.send_message("❌ This listing no longer exists.", ephemeral=True)
        buyer = database.get_player(i.user.id)
        if buyer['gold'] < listing['price']: return await i.response.send_message("❌ You don't have enough gold.", ephemeral=True)
        seller = database.get_player(listing['seller_id'])
        database.update_player(buyer['user_id'], gold=buyer['gold'] - listing['price']); database.update_player(seller['user_id'], gold=seller['gold'] + listing['price'])
        database.add_item_to_inventory(buyer['user_id'], listing['item_id'], listing['quantity']); database.delete_listing(listing_id)
        await i.response.send_message(f"✅ You purchased **{listing['quantity']}x {listing['item_name']}**!", ephemeral=True)
        self.listings, self.total_listings = database.get_paged_listings(self.current_page, self.per_page)
        self.total_pages = math.ceil(self.total_listings / self.per_page) or 1; self.update_components(); await i.message.edit(embed=await self.generate_embed(), view=self)

class MyListingsView(ui.View):
    def __init__(self, source):
        super().__init__(timeout=180)
        self.user = source.user if isinstance(source, discord.Interaction) else source.author; self.update_components()
    def update_components(self):
        self.clear_items(); self.listings = database.get_listings_by_seller(self.user.id)
        if self.listings:
            # BUG FIX: Use safe key access
            options = [discord.SelectOption(label=f"Cancel: {l['quantity']}x {l['item_name']} ({l['price']} G)", value=str(l['listing_id']), emoji=(l['emoji'] if 'emoji' in l.keys() else None)) for l in self.listings]
            cancel_dropdown = ui.Select(placeholder="Select a listing to cancel...", options=options); cancel_dropdown.callback = self.cancel_listing; self.add_item(cancel_dropdown)
    async def cancel_listing(self, i: discord.Interaction):
        listing_id = int(i.data['values'][0]); listing_to_cancel = database.get_listing_by_id(listing_id)
        if not listing_to_cancel or listing_to_cancel['seller_id'] != self.user.id: return await i.response.send_message("❌ Listing not valid.", ephemeral=True)
        database.delete_listing(listing_id); database.add_item_to_inventory(self.user.id, listing_to_cancel['item_id'], listing_to_cancel['quantity'])
        await i.response.send_message(f"✅ Your listing has been canceled.", ephemeral=True)
        self.update_components(); embed = discord.Embed(title="Your Active Listings", color=discord.Color.orange())
        if not self.listings: embed.description = "You have no active listings."
        else:
            # BUG FIX: Use safe key access
            desc = [f"ID: `{l['listing_id']}` - {l['emoji'] if 'emoji' in l.keys() else ''} **{l['quantity']}x {l['item_name']}** for `{l['price']}` Gold" for l in self.listings]
            embed.description = "\n".join(desc)
        await i.message.edit(embed=embed, view=self)

class SetPriceModal(ui.Modal, title="Set Price and Quantity"):
    quantity = ui.TextInput(label="Quantity to Sell", required=True)
    price = ui.TextInput(label="Total Price in Gold for the stack", required=True)
    async def on_submit(self, interaction: discord.Interaction): await interaction.response.defer(ephemeral=True, thinking=False)

class PostItemView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180)
        self.user_id = interaction.user.id; self.selected_item = None
        self.add_item(self.create_inventory_dropdown()); self.add_item(BackButton(row=2))
    def create_inventory_dropdown(self):
        inventory = [item for item in database.get_inventory(self.user_id) if database.get_item_by_name(item['name'])['tradeable']]
        options = [discord.SelectOption(label=f"{item['emoji'] or ''} {item['name']} (x{item['quantity']})", value=str(item['item_id'])) for item in inventory] if inventory else [discord.SelectOption(label="No tradeable items in inventory.", value="none")]
        select = ui.Select(placeholder="Select an item to sell...", options=options, disabled=(not inventory))
        select.callback = self.on_item_select
        return select
    async def on_item_select(self, interaction: discord.Interaction):
        if interaction.data['values'][0] == 'none': return await interaction.response.defer()
        item_id = int(interaction.data['values'][0])
        self.selected_item = next((i for i in database.get_inventory(self.user_id) if i['item_id'] == item_id), None)
        for child in self.children:
            if isinstance(child, ui.Button) and child.label == "Set Price & Quantity": child.disabled = False
        await interaction.response.edit_message(view=self)
    @ui.button(label="Set Price & Quantity", style=discord.ButtonStyle.green, row=1, disabled=True)
    async def set_price_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.selected_item: return
        modal = SetPriceModal(); await interaction.response.send_modal(modal); await modal.wait()
        try: qty_val = int(modal.quantity.value); price_val = int(modal.price.value)
        except (ValueError, TypeError): return await interaction.followup.send("❌ Invalid input.", ephemeral=True)
        if qty_val > 0 and price_val >= 0:
            player_item = next((i for i in database.get_inventory(self.user_id) if i['item_id'] == self.selected_item['item_id']), None)
            if player_item and player_item['quantity'] >= qty_val:
                database.remove_item_from_inventory(self.user_id, self.selected_item['item_id'], qty_val)
                database.create_listing(self.user_id, self.selected_item['item_id'], qty_val, price_val)
                await interaction.followup.send(f"✅ Listed **{qty_val}x {self.selected_item['name']}** for **{price_val} gold**.", ephemeral=True)
            else: await interaction.followup.send(f"❌ You don't have enough {self.selected_item['name']}.", ephemeral=True)
        else: await interaction.followup.send("❌ Quantity must be positive and price cannot be negative.", ephemeral=True)
        await interaction.message.edit(view=EconomyView(interaction))

class ExpeditionView(ui.View):
    def __init__(self, main_view_interaction: discord.Interaction):
        super().__init__(timeout=180); self.main_view_interaction = main_view_interaction; self.user_id = main_view_interaction.user.id
    async def handle_expedition(self, interaction: discord.Interaction, location: str, cost: int, xp_range: tuple, core_multiplier: float, item_chances: dict, bond_chance: float):
        if interaction.user.id != self.user_id: return
        player = database.get_player(self.user_id)
        if player['energy'] < cost: return await interaction.response.send_message(f"You need {cost} energy.", ephemeral=True)
        database.update_player(self.user_id, energy=player['energy'] - cost); database.update_task_progress(self.user_id, 'expedition', 1)
        xp_gained = random.randint(xp_range[0], xp_range[1]); cores_found = int(random.randint(5, 15) * core_multiplier * player['core_level'])
        if xp_gained > 0: await grant_xp(interaction, xp_gained)
        database.update_player(self.user_id, beast_cores=player['beast_cores'] + cores_found)
        msg = f"🌲 You spent {cost} energy exploring **{location}**, finding **{cores_found}** cores"
        if xp_gained > 0: msg += f" and gaining **{xp_gained}** XP."
        else: msg += "."
        for item_name, chance in item_chances.items():
            if random.random() < chance:
                item = database.get_item_by_name(item_name); database.add_item_to_inventory(self.user_id, item['item_id'])
                msg += f"\n\n**You found something!** A {item['emoji'] or ''} **{item['name']}**!"
        if random.random() < bond_chance:
            all_bonds = database.get_all_bonds(); found_bond = random.choice(all_bonds)
            database.add_bond_to_player(self.user_id, found_bond['bond_id'])
            msg += f"\n\n**You've formed a new bond!** You are now bonded with {found_bond['emoji']} **{found_bond['name']}**!"
        await interaction.response.send_message(msg, ephemeral=True)
        player = database.get_player(self.user_id)
        await self.main_view_interaction.message.edit(embed=create_profile_embed(player, interaction.user), view=MainView(player)); self.stop()
    @ui.button(label="Beast Glades (10⚡)", style=discord.ButtonStyle.green)
    async def beast_glades(self, i, b): await self.handle_expedition(i, "Beast Glades", 10, (15, 30), 1.0, {"Broken Beast Horn": 0.2, "Mana Infused Hide": 0.05}, 0.0)
    @ui.button(label="Elven Forest (15⚡)", style=discord.ButtonStyle.primary)
    async def elven_forest(self, i, b): await self.handle_expedition(i, "Elven Forest", 15, (10, 20), 0.5, {"Glow Moss": 0.2, "Sunpetal Leaf": 0.1, "Elderwood Heart": 0.02}, 0.0)
    @ui.button(label="Dwarven Mines (20⚡)", style=discord.ButtonStyle.secondary)
    async def dwarven_mines(self, i, b): await self.handle_expedition(i, "Dwarven Mines", 20, (0, 0), 2.5, {"Iron Ore": 0.3, "Silver Ore": 0.1, "Gold Ore": 0.03}, 0.0)
    @ui.button(label="The Wall (30⚡)", style=discord.ButtonStyle.danger, row=1)
    async def the_wall(self, i, b): await self.handle_expedition(i, "The Wall", 30, (100, 200), 1.2, {"Wyvern Claw": 0.08, "Glaudr Scale": 0.02}, 0.005)
    @ui.button(label="The Relictombs (50⚡)", style=discord.ButtonStyle.blurple, row=1)
    async def relictombs(self, i, b): await self.handle_expedition(i, "The Relictombs", 50, (250, 500), 0.1, {"Aetheric Crystal": 0.1, "Perfect Mana Crystal": 0.05}, 0.01)
    @ui.button(label="Back", style=discord.ButtonStyle.grey, row=2)
    async def back(self, interaction: discord.Interaction, button: ui.Button):
        player = database.get_player(self.user_id); await interaction.response.edit_message(embed=create_profile_embed(player, interaction.user), view=MainView(player))

class TasksView(ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300); self.user = interaction.user; self.update_components()
    def update_components(self):
        self.clear_items(); self.tasks = database.get_or_generate_daily_tasks(self.user.id); options = []
        for task in self.tasks:
            if task['progress'] >= task['target'] and not task['is_claimed']:
                options.append(discord.SelectOption(label=f"Claim: {task['description']}", value=str(task['id'])))
        if options:
            dropdown = ui.Select(placeholder="Select a completed task to claim...", options=options); dropdown.callback = self.claim_reward; self.add_item(dropdown)
    def generate_embed(self):
        embed = discord.Embed(title=f"📅 {self.user.display_name}'s Daily Tasks", color=discord.Color.dark_teal()); description = []
        for task in self.tasks:
            progress = min(task['progress'], task['target']); status_emoji = "✅" if progress >= task['target'] else "❌"
            if task['is_claimed']: status_emoji = "🎉"
            description.append(f"{status_emoji} **{task['description']}** ({progress}/{task['target']})")
        embed.description = "\n".join(description); embed.set_footer(text="Tasks reset daily."); return embed
    async def claim_reward(self, interaction: discord.Interaction):
        daily_task_id = int(interaction.data['values'][0]); task_to_claim = next((t for t in self.tasks if t['id'] == daily_task_id), None)
        gold_reward = 1000; xp_reward = 250; player = database.get_player(self.user.id)
        database.update_player(self.user.id, gold=player['gold'] + gold_reward); await grant_xp(interaction, xp_reward); database.claim_task_reward(daily_task_id)
        await interaction.response.send_message(f"🎉 You claimed the reward for '{task_to_claim['description']}' and received **{gold_reward}G** and **{xp_reward}XP**!", ephemeral=True)
        self.update_components(); await interaction.message.edit(embed=self.generate_embed(), view=self)

class CraftingView(ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.interaction = interaction; self.user_id = interaction.user.id; self.recipes = database.get_all_recipes(); self.selected_recipe = None
        self.inventory = {item['name']: item['quantity'] for item in database.get_inventory(self.user_id)}
        self.add_item(self.create_recipe_dropdown()); self.add_item(BackButton(row=2))
    def create_recipe_dropdown(self):
        options = [discord.SelectOption(label=f"Craft: {r['crafted_item_emoji'] or ''} {r['crafted_item_name']}", value=str(r['recipe_id'])) for r in self.recipes]
        select = ui.Select(placeholder="Select a recipe to view...", options=options); select.callback = self.on_select_recipe; return select
    def generate_embed(self):
        embed = discord.Embed(title="🛠️ Crafting Bench", color=discord.Color.from_rgb(139, 69, 19))
        if not self.selected_recipe: embed.description = "Select a recipe to see its materials."
        else:
            embed.description = f"**Recipe for: {self.selected_recipe['quantity_produced']}x {self.selected_recipe['crafted_item_emoji'] or ''} {self.selected_recipe['crafted_item_name']}**"
            materials_text = []
            for material in self.selected_recipe['materials'].split(';'):
                name, qty = material.split(':'); have = self.inventory.get(name, 0)
                emoji = "✅" if have >= int(qty) else "❌"
                materials_text.append(f"{emoji} {name}: {have}/{qty}")
            embed.add_field(name="Required Materials", value="\n".join(materials_text))
        return embed
    async def on_select_recipe(self, interaction: discord.Interaction):
        recipe_id = int(interaction.data['values'][0])
        self.selected_recipe = next((r for r in self.recipes if r['recipe_id'] == recipe_id), None)
        await self.update_view(interaction)
    @ui.button(label="Craft Item", style=discord.ButtonStyle.green, row=1, disabled=True)
    async def craft_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.selected_recipe: return
        for material in self.selected_recipe['materials'].split(';'):
            name, qty_needed = material.split(':')
            if self.inventory.get(name, 0) < int(qty_needed): return await interaction.response.send_message("You no longer have the materials.", ephemeral=True)
        for material in self.selected_recipe['materials'].split(';'):
            name, qty = material.split(':'); item = database.get_item_by_name(name)
            database.remove_item_from_inventory(self.user_id, item['item_id'], int(qty))
        crafted_item = database.get_item_by_id(self.selected_recipe['crafted_item_id'])
        database.add_item_to_inventory(self.user_id, crafted_item['item_id'], self.selected_recipe['quantity_produced'])
        database.update_task_progress(self.user_id, 'craft_item', 1)
        await interaction.response.send_message(f"✨ You successfully crafted **{self.selected_recipe['quantity_produced']}x {crafted_item['name']}**!", ephemeral=True)
        await self.update_view(interaction)
    async def update_view(self, interaction: discord.Interaction):
        new_view = CraftingView(interaction); new_view.selected_recipe = self.selected_recipe
        await interaction.response.edit_message(embed=new_view.generate_embed(), view=new_view)

class BondsView(ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.user = interaction.user; self.add_item(self.create_bond_dropdown()); self.add_item(BackButton(row=1))
    def create_bond_dropdown(self):
        bonds = database.get_player_bonds(self.user.id)
        options = [discord.SelectOption(label=f"Activate {bond['name']}", value=str(bond['id']), emoji=bond['emoji'], default=bool(bond['is_active'])) for bond in bonds]
        if not options: options.append(discord.SelectOption(label="You have no bonds yet.", value="none"))
        select = ui.Select(placeholder="Select a bond to make active...", options=options, disabled=(not bonds))
        select.callback = self.on_bond_select
        return select
    async def on_bond_select(self, interaction: discord.Interaction):
        if interaction.data['values'][0] != 'none':
            player_bond_id = int(interaction.data['values'][0])
            database.set_active_bond(self.user.id, player_bond_id)
            await interaction.response.send_message("✅ Your active bond has been updated!", ephemeral=True)
            await interaction.message.edit(view=BondsView(interaction))
        else: await interaction.response.defer()

class ActionsView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180); self.interaction = interaction; self.user_id = interaction.user.id; self.add_item(BackButton(row=1))
    @ui.button(label="Crafting", style=discord.ButtonStyle.secondary, row=0, emoji="🛠️")
    async def crafting_button(self, i: discord.Interaction, b: ui.Button): view = CraftingView(i); await i.response.edit_message(embed=view.generate_embed(), view=view)
    @ui.button(label="Minigame", style=discord.ButtonStyle.secondary, row=0, emoji="🎲")
    async def play_minigame(self, i: discord.Interaction, b: ui.Button):
        cost = 20; player = database.get_player(self.user_id)
        if player['energy'] < cost: return await i.response.send_message(f"You need {cost} energy to play.", ephemeral=True)
        database.update_player(self.user_id, energy=player['energy'] - cost)
        embed = discord.Embed(title="🎲 Guess the Mana Beast!", color=discord.Color.dark_purple()); embed.set_footer(text=f"This cost you {cost} energy.")
        await i.response.send_message(embed=embed, view=MinigameView(self.user_id), ephemeral=True)
    @ui.button(label="Claim Daily", style=discord.ButtonStyle.secondary, row=0, emoji="🗓️")
    async def claim_daily(self, i: discord.Interaction, b: ui.Button): await daily_logic(i)

class EconomyView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180); self.interaction = interaction; self.user_id = interaction.user.id; self.add_item(BackButton(row=1))
    @ui.button(label="Hourly Shop", style=discord.ButtonStyle.secondary, row=0, emoji="🛒")
    async def shop_button(self, i: discord.Interaction, b: ui.Button):
        now = datetime.now(UTC); random.seed(f"{now.year}-{now.month}-{now.day}-{now.hour}")
        all_items = database.get_all_items(); shop_items_pool = [item for item in all_items if item['item_type'] != 'material' and "Tome of Wealth" not in item['name']]
        random.shuffle(shop_items_pool); shop_items = shop_items_pool[:5]
        embed = discord.Embed(title="Hourly Shop", description=f"Items refresh in **{60 - now.minute} minutes**.", color=discord.Color.green())
        for item in shop_items: embed.add_field(name=f"{item['emoji'] or ''} {item['name']} - {item['price']} Gold", value=item['description'], inline=False)
        await i.response.send_message(embed=embed, view=ShopView(self.user_id, shop_items), ephemeral=True)
    @ui.button(label="Player Market", style=discord.ButtonStyle.secondary, row=0, emoji="📈")
    async def market_button(self, i: discord.Interaction, b: ui.Button):
        view = MarketView(i); await i.response.send_message(embed=await view.generate_embed(), view=view, ephemeral=True)
    @ui.button(label="My Listings", style=discord.ButtonStyle.secondary, row=0, emoji="📦")
    async def my_listings_button(self, i: discord.Interaction, b: ui.Button):
        listings = database.get_listings_by_seller(self.user_id)
        if not listings: return await i.response.send_message("You have no items listed.", ephemeral=True)
        embed = discord.Embed(title="Your Active Listings", color=discord.Color.orange())
        desc = [f"ID: `{l['listing_id']}` - {l['emoji'] or ''} **{l['quantity']}x {l['item_name']}** for `{l['price']}` Gold" for l in listings]
        embed.description = "\n".join(desc); await i.response.send_message(embed=embed, view=MyListingsView(i), ephemeral=True)
    @ui.button(label="Post Item", style=discord.ButtonStyle.primary, row=1, emoji="📮")
    async def post_item_button(self, i: discord.Interaction, b: ui.Button):
        await i.response.edit_message(embed=discord.Embed(title="Post an Item", description="Select an item from your inventory to sell.", color=discord.Color.dark_magenta()), view=PostItemView(i))

class CommunityView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180); self.interaction = interaction; self.user_id = interaction.user.id; self.add_item(BackButton(row=1))
    @ui.button(label="View Leaderboard", style=discord.ButtonStyle.secondary, row=0, emoji="🏆")
    async def show_leaderboard(self, i: discord.Interaction, b: ui.Button):
        top_players = database.get_leaderboard(10); embed = discord.Embed(title="🏆 Mana Core Leaderboard 🏆", color=discord.Color.gold())
        description = []; ranks = ["🥇", "🥈", "🥉"]
        for idx, p_data in enumerate(top_players):
            rank_emoji = ranks[idx] if idx < 3 else f"**#{idx+1}**"
            try: user = await i.client.fetch_user(p_data['user_id'])
            except: user_name = "Unknown Mage"
            else: user_name = user.display_name
            stage_name, _ = database.get_core_stage_info(p_data['core_level'])
            description.append(f"{rank_emoji} **{user_name}** - {stage_name} (Lvl {p_data['core_level']})")
        embed.description = "\n".join(description); await i.response.send_message(embed=embed, ephemeral=True)
    @ui.button(label="Give Item/Gold", style=discord.ButtonStyle.secondary, row=0, emoji="🎁")
    async def give_button(self, i: discord.Interaction, b: ui.Button): await i.response.send_modal(GiveModal())

class MainView(ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
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
        player = database.get_player(self.user_id)
        if player['beast_cores'] == 0: return await i.response.send_message("You have no cores to sell.", ephemeral=True)
        active_bond = database.get_active_bond(self.user_id)
        gold_bonus = 1.0 + active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'gold_boost' else 1.0
        gold_earned = int(player['beast_cores'] * 10 * gold_bonus)
        database.update_player(self.user_id, beast_cores=0, gold=player['gold'] + gold_earned)
        database.update_task_progress(self.user_id, 'sell_cores', player['beast_cores'])
        database.update_task_progress(self.user_id, 'earn_gold', gold_earned)
        await i.response.send_message(f"⚖️ You sold **{player['beast_cores']}** 💎 for **{gold_earned}** 💰 gold!", ephemeral=True); await self.refresh_ui(i)
    @ui.select(placeholder="Open a Menu...", row=1, options=[
        discord.SelectOption(label="Character", value="character", emoji="👤", description="Inventory, Tasks, Bonds"),
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

# --- Bot Setup and Commands ---
load_dotenv(); TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default(); intents.message_content = True; intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    database.setup_database(); await bot.load_extension('admin_cog'); print(f'Logged in as {bot.user}')

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

@bot.command(name="profile")
async def profile(ctx: commands.Context):
    player = database.get_player(ctx.author.id)
    await ctx.send(embed=create_profile_embed(player, ctx.author), view=MainView(player))

@bot.command(name="daily")
async def daily(ctx: commands.Context):
    await daily_logic(ctx)

bot.run(TOKEN)