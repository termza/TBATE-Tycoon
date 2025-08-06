# cogs/game_commands.py
# This file contains the user-facing commands like $profile and $daily.

import discord
from discord.ext import commands
import time

import database
from .game_views import create_profile_embed, MainView, grant_xp

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

class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="profile")
    async def profile(self, ctx: commands.Context):
        player = database.get_player(ctx.author.id)
        await ctx.send(embed=create_profile_embed(player, ctx.author), view=MainView(self.bot, player))

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        await daily_logic(ctx)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))