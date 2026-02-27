"""
Maya Discord Bot - Main entry point
Discord-First AI Agent Runtime with music playback
"""

import asyncio
import os
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class MayaBot(commands.Bot):
    """Maya Discord Bot - AI Agent Orchestrator"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.lavalink_nodes: list = []
    
    async def setup_hook(self):
        """Load cogs and setup Lavalink"""
        await self.load_extension("bot.cogs.music")
        # await self.load_extension("bot.cogs.agent")  # Future: agent cog
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f"Maya logged in as {self.user} (ID: {self.user.id})")
        print("------")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="@Maya mentions"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """Handle messages - check for @Maya mentions"""
        if message.author == self.user:
            return
        
        # Check if bot is mentioned
        if self.user in message.mentions:
            # Future: Hand off to agent runtime
            await message.reply("🎵 I'm Maya! Use `!play <song>` for music or ask me to code!")
            return
        
        await self.process_commands(message)

def main():
    """Run the bot"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable not set")
    
    bot = MayaBot()
    bot.run(token)

if __name__ == "__main__":
    main()
