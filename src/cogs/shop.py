import discord
from discord.ext import commands

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
            emeralds = self.bot.shop_service.get_user_emeralds(self.bot.db, guild_id, user_id)

            embed = discord.Embed(
                title="🏪 Marketplace", description=f"💎 **Emeralds:** {emeralds}", color=discord.Color.gold()
            )
            embed.add_field(name="🏛️ Trading Hall", value="Upgrade your village to unlock new services", inline=False)
            embed.set_footer(text=f"Use {self.bot.command_prefix}shop <category> to browse")

            await ctx.send(embed=embed)

        elif category == "upgrade":
            if target is None:
                upgrade_data = self.bot.shop_service.get_upgrade_data(self.bot.db, guild_id, user_id)
                embed = self._build_upgrade_list_embed(upgrade_data)
                await ctx.send(embed=embed)
                return

            if target == "trading":
                upgrade_data = self.bot.shop_service.get_upgrade_data(self.bot.db, guild_id, user_id, target)

                if "error" in upgrade_data:
                    await ctx.send(f"✅ {upgrade_data['error']}")
                    return

                embed = self._build_trading_hall_upgrade_embed(upgrade_data)
                view = UpgradeTradingView(
                    bot=self.bot, guild_id=guild_id, user_id=user_id, villager=upgrade_data["next_villager"]
                )
                await ctx.send(embed=embed, view=view)

            else:
                upgrade_data = self.bot.shop_service.get_upgrade_data(self.bot.db, guild_id, user_id, target)
                embed = self._build_upgrade_list_embed(upgrade_data)
                await ctx.send(embed=embed)
                return

        elif category == "trading":
            trading_data = self.bot.shop_service.get_trading_hall_data(self.bot.db, guild_id, user_id)
            embed = self._build_trading_hall_embed(trading_data)
            await ctx.send(embed=embed)

    def _build_upgrade_list_embed(self, data):
        if data.get("invalid_target"):
            description = f"💎 **Emeralds:** {data['emeralds']}\n\nUnknown upgrade target '{data['invalid_target']}'. Available upgrades:"
        else:
            description = f"💎 **Emeralds:** {data['emeralds']}\n\nChoose an upgrade to improve your village:"

        embed = discord.Embed(
            title="⬆️ Available Upgrades",
            description=description,
            color=discord.Color.gold(),
        )

        if data.get("next_trading_villager"):
            villager = data["next_trading_villager"]
            embed.add_field(
                name="🏛️ Trading Hall - Available",
                value=(
                    "Upgrade your trading hall to unlock the next villager tier.\n"
                    f"• **Next Tier:** {villager['name']}\n"
                    f"• **Unlocks:** {villager['description']}\n"
                    f"• **Price:** 💎 {villager['price']} emeralds\n"
                    f"• **Use:** `{self.bot.command_prefix}shop upgrade trading`"
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

    def _build_trading_hall_upgrade_embed(self, data):
        current_villager = (
            self.bot.shop_service._get_villager_by_level(data["current_level"]) if data["current_level"] > 0 else None
        )

        embed = discord.Embed(
            title="⬆️ Upgrade Trading Hall",
            description=(
                f"**Current Tier:** {current_villager['name'] if current_villager else 'None'}\n"
                f"**Next Tier:** {data['next_villager']['name']}\n\n"
                f"**Unlocks:**\n• {data['next_villager']['description']}\n\n"
                f"💎 **Price:** {data['price']} emeralds"
            ),
            color=discord.Color.gold(),
        )

        embed.set_footer(text="Confirm to upgrade your Trading Hall")
        return embed

    def _build_trading_hall_embed(self, data):
        embed = discord.Embed(
            title="🏛️ Trading Hall",
            description=f"Upgrade your village to unlock new services.\n\n💎 **Emeralds:** {data['emeralds']}",
            color=discord.Color.gold(),
        )

        for villager_data in data["villagers"]:
            if villager_data["state"] == "owned":
                embed.add_field(
                    name=f"✅ {villager_data['name']} - Owned",
                    value=f"• {villager_data['description']}",
                    inline=False,
                )
            elif villager_data["state"] == "available":
                embed.add_field(
                    name=f"🔓 {villager_data['name']} - Available",
                    value=(f"• {villager_data['description']}\n• **Price:** 💎 {villager_data['price']} emeralds\n"),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"🔒 {villager_data['name']} - Locked",
                    value=f"• {villager_data['description']}",
                    inline=False,
                )

        embed.set_footer(
            text=f"Use `{self.bot.command_prefix}shop upgrade trading` to upgrade your trading hall and unlock the next villager"
        )
        return embed


async def setup(bot):
    await bot.add_cog(Shop(bot))
