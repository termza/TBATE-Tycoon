# admin_cog.py

import discord
from discord.ext import commands
from discord import ui
import math
import database

# --- Admin Configuration & Check ---
ADMIN_USER_ID = 122694211064561667
def is_admin():
    async def predicate(ctx: commands.Context): return ctx.author.id == ADMIN_USER_ID
    return commands.check(predicate)

# --- Helper to create the status embed ---
def create_admin_embed(member: discord.Member):
    player = database.get_player(member.id)
    active_bond = database.get_active_bond(member.id)
    energy_bonus = active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'max_energy_bonus' else 0
    max_energy = database.calculate_max_energy(player['core_level']) + energy_bonus
    embed = discord.Embed(title=f"Admin Panel for {member.display_name}", color=discord.Color.orange())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Core Level", value=f"`{player['core_level']}`", inline=True)
    embed.add_field(name="Energy", value=f"`{player['energy']} / {int(max_energy)}`", inline=True)
    embed.add_field(name="XP", value=f"`{player['xp']}`", inline=True)
    embed.add_field(name="Gold", value=f"`{player['gold']}` 💰", inline=False)
    embed.add_field(name="Beast Cores", value=f"`{player['beast_cores']}` 💎", inline=True)
    return embed

# --- Modals for Input ---
class GiveResourceModal(ui.Modal, title="Give Resource"):
    resource = ui.TextInput(label="Resource Type (gold, cores, energy, xp)", style=discord.TextStyle.short, required=True)
    amount = ui.TextInput(label="Amount", style=discord.TextStyle.short, required=True)
    def __init__(self, member: discord.Member):
        super().__init__(); self.member = member
    async def on_submit(self, interaction: discord.Interaction):
        res = self.resource.value.lower()
        try: amt = int(self.amount.value)
        except ValueError: return await interaction.response.send_message("❌ Amount must be a number.", ephemeral=True)
        player = database.get_player(self.member.id)
        if res == 'gold': database.update_player(self.member.id, gold=player['gold'] + amt)
        elif res == 'cores': database.update_player(self.member.id, beast_cores=player['beast_cores'] + amt)
        elif res == 'xp': database.update_player(self.member.id, xp=player['xp'] + amt)
        elif res == 'energy':
            active_bond = database.get_active_bond(self.member.id)
            energy_bonus = active_bond['bonus_value'] if active_bond and active_bond['bonus_type'] == 'max_energy_bonus' else 0
            max_e = database.calculate_max_energy(player['core_level']) + energy_bonus
            database.update_player(self.member.id, energy=min(int(max_e), player['energy'] + amt))
        else: return await interaction.response.send_message("❌ Invalid resource type.", ephemeral=True)
        await interaction.response.send_message(f"✅ Gave **{amt} {res}** to {self.member.display_name}.", ephemeral=True)
        await interaction.message.edit(embed=create_admin_embed(self.member))

class SetLevelModal(ui.Modal, title="Set Core Level"):
    level = ui.TextInput(label="New Core Level", style=discord.TextStyle.short, required=True)
    def __init__(self, member: discord.Member):
        super().__init__(); self.member = member
    async def on_submit(self, interaction: discord.Interaction):
        try:
            lvl = int(self.level.value)
            if lvl <= 0: raise ValueError()
        except ValueError: return await interaction.response.send_message("❌ Level must be a positive number.", ephemeral=True)
        database.update_player(self.member.id, core_level=lvl, xp=0)
        await interaction.response.send_message(f"✅ Set {self.member.display_name}'s level to **{lvl}**.", ephemeral=True)
        await interaction.message.edit(embed=create_admin_embed(self.member))

class SetQuantityModal(ui.Modal, title="Set Quantity"):
    quantity = ui.TextInput(label="Quantity", required=True, default="1")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

class AdminItemSelectView(ui.View):
    def __init__(self, member: discord.Member, original_interaction: discord.Interaction, page: int = 1):
        super().__init__(timeout=180)
        self.member = member; self.original_interaction = original_interaction; self.current_page = page; self.per_page = 25
        all_items = database.get_all_items()
        self.total_pages = math.ceil(len(all_items) / self.per_page) or 1
        start_index = (self.current_page - 1) * self.per_page; end_index = start_index + self.per_page
        self.page_items = all_items[start_index:end_index]; self.selected_item = None; self.update_components()
    def update_components(self):
        self.clear_items()
        # BUG FIX: Replaced item.get('emoji') with safe access
        options = [discord.SelectOption(label=item['name'], value=str(item['item_id']), emoji=(item['emoji'] if 'emoji' in item.keys() else None)) for item in self.page_items]
        dropdown = ui.Select(placeholder=f"Select an item (Page {self.current_page}/{self.total_pages})...", options=options)
        dropdown.callback = self.on_item_select; self.add_item(dropdown)
        give_button = ui.Button(label="Give Selected Item", style=discord.ButtonStyle.green, disabled=(self.selected_item is None))
        give_button.callback = self.give_item; self.add_item(give_button)
        prev_button = ui.Button(label="⬅️", style=discord.ButtonStyle.grey, disabled=(self.current_page <= 1), row=2)
        prev_button.callback = self.prev_page; self.add_item(prev_button)
        next_button = ui.Button(label="➡️", style=discord.ButtonStyle.grey, disabled=(self.current_page >= self.total_pages), row=2)
        next_button.callback = self.next_page; self.add_item(next_button)
        back_button = ui.Button(label="Back to Main Panel", style=discord.ButtonStyle.danger, row=2)
        back_button.callback = self.go_back; self.add_item(back_button)
    async def on_item_select(self, interaction: discord.Interaction):
        item_id = int(interaction.data['values'][0])
        self.selected_item = database.get_item_by_id(item_id)
        self.update_components(); await interaction.response.edit_message(view=self)
    async def give_item(self, interaction: discord.Interaction):
        if not self.selected_item: return
        modal = SetQuantityModal(); await interaction.response.send_modal(modal); await modal.wait()
        try:
            qty = int(modal.quantity.value)
            if qty <= 0: raise ValueError
        except (ValueError, TypeError): return await interaction.followup.send("❌ Invalid quantity.", ephemeral=True)
        database.add_item_to_inventory(self.member.id, self.selected_item['item_id'], qty)
        await interaction.followup.send(f"✅ Gave {qty}x **{self.selected_item['name']}** to {self.member.display_name}.", ephemeral=True)
    async def prev_page(self, interaction: discord.Interaction): self.current_page -= 1; await self.refresh(interaction)
    async def next_page(self, interaction: discord.Interaction): self.current_page += 1; await self.refresh(interaction)
    async def refresh(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=AdminItemSelectView(self.member, self.original_interaction, self.current_page))
    async def go_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=None, embed=create_admin_embed(self.member), view=AdminPanelView(self.member))

class ResetConfirmationView(ui.View):
    def __init__(self, member: discord.Member, original_message: discord.Message):
        super().__init__(timeout=60); self.member = member; self.original_message = original_message
    @ui.button(label="Yes, Reset Profile", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: ui.Button):
        database.delete_player(self.member.id)
        await interaction.response.send_message(f"✅ Data for {self.member.display_name} has been reset.", ephemeral=True)
        await self.original_message.edit(embed=create_admin_embed(self.member), view=None)
        for child in self.children: child.disabled = True
        await interaction.message.edit(content="Action completed.", view=self); self.stop()
    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Reset cancelled.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(content="Action cancelled.", view=self); self.stop()

class AdminPanelView(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=300); self.member = member
    @ui.select(placeholder="Choose an admin action...", options=[
            discord.SelectOption(label="Give Resource", value="give_resource"), discord.SelectOption(label="Set Core Level", value="set_level"),
            discord.SelectOption(label="Add Item", value="add_item"), discord.SelectOption(label="Reset Profile", value="reset")])
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        action = select.values[0]
        if action == "give_resource": await interaction.response.send_modal(GiveResourceModal(self.member))
        elif action == "set_level": await interaction.response.send_modal(SetLevelModal(self.member))
        elif action == "add_item":
            await interaction.response.edit_message(content="Select an item to give:", embed=None, view=AdminItemSelectView(self.member, interaction))
        elif action == "reset":
            view = ResetConfirmationView(self.member, interaction.message)
            await interaction.response.send_message("❓ Are you sure you want to completely reset this user?", view=view, ephemeral=True)

class AdminPanelCog(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @commands.command(name="adminpanel")
    @is_admin()
    async def admin_panel(self, ctx: commands.Context, member: discord.Member):
        embed = create_admin_embed(member); view = AdminPanelView(member)
        await ctx.send(embed=embed, view=view)
    @admin_panel.error
    async def admin_panel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument): await ctx.send("❌ Usage: `$adminpanel @user`")
        elif isinstance(error, commands.CheckFailure): await ctx.send("🚫 You do not have permission to use this command.")
        else:
            await ctx.send("An unexpected error occurred.")
            print(f"Error in admin_panel command: {error}")

async def setup(bot):
    await bot.add_cog(AdminPanelCog(bot))