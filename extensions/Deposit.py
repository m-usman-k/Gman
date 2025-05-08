import stripe
import discord
import re
from discord import app_commands
from discord.ext import commands
from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, PAYMENT_CHANNEL_ID
from functions.database import add_balance

stripe.api_key = STRIPE_API_KEY

class Deposit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.payment_channel = None

    async def cog_load(self):
        # Get the payment channel when the cog loads
        self.payment_channel = self.bot.get_channel(PAYMENT_CHANNEL_ID)
        if not self.payment_channel:
            print(f"Warning: Payment channel with ID {PAYMENT_CHANNEL_ID} not found!")

    @app_commands.command(name="deposit", description="Deposit money to get points")
    @app_commands.describe(amount="The amount of money to deposit (in USD)")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Amount",
                description="Amount must be greater than 0.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create a Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Deposit {amount} points",
                    },
                    "unit_amount": amount * 100,  # Convert to cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"https://discord.com/channels/{interaction.guild_id}/{PAYMENT_CHANNEL_ID}?user_id={interaction.user.id}&amount={amount}",
            cancel_url=f"https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}",
            metadata={
                "user_id": str(interaction.user.id),
                "amount": str(amount)
            }
        )

        embed = discord.Embed(
            title="Deposit Money",
            description=f"Click [here]({session.url}) to complete your deposit.\n\n"
                       f"After payment, please check the payment channel for confirmation.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only process messages in the payment channel
        if message.channel.id != PAYMENT_CHANNEL_ID:
            return

        # Ignore bot messages
        if message.author.bot:
            return

        # Check if the message contains payment information
        # This pattern looks for messages like "Payment received: $10 from user_id:123456789"
        payment_pattern = r"Payment received: \$(\d+) from user_id:(\d+)"
        match = re.search(payment_pattern, message.content)

        if match:
            amount = int(match.group(1))
            user_id = int(match.group(2))

            # Add points to user's balance
            add_balance(user_id, amount)

            # Send confirmation message
            embed = discord.Embed(
                title="Payment Confirmed",
                description=f"Successfully added {amount:,} points to your balance!",
                color=discord.Color.green()
            )
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(embed=embed)
            except:
                # If we can't DM the user, send the confirmation in the payment channel
                await message.channel.send(f"<@{user_id}> {embed.description}")

    @commands.Cog.listener()
    async def on_webhook(self, payload):
        # Handle Stripe webhook events
        event = None
        try:
            event = stripe.Webhook.construct_event(
                payload, self.bot.http.headers["Stripe-Signature"], STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return  # Invalid payload
        except stripe.error.SignatureVerificationError:
            return  # Invalid signature

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = int(session["client_reference_id"])
            amount = int(session["amount_total"] / 100)  # Convert from cents
            add_balance(user_id, amount)
            print(f"Balance Added {amount}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Deposit(bot=bot))