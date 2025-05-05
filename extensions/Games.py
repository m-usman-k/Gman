import random
import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from functions.database import (
    get_user_stats,
    add_balance,
    set_balance
)
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_roulette_games: Dict[int, Dict] = {}  # channel_id: game_data
        self.active_blackjack_games: Dict[int, Dict] = {}  # channel_id: game_data
        self.active_jackpots: Dict[int, Dict] = {}  # channel_id: jackpot_data

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

    @app_commands.command(name="coinflip", description="Play a game of coinflip")
    @app_commands.describe(
        side="Choose heads or tails",
        amount="The amount of points to bet"
    )
    @app_commands.choices(side=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip_command(self, interaction: discord.Interaction, side: app_commands.Choice[str], amount: int):
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < amount:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to make this bet",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create initial embed showing the coin flipping
        embed = self.create_embed(
            "Coinflip",
            f"🪙 The coin is flipping...\n\n"
            f"Your bet: **{amount:,}** points on **{side.value.title()}**\n"
            f"Current balance: **{stats['points']:,}** points",
            discord.Color.teal()
        )
        message = await interaction.response.send_message(embed=embed)

        # Wait for 2 seconds to simulate coin flipping
        await asyncio.sleep(2)

        # Generate result
        result = random.choice(["heads", "tails"])
        won = result == side.value

        # Update points
        if won:
            # Add points to user (2x the bet)
            add_balance(interaction.user.id, amount)
            new_balance = stats['points'] + amount
        else:
            # Remove points from user
            set_balance(interaction.user.id, stats['points'] - amount)
            new_balance = stats['points'] - amount

        # Create result embed
        if won:
            embed = self.create_embed(
                "Coinflip Result",
                f"🎉 **{result.title()}**! You won **{amount:,}** points!\n\n"
                f"Your bet: **{amount:,}** points on **{side.value.title()}**\n"
                f"New balance: **{new_balance:,}** points",
                discord.Color.green()
            )
        else:
            embed = self.create_embed(
                "Coinflip Result",
                f"😢 **{result.title()}**! You lost **{amount:,}** points.\n\n"
                f"Your bet: **{amount:,}** points on **{side.value.title()}**\n"
                f"New balance: **{new_balance:,}** points",
                discord.Color.red()
            )

        # Edit the original message with the result
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="roulette", description="Start a game of roulette")
    @app_commands.describe(amount="The amount of points to bet")
    async def roulette_command(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < amount:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to make this bet",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if there's already a game in this channel
        channel_id = interaction.channel_id
        if channel_id in self.active_roulette_games:
            embed = self.create_embed(
                "Game in Progress",
                "There is already a roulette game in progress in this channel.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calculate end time
        end_time = datetime.now() + timedelta(seconds=30)
        timestamp = int(end_time.timestamp())

        # Initialize new game
        self.active_roulette_games[channel_id] = {
            "host_id": interaction.user.id,
            "host_amount": amount,
            "bets": [],
            "message": None,
            "end_time": end_time
        }

        # Create initial game embed
        embed = self.create_embed(
            "🎲 Roulette Game",
            f"**{interaction.user.mention}** started a roulette game!\n"
            f"Host's bet: **{amount:,}** points\n\n"
            "Click the Join button to participate!\n"
            f"Game ends <t:{timestamp}:R>",
            discord.Color.teal()
        )
        view = RouletteView(self, amount)
        message = await interaction.response.send_message(embed=embed, view=view)
        self.active_roulette_games[channel_id]["message"] = message

        # Start game timer
        await asyncio.sleep(30)
        
        # Check if game still exists (might have been cancelled)
        if channel_id not in self.active_roulette_games:
            return

        game = self.active_roulette_games[channel_id]
        bets = game["bets"]
        
        if not bets:
            embed = self.create_embed(
                "Roulette Game Cancelled",
                "No players joined the game.",
                discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed, view=None)
            del self.active_roulette_games[channel_id]
            return

        # Show spinning animation
        embed = self.create_embed(
            "🎲 Roulette Spinning",
            "The wheel is spinning...",
            discord.Color.teal()
        )
        await interaction.edit_original_response(embed=embed, view=None)
        await asyncio.sleep(3)

        # Generate result
        result = random.choice(["red", "black"])
        result_number = random.randint(0, 36)
        
        # Process results
        winners = []
        losers = []
        for bet in bets:
            if bet["color"] == result:
                add_balance(bet["user_id"], bet["amount"])
                winners.append(f"<@{bet['user_id']}> won {bet['amount']:,} points")
            else:
                set_balance(bet["user_id"], get_user_stats(bet["user_id"])["points"] - bet["amount"])
                losers.append(f"<@{bet['user_id']}> lost {bet['amount']:,} points")

        # Create result embed
        result_embed = self.create_embed(
            "🎲 Roulette Result",
            f"**{result.title()} {result_number}**!\n\n"
            f"**Winners:**\n" + "\n".join(winners) + "\n\n"
            f"**Losers:**\n" + "\n".join(losers),
            discord.Color.green() if winners else discord.Color.red()
        )
        await interaction.edit_original_response(embed=result_embed)
        del self.active_roulette_games[channel_id]

    @app_commands.command(name="blackjack", description="Play a game of blackjack")
    @app_commands.describe(amount="The amount of points to bet")
    async def blackjack_command(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < amount:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to make this bet",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user is already in a game
        channel_id = interaction.channel_id
        if channel_id in self.active_blackjack_games:
            embed = self.create_embed(
                "Game in Progress",
                "There is already a blackjack game in progress in this channel.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Initialize game
        deck = self._create_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        self.active_blackjack_games[channel_id] = {
            "player_id": interaction.user.id,
            "amount": amount,
            "deck": deck,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "message": None
        }

        # Create initial game embed
        player_value = self._calculate_hand_value(player_hand)
        dealer_value = self._calculate_hand_value([dealer_hand[0]])
        
        embed = self.create_embed(
            "🎲 Blackjack",
            f"**Your Hand** ({player_value}):\n{self._format_hand(player_hand)}\n\n"
            f"**Dealer's Hand** ({dealer_value}):\n{self._format_card(dealer_hand[0])} 🃏\n\n"
            f"**Your Points:** {stats['points']:,}\n"
            f"**Bet Amount:** {amount:,}\n\n"
            "Choose your action:",
            discord.Color.teal()
        )
        message = await interaction.response.send_message(embed=embed, view=BlackjackView(self))

    @app_commands.command(name="jackpot", description="Start a jackpot game")
    @app_commands.describe(
        duration="Duration of the jackpot in days (can use decimals for hours/minutes)",
        amount="The amount of points to contribute"
    )
    async def jackpot_command(self, interaction: discord.Interaction, duration: float, amount: int):
        if duration <= 0:
            embed = self.create_embed(
                "Invalid Duration",
                "Duration must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < amount:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to contribute to the jackpot",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if there's already a jackpot in this channel
        channel_id = interaction.channel_id
        if channel_id in self.active_jackpots:
            embed = self.create_embed(
                "Game in Progress",
                "There is already a jackpot in progress in this channel.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create new jackpot
        end_time = datetime.now() + timedelta(days=duration)
        self.active_jackpots[channel_id] = {
            "host_id": interaction.user.id,
            "total_amount": amount,
            "contributors": {interaction.user.id: amount},
            "end_time": end_time,
            "message": None,
            "amount": amount
        }

        # Deduct points from host
        set_balance(interaction.user.id, stats["points"] - amount)

        # Format duration display
        if duration < 1:
            if duration < 1/24:  # Less than an hour
                minutes = int(duration * 24 * 60)
                duration_display = f"{minutes} minutes"
            else:  # Less than a day
                hours = duration * 24
                duration_display = f"{hours:.1f} hours"
        else:
            duration_display = f"{duration} days"

        # Calculate initial contribution percentage
        percentage = (amount / amount) * 100  # Will be 100% initially

        # Create initial embed
        embed = self.create_embed(
            "🎰 Jackpot Started",
            f"**{interaction.user.mention}** started a jackpot!\n\n"
            f"**Initial Contribution:** {amount:,} points ({percentage:.1f}% chance)\n"
            f"**Duration:** {duration_display}\n"
            f"**Ends:** <t:{int(end_time.timestamp())}:R>\n\n"
            "Click the Join button to participate!\n"
            "The more you contribute, the higher your chance to win!",
            discord.Color.teal()
        )
        view = JackpotView(self, amount)
        message = await interaction.response.send_message(embed=embed, view=view)
        self.active_jackpots[channel_id]["message"] = message

        # Start jackpot timer
        await asyncio.sleep(duration * 24 * 60 * 60)  # Convert days to seconds

        # Check if jackpot still exists
        if channel_id not in self.active_jackpots:
            return

        jackpot = self.active_jackpots[channel_id]
        
        # Select winner based on contribution weights
        total_contributions = sum(jackpot["contributors"].values())
        random_value = random.uniform(0, total_contributions)
        current_sum = 0
        winner_id = None

        for user_id, contribution in jackpot["contributors"].items():
            current_sum += contribution
            if random_value <= current_sum:
                winner_id = user_id
                break

        # Award winner
        add_balance(winner_id, jackpot["total_amount"])

        # Create result embed with contribution details
        result_embed = self.create_embed(
            "🎰 Jackpot Winner!",
            f"**<@{winner_id}>** won the jackpot of **{jackpot['total_amount']:,}** points!\n\n"
            f"**Total Participants:** {len(jackpot['contributors'])}\n"
            f"**Total Contributions:** {jackpot['total_amount']:,} points\n"
            f"**Winner's Contribution:** {jackpot['contributors'][winner_id]:,} points ({(jackpot['contributors'][winner_id] / jackpot['total_amount'] * 100):.1f}% chance)\n\n"
            "Congratulations to the winner! 🎉",
            discord.Color.green()
        )
        await interaction.edit_original_response(embed=result_embed, view=None)
        del self.active_jackpots[channel_id]

    @app_commands.command(name="dice", description="Roll a dice and win if you roll above the target number")
    @app_commands.describe(
        target="The number you need to roll above",
        amount="The amount of points to bet"
    )
    @app_commands.choices(target=[
        app_commands.Choice(name="Above 3 (50.0% chance, 2.0x)", value=3),
        app_commands.Choice(name="Above 4 (33.3% chance, 3.0x)", value=4),
        app_commands.Choice(name="Above 5 (16.7% chance, 6.0x)", value=5)
    ])
    async def dice_command(self, interaction: discord.Interaction, target: app_commands.Choice[int], amount: int):
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount",
                "Amount must be greater than 0",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < amount:
            embed = self.create_embed(
                "Insufficient Points",
                "You don't have enough points to make this bet",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calculate win chance and multiplier
        win_chance = (6 - target.value) / 6 * 100
        multiplier = 6 / (6 - target.value)  # Higher target = higher multiplier

        # Create initial embed
        embed = self.create_embed(
            "🎲 Dice Roll",
            f"**{interaction.user.mention}** is rolling a dice!\n\n"
            f"**Target:** Above {target.value}\n"
            f"**Bet Amount:** {amount:,} points\n"
            f"**Win Chance:** {win_chance:.1f}%\n"
            f"**Multiplier:** {multiplier:.2f}x\n\n"
            "Rolling the dice...",
            discord.Color.teal()
        )
        message = await interaction.response.send_message(embed=embed)

        # Wait for dramatic effect
        await asyncio.sleep(2)

        # Roll the dice
        roll = random.randint(1, 6)
        won = roll > target.value

        # Update points
        if won:
            winnings = int(amount * multiplier)
            add_balance(interaction.user.id, winnings)
            new_balance = stats['points'] + winnings
            result_color = discord.Color.green()
            result_message = f"🎉 You rolled a **{roll}** and won **{winnings:,}** points!"
        else:
            set_balance(interaction.user.id, stats['points'] - amount)
            new_balance = stats['points'] - amount
            result_color = discord.Color.red()
            result_message = f"😢 You rolled a **{roll}** and lost **{amount:,}** points."

        # Create result embed
        result_embed = self.create_embed(
            "🎲 Dice Roll Result",
            f"{result_message}\n\n"
            f"**Target:** Above {target.value}\n"
            f"**Roll:** {roll}\n"
            f"**Bet Amount:** {amount:,} points\n"
            f"**New Balance:** {new_balance:,} points",
            result_color
        )
        await interaction.edit_original_response(embed=result_embed)

    def _create_deck(self) -> List[str]:
        """Create a shuffled deck of cards"""
        suits = ["♠", "♥", "♦", "♣"]
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        deck = [f"{value}{suit}" for suit in suits for value in values]
        random.shuffle(deck)
        return deck

    def _format_hand(self, hand: List[str]) -> str:
        """Format a hand of cards for display"""
        return " ".join(self._format_card(card) for card in hand)

    def _format_card(self, card: str) -> str:
        """Format a single card for display"""
        suit = card[-1]
        value = card[:-1]
        
        # Map suits to emojis
        suit_emoji = {
            "♠": "♠️",
            "♥": "♥️",
            "♦": "♦️",
            "♣": "♣️"
        }
        
        # Map values to emojis
        value_emoji = {
            "A": "🅰️",
            "K": "👑",
            "Q": "👸",
            "J": "🎭"
        }
        
        # Format the card
        if value in value_emoji:
            return f"{value_emoji[value]}{suit_emoji[suit]}"
        else:
            return f"{value}{suit_emoji[suit]}"

    def _calculate_hand_value(self, hand: List[str]) -> int:
        """Calculate the value of a hand"""
        value = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            if rank in ["J", "Q", "K"]:
                value += 10
            elif rank == "A":
                aces += 1
                value += 11
            else:
                value += int(rank)
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value


class RouletteView(discord.ui.View):
    def __init__(self, cog: Games, amount: int):
        super().__init__(timeout=30)
        self.cog = cog
        self.amount = amount

    @discord.ui.button(label="Join Red", style=discord.ButtonStyle.red)
    async def join_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._join_game(interaction, "red")

    @discord.ui.button(label="Join Black", style=discord.ButtonStyle.grey)
    async def join_black(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._join_game(interaction, "black")

    async def _join_game(self, interaction: discord.Interaction, color: str):
        channel_id = interaction.channel_id
        game = self.cog.active_roulette_games.get(channel_id)
        
        if not game:
            await interaction.response.send_message("This game has already ended!", ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < self.amount:
            embed = self.cog.create_embed(
                "Insufficient Points",
                "You don't have enough points to join this game",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Add bet to game
        game["bets"].append({
            "user_id": interaction.user.id,
            "color": color,
            "amount": self.amount
        })

        embed = self.cog.create_embed(
            "Bet Placed",
            f"Your bet of **{self.amount:,}** points on **{color.title()}** has been placed.\n"
            "Waiting for other players...",
            discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BlackjackView(discord.ui.View):
    def __init__(self, cog: Games):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel_id
        game = self.cog.active_blackjack_games.get(channel_id)
        
        if not game or game["player_id"] != interaction.user.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        # Draw a card
        game["player_hand"].append(game["deck"].pop())
        player_value = self.cog._calculate_hand_value(game["player_hand"])
        dealer_value = self.cog._calculate_hand_value([game["dealer_hand"][0]])
        stats = get_user_stats(interaction.user.id)

        if player_value > 21:
            # Player busts
            embed = self.cog.create_embed(
                "🎲 Blackjack - Bust!",
                f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
                f"**Dealer's Hand** ({self.cog._calculate_hand_value(game['dealer_hand'])}):\n{self.cog._format_hand(game['dealer_hand'])}\n\n"
                f"**Your Points:** {stats['points']:,}\n"
                f"**Bet Amount:** {game['amount']:,}\n\n"
                f"You busted and lost {game['amount']:,} points!",
                discord.Color.red()
            )
            set_balance(interaction.user.id, stats["points"] - game["amount"])
            await interaction.response.edit_message(embed=embed, view=None)
            del self.cog.active_blackjack_games[channel_id]
            return

        embed = self.cog.create_embed(
            "🎲 Blackjack",
            f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
            f"**Dealer's Hand** ({dealer_value}):\n{self.cog._format_card(game['dealer_hand'][0])} 🃏\n\n"
            f"**Your Points:** {stats['points']:,}\n"
            f"**Bet Amount:** {game['amount']:,}\n\n"
            "Choose your action:",
            discord.Color.teal()
        )
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel_id
        game = self.cog.active_blackjack_games.get(channel_id)
        
        if not game or game["player_id"] != interaction.user.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        # Dealer's turn
        dealer_value = self.cog._calculate_hand_value(game["dealer_hand"])
        while dealer_value < 17:
            game["dealer_hand"].append(game["deck"].pop())
            dealer_value = self.cog._calculate_hand_value(game["dealer_hand"])

        player_value = self.cog._calculate_hand_value(game["player_hand"])
        stats = get_user_stats(interaction.user.id)

        # Determine winner
        if dealer_value > 21:
            # Dealer busts
            add_balance(interaction.user.id, game["amount"])
            embed = self.cog.create_embed(
                "🎲 Blackjack - Win!",
                f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
                f"**Dealer's Hand** ({dealer_value}):\n{self.cog._format_hand(game['dealer_hand'])}\n\n"
                f"**Your Points:** {stats['points'] + game['amount']:,}\n"
                f"**Bet Amount:** {game['amount']:,}\n\n"
                f"Dealer busted! You won {game['amount']:,} points!",
                discord.Color.green()
            )
        elif player_value > dealer_value:
            # Player wins
            add_balance(interaction.user.id, game["amount"])
            embed = self.cog.create_embed(
                "🎲 Blackjack - Win!",
                f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
                f"**Dealer's Hand** ({dealer_value}):\n{self.cog._format_hand(game['dealer_hand'])}\n\n"
                f"**Your Points:** {stats['points'] + game['amount']:,}\n"
                f"**Bet Amount:** {game['amount']:,}\n\n"
                f"You won {game['amount']:,} points!",
                discord.Color.green()
            )
        elif player_value < dealer_value:
            # Dealer wins
            set_balance(interaction.user.id, stats["points"] - game["amount"])
            embed = self.cog.create_embed(
                "🎲 Blackjack - Loss!",
                f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
                f"**Dealer's Hand** ({dealer_value}):\n{self.cog._format_hand(game['dealer_hand'])}\n\n"
                f"**Your Points:** {stats['points'] - game['amount']:,}\n"
                f"**Bet Amount:** {game['amount']:,}\n\n"
                f"You lost {game['amount']:,} points!",
                discord.Color.red()
            )
        else:
            # Push
            embed = self.cog.create_embed(
                "🎲 Blackjack - Push!",
                f"**Your Hand** ({player_value}):\n{self.cog._format_hand(game['player_hand'])}\n\n"
                f"**Dealer's Hand** ({dealer_value}):\n{self.cog._format_hand(game['dealer_hand'])}\n\n"
                f"**Your Points:** {stats['points']:,}\n"
                f"**Bet Amount:** {game['amount']:,}\n\n"
                "It's a push! Your bet is returned.",
                discord.Color.teal()
            )

        await interaction.response.edit_message(embed=embed, view=None)
        del self.cog.active_blackjack_games[channel_id]


class JackpotView(discord.ui.View):
    def __init__(self, cog: Games, amount: int):
        super().__init__(timeout=None)  # No timeout since we handle it in the command
        self.cog = cog
        self.amount = amount

    @discord.ui.button(label="Join Jackpot", style=discord.ButtonStyle.green, emoji="🎰")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel_id
        jackpot = self.cog.active_jackpots.get(channel_id)
        
        if not jackpot:
            await interaction.response.send_message("This jackpot has already ended!", ephemeral=True)
            return

        # Check if user has enough points
        stats = get_user_stats(interaction.user.id)
        if stats['points'] < self.amount:
            embed = self.cog.create_embed(
                "Insufficient Points",
                "You don't have enough points to contribute to the jackpot",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Add or update contribution
        if interaction.user.id in jackpot["contributors"]:
            # Update existing contribution
            jackpot["contributors"][interaction.user.id] += self.amount
        else:
            # Add new contribution
            jackpot["contributors"][interaction.user.id] = self.amount

        # Update total amount and deduct points
        jackpot["total_amount"] += self.amount
        set_balance(interaction.user.id, stats["points"] - self.amount)

        # Calculate contribution percentage
        contribution = jackpot["contributors"][interaction.user.id]
        percentage = (contribution / jackpot["total_amount"]) * 100

        # Update embed
        embed = self.cog.create_embed(
            "🎰 Jackpot Updated",
            f"**{interaction.user.mention}** contributed **{self.amount:,}** points!\n"
            f"**Total Contribution:** {contribution:,} points ({percentage:.1f}% chance)\n\n"
            f"**Total Jackpot:** {jackpot['total_amount']:,} points\n"
            f"**Participants:** {len(jackpot['contributors'])}\n"
            f"**Ends:** <t:{int(jackpot['end_time'].timestamp())}:R>\n\n"
            "Click the Join button to contribute more!",
            discord.Color.teal()
        )
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot=bot))