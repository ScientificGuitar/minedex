import discord
from discord.ext import commands

from database.user import User


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, section: str | None = None):
        """Show help information for the bot."""
        if section is None:
            embed = discord.Embed(
                title="📘 MobDex - How to Play",
                description=(
                    "Collect Minecraft mobs, earn emeralds, trade duplicates,\n"
                    "and defend your village in massive boss raids!"
                ),
                color=0x2ECC71,
            )

            embed.add_field(
                name="🟢 Getting Started",
                value=(
                    f"`{self.bot.command_prefix}roll` - Roll for a mob (hourly)\n"
                    f"`{self.bot.command_prefix}daily` - Free emeralds + a common mob\n"
                    f"`{self.bot.command_prefix}collection` - View your mobs\n"
                    f"`{self.bot.command_prefix}missing` - See missing mobs\n"
                    f"`{self.bot.command_prefix}leaderboard` - Server rankings\n"
                    f"`{self.bot.command_prefix}balance` - Check your emeralds\n"
                    f"**Reset Time:** 00:00 UTC (Global)"
                ),
                inline=False,
            )
            embed.add_field(
                name="⚔️ Raid & Discovery",
                value=(
                    f"`{self.bot.command_prefix}raid` - View active boss status\n"
                    f"`{self.bot.command_prefix}raid donate <id> <qty>` - Defend the village\n"
                    f"`{self.bot.command_prefix}tags <mob_id>` - View a mob's traits and power\n"
                    f"`{self.bot.command_prefix}mobs <tag>` - Filter your collection by trait"
                ),
                inline=False,
            )
            embed.add_field(
                name="🧑‍🌾 Trading & Progression",
                value=(
                    f"`{self.bot.command_prefix}trade farmer/cleric` - Manage duplicates\n"
                    f"`{self.bot.command_prefix}shop` - Open the Village Marketplace\n"
                    f"`{self.bot.command_prefix}stats` - View your lifetime statistics"
                ),
                inline=False,
            )
            embed.add_field(
                name="📖 Learn More",
                value=(
                    f"`{self.bot.command_prefix}help raid` | `{self.bot.command_prefix}help trading` | `{self.bot.command_prefix}help shop`"
                ),
                inline=False,
            )

            await ctx.send(embed=embed)
            return

        section = section.lower()
        if section == "raid":
            embed = discord.Embed(title="⚔️ Boss Raids", color=0xE74C3C)
            embed.add_field(
                name="How it works",
                value=(
                    "When the village gathers enough emeralds, a Boss spawns!\n"
                    "Players work together to complete **3 Phases** by donating mobs.\n"
                    "Every donation uses a mob's **Base Power** to weaken the boss."
                ),
                inline=False,
            )
            embed.add_field(
                name="Phase Rules",
                value=(
                    "**Phase 1:** Requires specific Tags (Undead, Nether, etc.)\n"
                    "**Phase 2:** Only Common/Uncommon mobs allowed.\n"
                    "**Phase 3:** Only Epic/Legendary mobs allowed."
                ),
                inline=False,
            )
            embed.add_field(
                name="Rewards",
                value="Defeat the boss to earn **Raid Crates** containing emeralds, tokens, and rare **Artifacts**!",
                inline=False,
            )
            await ctx.send(embed=embed)

        elif section == "trading":
            embed = discord.Embed(
                title="🧑‍🌾 Trading Duplicate Mobs",
                description="Trading uses **duplicate mobs only**.\nYou will always keep **at least one copy** of a mob",
                color=0xF1C40F,
            )
            embed.add_field(
                name="Farmer - Emeralds",
                value="Trade duplicates for emeralds to spend in the shop.",
                inline=True,
            )
            embed.add_field(
                name="Cleric - Tokens",
                value="Convert duplicates into tokens (2 mobs → 1 token).",
                inline=True,
            )
            await ctx.send(embed=embed)

        elif section == "shop":
            embed = discord.Embed(
                title="🏪 Village Marketplace",
                description=(
                    "Use `&shop` to open the interactive marketplace.\n\n"
                    "• **Upgrades:** Permanent villager licenses (Non-linear!)\n"
                    "• **Items:** Single-use roll tokens and boosters."
                ),
                color=0x9B59B6,
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
