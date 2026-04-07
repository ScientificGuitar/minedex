import discord
from discord.ext import commands

from constants import TRADING_HALL_ORDER
from database.user import User
from views.upgrade_confirm import UpgradeTradingView


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx, action: str | None = None, target: str | None = None):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        category = action.lower() if action else None
        User.ensure_user(self.bot.db, guild_id, user_id)

        if category is None:
            emeralds = User.get_emeralds(self.bot.db, guild_id, user_id) or 0

            embed = discord.Embed(
                title="🏪 Marketplace", description=f"💎 **Emeralds:** {emeralds}", color=discord.Color.gold()
            )
            embed.add_field(name="🏛️ Trading Hall", value="Upgrade your village to unlock new services", inline=False)
            embed.set_footer(text=f"Use {self.bot.command_prefix}shop <category> to browse")

            await ctx.send(embed=embed)

        if category == "upgrade":
            if target is None:
                embed = build_upgrade_list_embed(self.bot, guild_id, user_id)
                await ctx.send(embed=embed)
                return

            if target == "trading":
                current_level = User.get_trading_hall_level(self.bot.db, guild_id, user_id) or 0
                emeralds = User.get_emeralds(self.bot.db, guild_id, user_id) or 0
                next_level = current_level + 1

                next_villager = get_villager_by_level(self.bot.villagers, next_level)
                if not next_villager:
                    await ctx.send("✅ Your Trading Hall is already fully upgraded.")
                    return

                price = next_villager["price"]

                if emeralds < price:
                    await ctx.send(f"❌ You need **{price} emeralds**, but you only have **{emeralds}**.")
                    return

                current_villager = (
                    get_villager_by_level(self.bot.villagers, current_level) if current_level > 0 else None
                )

                embed = discord.Embed(
                    title="⬆️ Upgrade Trading Hall",
                    description=(
                        f"**Current Tier:** {current_villager['name'] if current_villager else 'None'}\n"
                        f"**Next Tier:** {next_villager['name']}\n\n"
                        f"**Unlocks:**\n• {next_villager['description']}\n\n"
                        f"💎 **Price:** {price} emeralds"
                    ),
                    color=discord.Color.gold(),
                )

                view = UpgradeTradingView(bot=self.bot, guild_id=guild_id, user_id=user_id, villager=next_villager)

                embed.set_footer(text="Confirm to upgrade your Trading Hall")
                await ctx.send(embed=embed, view=view)

            else:
                embed = build_upgrade_list_embed(self.bot, guild_id, user_id, invalid_target=target)
                await ctx.send(embed=embed)
                return

        if category == "trading":
            emeralds = User.get_emeralds(self.bot.db, guild_id, user_id) or 0

            embed = discord.Embed(
                title="🏛️ Trading Hall",
                description=f"Upgrade your village to unlock new services.\n\n💎 **Emeralds:** {emeralds}",
                color=discord.Color.gold(),
            )

            current_trading_level = User.get_trading_hall_level(self.bot.db, guild_id, user_id) or 0
            for villager_id in TRADING_HALL_ORDER:
                next_villager = self.bot.villagers[villager_id]
                state = get_villager_state(current_trading_level, next_villager["level"])

                if state == "owned":
                    embed.add_field(
                        name=f"✅ {next_villager['name']} - Owned",
                        value=(f"• {next_villager['description']}"),
                        inline=False,
                    )
                elif state == "available":
                    embed.add_field(
                        name=f"🔓 {next_villager['name']} - Available",
                        value=(
                            f"• {next_villager['description']}\n• **Price:** 💎 {next_villager['price']} emeralds\n"
                        ),
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name=f"🔒 {next_villager['name']} - Locked",
                        value=(f"• {next_villager['description']}"),
                        inline=False,
                    )

            embed.set_footer(
                text=f"Use `{self.bot.command_prefix}shop upgrade trading` to upgrade your trading hall and unlock the next villager"
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))


def build_upgrade_list_embed(bot, guild_id: int, user_id: int, invalid_target: str | None = None) -> discord.Embed:
    emeralds = User.get_emeralds(bot.db, guild_id, user_id) or 0
    current_trading_level = User.get_trading_hall_level(bot.db, guild_id, user_id) or 0
    next_trading_villager = get_villager_by_level(bot.villagers, current_trading_level + 1)

    if invalid_target is None:
        description = f"💎 **Emeralds:** {emeralds}\n\nChoose an upgrade to improve your village:"
    else:
        description = f"💎 **Emeralds:** {emeralds}\n\nUnknown upgrade target '{invalid_target}'. Available upgrades:"

    embed = discord.Embed(
        title="⬆️ Available Upgrades",
        description=description,
        color=discord.Color.gold(),
    )

    if next_trading_villager:
        embed.add_field(
            name="🏛️ Trading Hall - Available",
            value=(
                "Upgrade your trading hall to unlock the next villager tier.\n"
                f"• **Next Tier:** {next_trading_villager['name']}\n"
                f"• **Unlocks:** {next_trading_villager['description']}\n"
                f"• **Price:** 💎 {next_trading_villager['price']} emeralds\n"
                f"• **Use:** `{bot.command_prefix}shop upgrade trading`"
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name="✅ Trading Hall - Fully Upgraded",
            value="Your Trading Hall is already at maximum level.",
            inline=False,
        )

    return embed


def get_villager_state(current_level: int, villager_level: int) -> str:
    if villager_level <= current_level:
        return "owned"
    elif villager_level == current_level + 1:
        return "available"
    else:
        return "locked"


def get_villager_by_level(villagers: dict, level: int) -> dict | None:
    for _, villager in villagers.items():
        if villager["level"] == level:
            return villager
    return None
