from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from database.user import User


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx, tz: str | None = None):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)

        if tz is None:
            current_tz = User.get_timezone(self.bot.db, guild_id, user_id)
            if current_tz:
                await ctx.send(f"🕐 Your current timezone is: `{current_tz}`")
            else:
                await ctx.send(
                    "🕐 You haven't set a timezone yet. Use `&timezone <timezone>` to set one.\nExample: `&timezone Europe/London`"
                )
            return

        # Validate timezone
        try:
            ZoneInfo(tz)
        except Exception:
            await ctx.send(
                "❌ Invalid timezone. Please use a valid IANA timezone name like `America/New_York` or `Europe/London`."
            )
            return

        User.set_timezone(self.bot.db, guild_id, user_id, tz)
        await ctx.send(
            f"✅ Your timezone has been set to `{tz}`. Rolls and daily limits will now reset based on this timezone."
        )

    @commands.command()
    async def help(self, ctx, section: str | None = None):
        if section is None:
            embed = discord.Embed(
                title="📘 MobDex - How to Play",
                description=(
                    "Collect Minecraft mobs, earn emeralds, trade duplicates,\n"
                    "and upgrade your village to unlock powerful features."
                ),
                color=0x2ECC71,
            )

            embed.add_field(
                name="🟢 Getting Started",
                value=(
                    f"`{self.bot.command_prefix}roll` - Roll for a mob (hourly)\n"
                    f"`{self.bot.command_prefix}daily` - Free emeralds + a common mob\n"
                    f"`{self.bot.command_prefix}collection` - View your mobs\n"
                    f"`{self.bot.command_prefix}missing` - See what mobs you haven't collected\n"
                    f"`{self.bot.command_prefix}leaderboard` - Show emerald, completion, and value leaderboards\n"
                    f"`{self.bot.command_prefix}achievements` - View achievements you've unlocked"
                    f"`{self.bot.command_prefix}stats` - View your lifetime statistics"
                    f"`{self.bot.command_prefix}balance` - Check your emeralds\n"
                    f"`{self.bot.command_prefix}timezone` - Set your timezone for daily resets"
                ),
                inline=False,
            )
            embed.add_field(
                name="🧑‍🌾 Trading & Progression",
                value=(
                    f"`{self.bot.command_prefix}trade farmer` - Trade duplicates for emeralds\n"
                    f"`{self.bot.command_prefix}trade cleric` - Convert duplicates into tokens\n"
                    f"`{self.bot.command_prefix}farmer` / `{self.bot.command_prefix}cleric` - Alternative trade commands\n"
                    f"`{self.bot.command_prefix}shop` - Upgrade your Trading Hall\n"
                ),
                inline=False,
            )
            embed.add_field(
                name="📖 Learn More",
                value=(
                    f"`{self.bot.command_prefix}help rolls`\n`{self.bot.command_prefix}help trading`\n`{self.bot.command_prefix}help shop`\n`{self.bot.command_prefix}help tokens`"
                ),
                inline=False,
            )

            await ctx.send(embed=embed)
            return

        if section.lower() == "rolls":
            embed = discord.Embed(title="🎲 Rolling & Claiming Mobs", color=0x3498DB)

            embed.add_field(
                name="Rolling",
                value=(
                    f"`{self.bot.command_prefix}roll`\n"
                    "• Once per hour\n"
                    "• Displays a mob with a Claim button\n"
                    "• Claim expires after 1 hour"
                ),
                inline=False,
            )

            embed.add_field(
                name="Claiming Rules",
                value=(
                    "• You may claim **once per day**\n"
                    "• Claiming adds the mob to your collection\n"
                    "• Awards emeralds based on rarity"
                ),
                inline=False,
            )
            embed.add_field(
                name="Mob Rarities",
                value=("Common - 55%\nUncommon - 25%\nRare - 13%\nEpic - 6%\nLegendary - 1%"),
                inline=False,
            )

            await ctx.send(embed=embed)

        if section.lower() == "trading":
            embed = discord.Embed(
                title="🧑‍🌾 Trading Duplicate Mobs",
                description="Trading uses **duplicate mobs only**.\nYou will always keep **at least one copy** of a mob",
                color=0xF1C40F,
            )

            embed.add_field(
                name="Farmer - Emerald Trades",
                value=(
                    "• Trade duplicates for emeralds\n"
                    "• Value scales by rarity:\n"
                    "  Common: 5💎 | Uncommon: 20💎 | Rare: 50💎\n"
                    "  Epic: 100💎 | Legendary: 200💎\n"
                    f"`{self.bot.command_prefix}trade farmer <mob_id> <amount>`\n"
                    f"`{self.bot.command_prefix}farmer <mob_id> <amount>`"
                ),
                inline=False,
            )
            embed.add_field(
                name="Cleric - Token Trades",
                value=(
                    "• Convert duplicates into roll tokens\n"
                    "• Trades must be in multiples of 2 (2 mobs → 1 token)\n"
                    "• Only Common-Rare mobs can be traded for Uncommon-Epic tokens:\n"
                    "  Common → Uncommon | Uncommon → Rare | Rare → Epic\n"
                    f"`{self.bot.command_prefix}trade cleric <mob_id> <amount>`\n"
                    f"`{self.bot.command_prefix}cleric <mob_id> <amount>`"
                ),
                inline=False,
            )

            await ctx.send(embed=embed)

        if section.lower() == "shop":
            embed = discord.Embed(
                title="🏛️ Trading Hall Progression",
                description="Upgrade your village to unlock new mechanics.",
                color=0x9B59B6,
            )

            tier = 1
            for _, villager in self.bot.villagers.items():
                embed.add_field(
                    name=f"Tier {tier} - {villager['name']} ({villager['price']} emeralds)",
                    value=villager["description"],
                    inline=False,
                )
                tier += 1

            await ctx.send(embed=embed)

        if section.lower() == "tokens":
            embed = discord.Embed(title="🎟️ Roll Tokens", color=0xE67E22)

            embed.add_field(
                name="Token Types", value=("• Uncommon Roll Token\n• Rare Roll Token\n• Epic Roll Token"), inline=False
            )
            embed.add_field(
                name="Using Tokens",
                value=(
                    f"`{self.bot.command_prefix}roll token <rarity>`\n"
                    "• Valid rarities: uncommon, rare, epic\n"
                    "• Consumes the token\n"
                    "• Rolls only within that rarity band"
                ),
                inline=False,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
