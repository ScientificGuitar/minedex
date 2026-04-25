import discord
from discord.ext import commands

from constants import RARITY_COLORS, RARITY_EMOJIS
from database.user import User


class CollectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def collection(self, ctx, collection_filter: int | str = 1):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        rows = self.bot.collection_service.get_user_collection(self.bot.db, guild_id, user_id)

        if not rows:
            await ctx.send(f"📭 Your collection is empty. Try `{self.bot.command_prefix}roll`!")
            return

        if isinstance(collection_filter, int):
            embed_data = self.bot.collection_service.build_collection_embed_data(rows, page=collection_filter)
        else:
            embed_data = self.bot.collection_service.build_collection_embed_data(rows, rarity_filter=collection_filter)

        if "error" in embed_data:
            embed = discord.Embed(
                title="❌ Error",
                description=embed_data["error"],
                colour=discord.Colour.red(),
            )
        else:
            embed = self._build_embed_from_data(embed_data, ctx.author.display_name)

        await ctx.send(embed=embed)

    @commands.command()
    async def missing(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        missing_by_rarity = self.bot.collection_service.get_missing_mobs(self.bot.db, guild_id, user_id)

        if not missing_by_rarity:
            await ctx.send("🎉 You have collected all mobs! Congratulations!")
            return

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Missing Collection", colour=discord.Colour.red())

        rarity_order = [
            ":orange_circle: Legendary",
            ":purple_circle: Epic",
            ":blue_circle: Rare",
            ":green_circle: Uncommon",
            ":white_circle: Common",
        ]

        for rarity_display in rarity_order:
            symbol, rarity = rarity_display.split(" ")
            if rarity in missing_by_rarity:
                mob_list = missing_by_rarity[rarity]
                if len(", ".join(mob_list)) > 1000:
                    mob_list = mob_list[:10] + [f"... and {len(mob_list) - 10} more"]
                embed.add_field(name=f"{symbol} {rarity}", value=", ".join(mob_list), inline=False)

        total_missing = sum(len(mobs) for mobs in missing_by_rarity.values())
        embed.set_footer(text=f"Total missing: {total_missing} mobs")
        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx, category: str | None = None):
        if ctx.guild is None:
            await ctx.send("❌ Leaderboards can only be viewed in a server.")
            return
        normalized = category.lower() if category else None
        if normalized in {"collection", "completion"}:
            category_key = "completion"
        elif normalized in {"emeralds", "emerald"}:
            category_key = "emeralds"
        elif normalized is None:
            category_key = None
        else:
            await ctx.send("❌ Invalid leaderboard category. Available categories: emeralds, completion.")
            return

        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)

        leaderboard_data = self.bot.collection_service.get_leaderboards(self.bot.db, guild_id, limit=5)
        if not any(leaderboard_data.values()):
            await ctx.send("📭 No leaderboard data is available yet.")
            return

        embed = discord.Embed(title="🏆 Leaderboards", colour=discord.Colour.gold())

        if category_key is None or category_key == "emeralds":
            embed.add_field(
                name="💎 Emeralds",
                value=self._format_emerald_leaderboard(ctx.guild, leaderboard_data["emeralds"]),
                inline=False,
            )

        if category_key is None or category_key == "completion":
            embed.add_field(
                name="📚 Collection Completion",
                value=self._format_completion_leaderboard(ctx.guild, leaderboard_data["completion"]),
                inline=False,
            )

        embed.set_footer(text=f"Use {self.bot.command_prefix}collection to view your collection.")
        await ctx.send(embed=embed)

    def _format_emerald_leaderboard(self, guild, rows):
        if not rows:
            return "No emerald leaderboard entries yet."

        lines = []
        for idx, row in enumerate(rows, start=1):
            display_name = self._get_member_display_name(row["user_id"], guild)
            lines.append(f"{idx}. {display_name} — {row['emeralds']} 💎")

        return "\n".join(lines)

    def _format_completion_leaderboard(self, guild, rows):
        if not rows:
            return "No completion leaderboard entries yet."

        lines = []
        total_unique = len(self.bot.mobs)
        for idx, row in enumerate(rows, start=1):
            display_name = self._get_member_display_name(row["user_id"], guild)
            lines.append(
                f"{idx}. {display_name} — {row['unique_count']}/{total_unique} ({row['completion_pct']:.1f}%)"
            )

        return "\n".join(lines)

    def _get_member_display_name(self, user_id: int, guild):
        if guild is None:
            return f"<@{user_id}>"

        member = guild.get_member(user_id)
        return member.display_name if member else f"<@{user_id}>"

    @commands.command()
    async def mobs(self, ctx, mob_filter: int | str = 1):
        if isinstance(mob_filter, int):
            await self._all_mobs(ctx, mob_filter)
            return

        await self._mobs_by_rarity(ctx, mob_filter)

    @commands.command()
    async def mob(self, ctx, mob_id: str):
        mob = self.bot.collection_service.get_mob_info(mob_id)
        if not mob:
            await ctx.send("❌ That mob does not exist.")
            return

        rarity = mob["rarity"]
        color = RARITY_COLORS[rarity]

        embed = discord.Embed(title=f"{mob['name']}", description=f"*{mob.get('lore', '')}*", color=color)
        embed.set_image(url=mob["image"])
        embed.set_footer(text=f"Mob ID: {mob_id}")

        await ctx.send(embed=embed)

    def _build_embed_from_data(self, data, display_name):
        embed = discord.Embed(
            title=f"{display_name}'s Collection",
            colour=discord.Colour.green(),
            description=f"Page {data['current_page']}/{data['total_pages']} ({data['total_entries']} mobs total) — {data['completion_pct']:.1f}% Complete",
        )

        for rarity_name, entries in data["entries"].items():
            embed.add_field(
                name=f"{RARITY_EMOJIS[rarity_name]} {rarity_name}",
                value="\n".join(entries),
                inline=False,
            )

        footer_text = f"Use {self.bot.command_prefix}collection <page> to navigate"
        if data.get("rarity_filter"):
            footer_text += f" | Filtering by rarity: {data['rarity_filter'].capitalize()}"
        embed.set_footer(text=footer_text)
        return embed

    async def _all_mobs(self, ctx, page: int = 1):
        data = self.bot.collection_service.get_all_mobs_paginated(page)

        if "error" in data:
            await ctx.send(data["error"])
            return

        embed = discord.Embed(
            title="📘 Mob Bestiary", description="All known mobs, grouped by rarity.", color=discord.Color.dark_gray()
        )

        for rarity, mob_names in data["mobs"].items():
            embed.add_field(
                name=f"{RARITY_EMOJIS[rarity]} {rarity}",
                value="• " + "\n• ".join(mob_names),
                inline=False,
            )

        embed.set_footer(
            text=(
                f"Page {data['current_page']}/{data['total_pages']} ({data['total_mobs']} total mobs) | Use {self.bot.command_prefix}mobs <page> to navigate\n"
                f"Use {self.bot.command_prefix}mobs <rarity> to filter by rarity\n"
                f"Use {self.bot.command_prefix}mob <mob_name> for more information about a specific mob"
            )
        )
        await ctx.send(embed=embed)

    async def _mobs_by_rarity(self, ctx, rarity: str):
        data = self.bot.collection_service.get_mobs_by_rarity(rarity)

        if "error" in data:
            await ctx.send(data["error"])
            return

        embed = discord.Embed(
            title=f"{RARITY_EMOJIS[data['rarity']]} {data['rarity']} Mobs",
            description="• " + "\n• ".join(data["mobs"]),
            color=RARITY_COLORS[data["rarity"]],
        )

        embed.set_footer(text=f"Total: {data['count']} mobs")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CollectionCog(bot))
