"""
Maya Music Cog - Voice channel music playback
Uses Pomice (Lavalink client) for audio streaming
"""

import asyncio
from typing import Optional

import discord
import pomice
from discord.ext import commands


class Music(commands.Cog):
    """Music playback commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pomice = pomice.NodePool()
        
        # Store queue per guild
        self.queues: dict[int, list[pomice.Track]] = {}
        self.current_tracks: dict[int, pomice.Track] = {}
    
    async def cog_load(self):
        """Connect to Lavalink node"""
        await self.pomice.create_node(
            bot=self.bot,
            host="localhost",
            port=2333,
            password="youshallnotpass",
            identifier="maya-node",
            spotify_client_id=None,
            spotify_client_secret=None,
        )
    
    def get_queue(self, guild_id: int) -> list:
        """Get or create queue for guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]
    
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song from URL or search query"""
        # Check if user is in voice channel
        if not ctx.author.voice:
            return await ctx.reply("You need to be in a voice channel! 🎵")
        
        # Get or create player
        player: pomice.Player = ctx.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=pomice.Player)
        
        # Search for track
        results = await self.pomice.get_tracks(query=query, ctx=ctx)
        
        if not results:
            return await ctx.reply("No results found! 🔍")
        
        track = results[0]
        queue = self.get_queue(ctx.guild.id)
        
        if player.is_playing:
            # Add to queue
            queue.append(track)
            await ctx.reply(f"Added to queue: **{track.title}** 🎵")
        else:
            # Play immediately
            self.current_tracks[ctx.guild.id] = track
            await player.play(track)
            await ctx.reply(f"Now playing: **{track.title}** 🎶")
    
    @commands.command(name="skip", aliases=["s", "next"])
    async def skip(self, ctx: commands.Context):
        """Skip current song"""
        player: pomice.Player = ctx.voice_client
        if not player or not player.is_playing:
            return await ctx.reply("Nothing is playing! 🎵")
        
        await player.stop()
        await ctx.reply("Skipped! ⏭️")
        
        # Play next in queue
        queue = self.get_queue(ctx.guild.id)
        if queue:
            next_track = queue.pop(0)
            self.current_tracks[ctx.guild.id] = next_track
            await player.play(next_track)
            await ctx.send(f"Now playing: **{next_track.title}** 🎶")
    
    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx: commands.Context):
        """Stop playback and disconnect"""
        player: pomice.Player = ctx.voice_client
        if not player:
            return await ctx.reply("Not connected to a voice channel! 🔇")
        
        # Clear queue
        self.queues[ctx.guild.id] = []
        self.current_tracks.pop(ctx.guild.id, None)
        
        await player.destroy()
        await ctx.reply("Disconnected! 👋")
    
    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause playback"""
        player: pomice.Player = ctx.voice_client
        if not player or not player.is_playing:
            return await ctx.reply("Nothing is playing! 🎵")
        
        await player.set_pause(True)
        await ctx.reply("Paused! ⏸️")
    
    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume playback"""
        player: pomice.Player = ctx.voice_client
        if not player or not player.is_paused:
            return await ctx.reply("Not paused! 🎵")
        
        await player.set_pause(False)
        await ctx.reply("Resumed! ▶️")
    
    @commands.command(name="queue", aliases=["q"])
    async def queue_cmd(self, ctx: commands.Context):
        """Show current queue"""
        queue = self.get_queue(ctx.guild.id)
        current = self.current_tracks.get(ctx.guild.id)
        
        if not current and not queue:
            return await ctx.reply("Queue is empty! 🎵")
        
        msg = "**Now Playing:**\n"
        if current:
            msg += f"🎶 {current.title}\n"
        
        if queue:
            msg += "\n**Queue:**\n"
            for i, track in enumerate(queue[:10], 1):
                msg += f"{i}. {track.title}\n"
            if len(queue) > 10:
                msg += f"... and {len(queue) - 10} more\n"
        
        await ctx.reply(msg)
    
    @commands.command(name="volume")
    async def volume(self, ctx: commands.Context, volume: int):
        """Set volume (0-100)"""
        if not 0 <= volume <= 100:
            return await ctx.reply("Volume must be between 0 and 100! 🔊")
        
        player: pomice.Player = ctx.voice_client
        if not player:
            return await ctx.reply("Not connected! 🔇")
        
        await player.set_volume(volume)
        await ctx.reply(f"Volume set to {volume}% 🔊")
    
    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: pomice.Player, track: pomice.Track, reason: str):
        """Called when track ends - play next in queue"""
        queue = self.get_queue(player.guild.id)
        
        if queue:
            next_track = queue.pop(0)
            self.current_tracks[player.guild.id] = next_track
            await player.play(next_track)
            
            # Notify channel
            if player.channel:
                await player.channel.send(f"Now playing: **{next_track.title}** 🎶")
        else:
            self.current_tracks.pop(player.guild.id, None)


async def setup(bot: commands.Bot):
    """Add the cog to the bot"""
    await bot.add_cog(Music(bot))
