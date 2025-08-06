# main.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

import database

class TbateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # Required for fetching members for roles
        super().__init__(command_prefix="$", intents=intents)
        
        self.initial_extensions = [
            'admin_cog',
            'cogs.game_commands'
        ]
        self.cogs_loaded = []
        self.cogs_failed = []

    async def setup_hook(self):
        """This is called once the bot is ready, before it connects."""
        database.setup_database()
        
        # Load all cogs and store the results
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                self.cogs_loaded.append(extension)
            except Exception as e:
                self.cogs_failed.append(f"{extension} ({e})")

    async def on_ready(self):
        # Clear the console and print the new startup screen
        os.system('cls' if os.name == 'nt' else 'clear')

        ascii_art = """
 ████████╗██████╗  █████╗ ████████╗███████╗
 ╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
    ██║   ██████╔╝███████║   ██║   █████╗  
    ██║   ██╔══██╗██╔══██║   ██║   ██╔══╝  
    ██║   ██║  ██║██║  ██║   ██║   ███████╗
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
                                          
      ██████╗  ██████╗ ████████╗
     ██╔═══██╗██╔═══██╗╚══██╔══╝
     ██║   ██║██║   ██║   ██║   
     ██║   ██║██║   ██║   ██║   
     ╚██████╔╝╚██████╔╝   ██║   
      ╚═════╝  ╚═════╝    ╚═╝   
"""
        print(ascii_art)
        print("=================================================")
        print(f"Logged in as: {self.user} (ID: {self.user.id})")
        print(f"Database: Connected and setup complete.")
        print(f"Cogs Loaded: {len(self.cogs_loaded)}/{len(self.initial_extensions)}")
        for cog in self.cogs_loaded:
            print(f"  - {cog}")
        if self.cogs_failed:
            print("--- FAILED TO LOAD ---")
            for cog in self.cogs_failed:
                print(f"  - {cog}")
        print("=================================================")
        print("Bot is online and ready.")

def main():
    # Configure logging to hide unnecessary messages from discord.py
    # We only want to see warnings and errors from the library
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN is None:
        print("FATAL ERROR: DISCORD_TOKEN not found in .env file.")
        return

    bot = TbateBot()
    bot.run(TOKEN)

if __name__ == '__main__':
    main()