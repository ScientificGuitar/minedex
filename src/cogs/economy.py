import time
from datetime import datetime, timezone

import discord
from discord.ext import commands

from constants import RARITY_COLORS, RARITY_EMOJIS
from database.user import User


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def balance(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        emeralds = self.bot.economy_service.get_user_balance(self.bot.db, guild_id, user_id)

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Balance", colour=discord.Colour.green())

        embed.add_field(name="💎 Emeralds", value=str(emeralds), inline=False)
        embed.set_footer(text="Collect mobs to earn more emeralds!")

        await ctx.send(embed=embed)

    @commands.command()
    async def inventory(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        grouped_inventory = self.bot.economy_service.get_user_inventory(self.bot.db, guild_id, user_id)

        if not grouped_inventory:
            await ctx.send("🎒 Your inventory is empty.")
            return

        embed = discord.Embed(title=f"🎒 {ctx.author.display_name}'s Inventory", colour=discord.Colour.dark_gold())

        for item_type, items in grouped_inventory.items():
            lines = []

            for item, amount in items:
                rarity = item.get("rarity", "Common")
                emoji = RARITY_EMOJIS[rarity]

                lines.append(f"{emoji} **{item['name']}** x{amount}")

            embed.add_field(
                name=item_type.title(),
                value="\n".join(lines),
                inline=False,
            )

        embed.set_footer(text=f"Use {self.bot.command_prefix}item <item_id> to view details")
        await ctx.send(embed=embed)

    @commands.command()
    async def item(self, ctx, item_id: str):
        item = self.bot.economy_service.get_item_info(item_id)
        if not item:
            await ctx.send("❌ Unknown item.")
            return

        rarity = item.get("rarity", "Common")
        colour = RARITY_COLORS.get(rarity, discord.Colour.dark_grey())

        embed = discord.Embed(title=item["name"], description=item.get("description", "No description."), colour=colour)

        embed.add_field(name="Type", value=item.get("type", "Unknown").title(), inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def daily(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        now = int(time.time())
        User.ensure_user(self.bot.db, guild_id, user_id)

        result = self.bot.economy_service.claim_daily_reward(self.bot.db, guild_id, user_id, now, ctx.channel.id)

        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=("You checked in today and received your daily reward!\nCome back tomorrow for more."),
            colour=discord.Colour.green(),
        )

        embed.add_field(
            name="💎 Emeralds",
            value=f"+{result['emeralds']}",
            inline=False,
        )

        embed.add_field(
            name="🪨 Common Mob",
            value=f"**{result['mob']['name']}**",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
