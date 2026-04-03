import discord
from discord.ext import commands

from constants import CLERIC_RARITY_TO_TOKEN, FARMER_EMERALD_VALUES
from database.collection import Collection
from database.user import User
from views.cleric_trade_confirm import ClericTradeConfirm
from views.farmer_trade_confirm import FarmerTradeConfirm


class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def farmer(self, ctx, mob_id: str | None = None, mob_amount: int | None = None):
        await self._trade_with_villager(ctx, "farmer", mob_id, mob_amount)

    @commands.command()
    async def cleric(self, ctx, mob_id: str | None = None, mob_amount: int | None = None):
        await self._trade_with_villager(ctx, "cleric", mob_id, mob_amount)

    @commands.command(aliases=["trading"])
    async def trade(self, ctx, villager: str | None = None, mob_id: str | None = None, mob_amount: int | None = None):
        if villager is None:
            await ctx.send(
                "❌ You need to specify **which villager** you want to trade with.\n\n"
                "Available villagers:\n"
                "• **farmer** - trade duplicate mobs for emeralds\n"
                "• **cleric** - trade duplicate mobs for roll tokens\n\n"
                "Example:\n"
                f"`{self.bot.command_prefix}trade farmer <mob_id> <amount>`"
            )
            return

        await self._trade_with_villager(ctx, villager, mob_id, mob_amount)

    async def _trade_with_villager(self, ctx, villager: str, mob_id: str | None, mob_amount: int | None):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        user = User.get_user(self.bot.db, guild_id, user_id)

        if mob_id is None:
            await ctx.send(
                f"❌ You need to specify **which mob** you want to trade.\n\nExample:\n`{self.bot.command_prefix}{villager} <mob_id> <amount>`"
            )
            return
        if mob_amount is None:
            await ctx.send(
                f"❌ You need to specify **how many** mobs you want to trade.\n\nExample:\n`{self.bot.command_prefix}{villager} <mob_id> 1`"
            )
            return
        elif villager.lower() == "farmer":
            user_trading_hall_level = user.trading_hall_level if user else 0
            if user_trading_hall_level < self.bot.villagers["farmer"]["level"]:
                await ctx.send(
                    "❌ Your village doesn't have a Farmer yet! Upgrade your Trading Hall to trade your duplicate mobs for emeralds!"
                )
                return

            mob = self.bot.mobs.get(mob_id)
            if not mob:
                await ctx.send("❌ That mob does not exist.")
                return

            user_mob_count = Collection.get_mob_count(self.bot.db, guild_id, user_id, mob_id) or 0
            if user_mob_count <= 1:
                await ctx.send(
                    "❌ You don't have any **duplicate copies** of this mob to trade.\n"
                    "_The Farmer only buys duplicates._"
                )
                return
            if mob_amount >= user_mob_count:
                await ctx.send(
                    f"❌ You must keep **at least 1 copy** of each mob.\n"
                    f"You can trade **up to {user_mob_count - 1}** of this mob."
                )
                return

            rarity = mob["rarity"]
            value_per = FARMER_EMERALD_VALUES[rarity]
            emeralds = mob_amount * value_per

            embed = discord.Embed(
                title="Farmer Trade Offer",
                colour=discord.Colour.green(),
            )
            embed.add_field(
                name="You Give",
                value=f"🃏 **{mob['name']}** x{mob_amount} ({rarity})",
                inline=False,
            )
            embed.add_field(
                name="You Receive",
                value=f"💎 **Emeralds** x{emeralds} ({value_per}💎 each)",
                inline=False,
            )

            embed.set_thumbnail(url=mob["image"])
            embed.set_footer(text="Confirming this trade will permanently remove the mobs.")

            view = FarmerTradeConfirm(
                bot=self.bot, guild_id=guild_id, user_id=user_id, mob_id=mob_id, amount=mob_amount, emeralds=emeralds
            )

            await ctx.send(embed=embed, view=view)
        elif villager == "cleric":
            user_trading_hall_level = user.trading_hall_level if user else 0
            if user_trading_hall_level < self.bot.villagers["cleric"]["level"]:
                await ctx.send(
                    "❌ Your village doesn't have a Cleric yet! Upgrade your Trading Hall to trade your duplicate mobs for tokens!"
                )
                return

            mob = self.bot.mobs.get(mob_id)
            if not mob:
                await ctx.send("❌ That mob does not exist.")
                return

            user_mob_count = Collection.get_mob_count(self.bot.db, guild_id, user_id, mob_id) or 0
            if user_mob_count <= 2:
                await ctx.send(
                    "❌ You need **at least 2 duplicate copies** of this mob to trade with the Cleric.\n"
                    "_The Cleric converts duplicates into tokens (2 mobs → 1 token)._"
                )
                return
            if mob_amount >= user_mob_count:
                await ctx.send(
                    f"❌ You must keep **at least 1 copy** of each mob.\n"
                    f"You can trade **up to {user_mob_count - 1}** of this mob."
                )
                return
            if mob_amount % 2 != 0:
                await ctx.send(
                    "❌ The Cleric only accepts **pairs of duplicates**.\n_Trade 2 mobs to receive 1 roll token._"
                )
                return

            mob_rarity = mob["rarity"]
            token_rarity = CLERIC_RARITY_TO_TOKEN[mob_rarity]
            token_id = token_rarity
            token_count = mob_amount // 2
            token = self.bot.items[token_id]

            embed = discord.Embed(
                title="Cleric Trade Offer",
                colour=discord.Colour.green(),
            )
            embed.add_field(
                name="You Give",
                value=f"🃏 **{mob['name']}** x{mob_amount} ({mob_rarity})",
                inline=False,
            )
            embed.add_field(
                name="You Receive",
                value=f"🪙 **{token['name']}** x{token_count} (2 mobs → 1 token)",
                inline=False,
            )

            embed.set_thumbnail(url=mob["image"])
            embed.set_footer(text="Confirming this trade will permanently remove the mobs.")

            view = ClericTradeConfirm(
                bot=self.bot,
                guild_id=guild_id,
                user_id=user_id,
                mob_id=mob_id,
                mob_amount=mob_amount,
                token_id=token_id,
                token=token,
            )

            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(
                "❌ That villager does not exist.\nUse `{self.bot.command_prefix}help trading` for more information about trading"
            )
            return


async def setup(bot):
    await bot.add_cog(Trade(bot))
