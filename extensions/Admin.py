import discord
from discord import app_commands
from discord.ext import commands
from functions.database import (
    set_balance,
    add_balance,
    remove_win_rate,
    set_wins,
    set_losses,
    adjust_win_rate,
    get_user_stats,
    transfer_points
)
from datetime import datetime


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Check if the user has administrator permissions"""
        return interaction.user.guild_permissions.administrator

    def create_embed(self, title: str, description: str, color: discord.Color = discord.Color.teal()) -> discord.Embed:
        """Helper function to create consistent embeds"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        current_time = datetime.now().strftime("%I:%M %p")
        embed.set_footer(text=f"Today at {current_time}")
        return embed

    @app_commands.command(name="setbalance", description="Set a user's balance to a specific amount")
    @app_commands.describe(user="The user to set balance for", amount="The amount to set")
    async def set_balance_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        set_balance(user.id, amount)
        embed = self.create_embed(
            "Balance Updated",
            f"Set {user.mention}'s balance to {amount:,} points",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addbalance", description="Add points to a user's balance")
    @app_commands.describe(user="The user to add balance to", amount="The amount to add")
    async def add_balance_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        add_balance(user.id, amount)
        embed = self.create_embed(
            "Balance Added",
            f"Added {amount:,} points to {user.mention}'s balance",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removewinrate", description="Reset a user's win rate to 0")
    @app_commands.describe(user="The user to reset win rate for")
    async def remove_win_rate_command(self, interaction: discord.Interaction, user: discord.Member):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        remove_win_rate(user.id)
        embed = self.create_embed(
            "Win Rate Reset",
            f"Reset {user.mention}'s win rate to 0%",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setwins", description="Set a user's number of wins")
    @app_commands.describe(user="The user to set wins for", wins="The number of wins to set")
    async def set_wins_command(self, interaction: discord.Interaction, user: discord.Member, wins: int):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        set_wins(user.id, wins)
        embed = self.create_embed(
            "Wins Updated",
            f"Set {user.mention}'s wins to {wins:,}",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setlosses", description="Set a user's number of losses")
    @app_commands.describe(user="The user to set losses for", losses="The number of losses to set")
    async def set_losses_command(self, interaction: discord.Interaction, user: discord.Member, losses: int):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        set_losses(user.id, losses)
        embed = self.create_embed(
            "Losses Updated",
            f"Set {user.mention}'s losses to {losses:,}",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="adjustwinrate", description="Set a user's win rate to a specific percentage")
    @app_commands.describe(user="The user to adjust win rate for", percentage="The win rate percentage (0-100)")
    async def adjust_win_rate_command(self, interaction: discord.Interaction, user: discord.Member, percentage: float):
        if not self.is_admin(interaction):
            embed = self.create_embed(
                "Permission Denied",
                "You need administrator permissions to use this command",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if percentage < 0 or percentage > 100:
            embed = self.create_embed(
                "Invalid Win Rate",
                "Win rate must be between 0 and 100",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        adjust_win_rate(user.id, percentage)
        embed = self.create_embed(
            "Win Rate Adjusted",
            f"Set {user.mention}'s win rate to {percentage:.1f}%",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="Show your game statistics")
    async def stats_command(self, interaction: discord.Interaction):
        stats = get_user_stats(interaction.user.id)
        
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Statistics",
            color=discord.Color.teal()
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(
            name="Points",
            value=f"{stats['points']:,}",
            inline=True
        )
        
        embed.add_field(
            name="Win Rate",
            value=f"{stats['win_rate']:.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="Games Played",
            value=f"{stats['total_games']:,}",
            inline=True
        )
        
        embed.add_field(
            name="Wins",
            value=f"{stats['wins']:,}",
            inline=True
        )
        
        embed.add_field(
            name="Losses",
            value=f"{stats['losses']:,}",
            inline=True
        )
        
        embed.add_field(
            name="Draws",
            value=f"{stats['draws']:,}",
            inline=True
        )
        
        current_time = datetime.now().strftime("%I:%M %p")
        embed.set_footer(text=f"Today at {current_time}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="transfer", description="Transfer your points to another user")
    @app_commands.describe(
        user="The user to transfer points to",
        amount="The amount of points to transfer"
    )
    async def transfer_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if user.id == interaction.user.id:
            embed = self.create_embed(
                "Invalid Transfer",
                "You cannot transfer points to yourself",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        success = transfer_points(interaction.user.id, user.id, amount)
        
        if success:
            embed = self.create_embed(
                "Transfer Successful",
                f"Successfully transferred {amount:,} points to {user.mention}",
                discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to make this transfer",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot=bot))