import discord
from discord.ext import commands

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
            check_result = self.bot.trade_service.can_trade_with_farmer(
                self.bot.db, guild_id, user_id, mob_id, mob_amount
            )
            if not check_result["can_trade"]:
                await ctx.send(f"❌ {check_result['error']}")
                return

            mob = check_result["mob"]
            trade_data = self.bot.trade_service.calculate_farmer_trade(mob, mob_amount)

            embed = discord.Embed(
                title="Farmer Trade Offer",
                colour=discord.Colour.green(),
            )
            embed.add_field(
                name="You Give",
                value=f"🃏 **{trade_data['mob']['name']}** x{trade_data['mob_amount']} ({trade_data['mob']['rarity']})",
                inline=False,
            )
            embed.add_field(
                name="You Receive",
                value=f"💎 **Emeralds** x{trade_data['emeralds']} ({trade_data['value_per']}💎 each)",
                inline=False,
            )

            embed.set_thumbnail(url=trade_data["mob"]["image"])
            embed.set_footer(text="Confirming this trade will permanently remove the mobs.")

            view = FarmerTradeConfirm(
                bot=self.bot,
                guild_id=guild_id,
                user_id=user_id,
                mob_id=mob_id,
                amount=mob_amount,
                emeralds=trade_data["emeralds"],
            )

            await ctx.send(embed=embed, view=view)
        elif villager == "cleric":
            check_result = self.bot.trade_service.can_trade_with_cleric(
                self.bot.db, guild_id, user_id, mob_id, mob_amount
            )
            if not check_result["can_trade"]:
                await ctx.send(f"❌ {check_result['error']}")
                return

            mob = check_result["mob"]
            trade_data = self.bot.trade_service.calculate_cleric_trade(mob, mob_amount)

            embed = discord.Embed(
                title="Cleric Trade Offer",
                colour=discord.Colour.green(),
            )
            embed.add_field(
                name="You Give",
                value=f"🃏 **{trade_data['mob']['name']}** x{trade_data['mob_amount']} ({trade_data['mob']['rarity']})",
                inline=False,
            )
            embed.add_field(
                name="You Receive",
                value=f"🪙 **{trade_data['token']['name']}** x{trade_data['token_count']} (2 mobs → 1 token)",
                inline=False,
            )

            embed.set_thumbnail(url=trade_data["mob"]["image"])
            embed.set_footer(text="Confirming this trade will permanently remove the mobs.")

            view = ClericTradeConfirm(
                bot=self.bot,
                guild_id=guild_id,
                user_id=user_id,
                mob_id=mob_id,
                mob_amount=mob_amount,
                token_id=trade_data["token_id"],
                token=trade_data["token"],
            )

            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(
                "❌ That villager does not exist.\nUse `{self.bot.command_prefix}help trading` for more information about trading"
            )
            return


async def setup(bot):
    await bot.add_cog(Trade(bot))
