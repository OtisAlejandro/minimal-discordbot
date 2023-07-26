import discord
from discord import app_commands
from discord.ext import commands


class DevCommands(commands.Cog, name="dev_commands"):
    def __init__(self, bot):
        self.bot = bot

    async def embedder(self, msg):
        embed = discord.Embed(description=f"{msg}", color=0x9C84EF)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print("Dev Commands cog synced.")

    @app_commands.command(name="test", description="Test command")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Test passed and tree synced.", delete_after=3
        )

    @app_commands.command(name="reload", description="reload cog")
    async def reload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(
                embed=await self.embedder(f"Reloaded `{cog}`"), delete_after=3
            )
        except Exception:
            await interaction.response.send_message(
                embed=await self.embedder(f"Reloaded `{cog}`"), delete_after=3
            )

async def setup(bot):
    await bot.add_cog(DevCommands(bot))
