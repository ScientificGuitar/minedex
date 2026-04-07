import time

import discord
from discord.ext import commands

from constants import RARITY_COLORS, RARITY_EMOJIS
from database.user import User
from views.claim import Claim


class Rolls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def reroll(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        now = int(time.time())

        User.ensure_user(self.bot.db, guild_id, user_id)

        can_reroll_result = self.bot.roll_service.can_reroll(self.bot.db, guild_id, user_id, now)
        if not can_reroll_result["can_reroll"]:
            await ctx.send(f"❌ {can_reroll_result['error']}")
            return

        mob_id, mob = self.bot.roll_service.perform_reroll(self.bot.db, guild_id, user_id, now)

        embed = self._build_mob_embed(guild_id, user_id, mob_id, mob, ctx.author.display_name, rerolled=True)

        await ctx.send(
            embed=embed,
            view=Claim(bot=self.bot, guild_id=guild_id, user_id=ctx.author.id, mob_id=mob_id, mob=mob),
        )

    @commands.command()
    async def roll(self, ctx, mode: str | None = None, value: str | None = None):
        mode = mode.lower() if mode else "standard"
        value = value.lower() if value else None

        guild_id = ctx.guild.id
        user_id = ctx.author.id
        now = int(time.time())

        User.ensure_user(self.bot.db, guild_id, user_id)

        can_roll_result = self.bot.roll_service.can_roll(self.bot.db, guild_id, user_id, now, mode, value)
        if not can_roll_result["can_roll"]:
            await ctx.send(f"❌ {can_roll_result['error']}")
            return

        mob_id, mob = self.bot.roll_service.perform_roll(self.bot.db, guild_id, user_id, now, mode, value)

        embed = self._build_mob_embed(guild_id, user_id, mob_id, mob, ctx.author.display_name)

        await ctx.send(
            embed=embed,
            view=Claim(bot=self.bot, guild_id=guild_id, user_id=ctx.author.id, mob_id=mob_id, mob=mob),
        )

    def _build_mob_embed(
        self, guild_id: int, user_id: int, mob_id: str, mob: dict, display_name: str, rerolled: bool = False
    ) -> discord.Embed:
        embed_data = self.bot.roll_service.build_mob_embed_data(self.bot.db, guild_id, user_id, mob_id, mob, rerolled)

        emoji = RARITY_EMOJIS.get(mob["rarity"], "❔")
        color = RARITY_COLORS.get(mob["rarity"], 0x2F3136)

        if embed_data["owned_amount"] > 0:
            embed = discord.Embed(
                title=f"{emoji} {mob['name']} - Duplicate!",
                description=(
                    f"**Rarity:** {mob['rarity']}\n"
                    f"**You already own:** {embed_data['owned_amount']}\n"
                    "*💡 Duplicates can still be claimed.*"
                ),
                color=color,
            )
        else:
            embed = discord.Embed(
                title=f"{emoji} {mob['name']}",
                description=f"**Rarity:** {mob['rarity']}",
                color=color,
            )

        embed.set_image(url=mob["image"])
        action = "Rerolled" if rerolled else "Rolled"
        embed.set_footer(text=f"{action} by: {display_name}")
        return embed


async def setup(bot):
    await bot.add_cog(Rolls(bot))


def get_cooldown_remaining(last_action_ts: int | None, now_ts: int, cooldown_seconds: int) -> int:
    if last_action_ts is None:
        return 0

    elapsed = now_ts - last_action_ts
    return max(0, cooldown_seconds - elapsed)
