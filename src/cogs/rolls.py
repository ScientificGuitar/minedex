import random
import time

import discord
from discord.ext import commands

from constants import RARITY_COLORS, RARITY_EMOJIS, RARITY_WEIGHTS, VALID_TOKEN_RARITIES
from database.collection import Collection
from database.inventory import Inventory
from database.user import User, same_utc_day
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
        user = User.get_user(self.bot.db, guild_id, user_id)

        user_trading_hall_level = user.trading_hall_level if user else 0
        if user_trading_hall_level < self.bot.villagers["toolsmith"]["level"]:
            await ctx.send(
                "❌ Your village doesn't have a Toolsmith yet! Upgrade your Trading Hall to get one reroll per day."
            )
            return

        last_claim_at = user.last_claim_at if user else 0
        user_tz = user.timezone if user else None
        if same_utc_day(last_claim_at, now, user_tz):
            await ctx.send("❌ You've already claimed today.")
            return

        last_reroll_at = user.last_reroll_at if user else 0
        if same_utc_day(last_reroll_at, now, user_tz):
            await ctx.send("❌ You've already rerolled today.")
            return

        mob_id, mob = self.roll_random_mob()
        User.record_reroll(self.bot.db, guild_id, user_id, now)

        embed = self.build_mob_embed(
            guild_id=guild_id,
            user_id=user_id,
            mob_id=mob_id,
            mob=mob,
            display_name=ctx.author.display_name,
            rerolled=True,
        )

        await ctx.send(
            embed=embed,
            view=Claim(bot=self.bot, guild_id=guild_id, user_id=ctx.author.id, mob_id=mob_id, mob=mob),
        )

    @commands.command()
    async def roll(self, ctx, mode: str | None = None, value: str | None = None):
        mode = mode.lower() if mode else None
        value = value.lower() if value else None

        guild_id = ctx.guild.id
        user_id = ctx.author.id
        now = int(time.time())

        User.ensure_user(self.bot.db, guild_id, user_id)
        user = User.get_user(self.bot.db, guild_id, user_id)

        if mode is None:
            roll_type = "standard"
        elif mode == "focus":
            user_trading_hall_level = user.trading_hall_level if user else 0
            if user_trading_hall_level < self.bot.villagers["librarian"]["level"]:
                await ctx.send(
                    "❌ Your village doesn't have a Librarian yet! Upgrade your Trading Hall to get one focus roll per day."
                )
                return
            roll_type = mode
        elif mode == "token":
            if value is None:
                await ctx.send("❌ You must specify a token rarity (e.g. `uncommon`, `rare`, `epic`).")
                return
            if value not in VALID_TOKEN_RARITIES:
                await ctx.send(f"❌ Invalid token rarity. Valid options: {', '.join(VALID_TOKEN_RARITIES)}")
                return
            roll_type = mode
            token_id = f"token_{value}_roll"
        else:
            await ctx.send(
                f"❌ Invalid roll type. Try `{self.bot.command_prefix}roll`, `{self.bot.command_prefix}roll focus`, or `{self.bot.command_prefix}roll token <rarity>`."
            )
            return

        last_claim_at = user.last_claim_at if user else 0
        user_tz = user.timezone if user else None
        if same_utc_day(last_claim_at, now, user_tz):
            await ctx.send("❌ You've already claimed today.")
            return

        last_roll_at = user.last_roll_at if user else None
        cooldown = get_cooldown_remaining(last_roll_at, now, 3600)
        if cooldown > 0:
            minutes = cooldown // 60
            if minutes == 0:
                msg = "⏳ You can roll again in less than a minute."
            else:
                msg = f"⏳ You can roll again in **{minutes} minutes**."
            await ctx.send(msg)
            return

        if roll_type == "standard":
            mob_id, mob = self.roll_random_mob()
            User.record_roll(self.bot.db, guild_id, user_id, now)
        elif roll_type == "focus":
            if User.has_focus_rolled_today(self.bot.db, guild_id, user_id, now):
                await ctx.send("❌ You've already focus rolled today.")
                return
            mob_id, mob = self.roll_random_mob(exclude={"Common"})
            User.record_focus_roll(self.bot.db, guild_id, user_id, now)
        elif roll_type == "token":
            inventory = Inventory.get_item(self.bot.db, guild_id, user_id, token_id)
            token_count = inventory["amount"] if inventory else 0
            if token_count <= 0:
                await ctx.send("❌ You do not have enough of that token type.")
                return

            Inventory.add_to_inventory(self.bot.db, guild_id, user_id, token_id, -1)
            mob_id, mob = self.roll_random_mob(allowed={value.capitalize()} if value else None)
            User.record_roll(self.bot.db, guild_id, user_id, now)

        embed = self.build_mob_embed(
            guild_id=guild_id, user_id=user_id, mob_id=mob_id, mob=mob, display_name=ctx.author.display_name
        )

        await ctx.send(
            embed=embed,
            view=Claim(bot=self.bot, guild_id=guild_id, user_id=ctx.author.id, mob_id=mob_id, mob=mob),
        )

    def roll_random_mob(self, exclude=None, allowed=None):
        rarity = Rolls.roll_rarity(exclude, allowed)
        mob = random.choice(self.bot.mobs_by_rarity[rarity])
        return mob, self.bot.mobs[mob]

    @staticmethod
    def roll_rarity(exclude=None, allowed=None):
        exclude = exclude or set()
        if allowed:
            rarities = [r for r in allowed if r in RARITY_WEIGHTS]
        else:
            rarities = [r for r in RARITY_WEIGHTS if r not in exclude]
        weights = [RARITY_WEIGHTS[r] for r in rarities]

        return random.choices(rarities, weights=weights, k=1)[0]

    def build_mob_embed(
        self, guild_id: int, user_id: int, mob_id: str, mob: dict, display_name: str, rerolled: bool = False
    ) -> discord.Embed:
        owned_amount = Collection.get_mob_count(self.bot.db, guild_id, user_id, mob_id) or 0
        emoji = RARITY_EMOJIS.get(mob["rarity"], "❔")
        color = RARITY_COLORS.get(mob["rarity"], 0x2F3136)

        if owned_amount > 0:
            embed = discord.Embed(
                title=f"{emoji} {mob['name']} - Duplicate!",
                description=(
                    f"**Rarity:** {mob['rarity']}\n"
                    f"**You already own:** {owned_amount}\n"
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
