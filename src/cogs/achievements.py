import discord
from discord.ext import commands


class Achievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def achievements(self, ctx):
        """View your unlocked achievements."""
        guild_id = ctx.guild.id
        user_id = ctx.author.id

        achievements = self.bot.achievement_service.get_user_achievements(self.bot.db, guild_id, user_id)

        if not achievements:
            embed = discord.Embed(
                title="🏆 Your Achievements",
                description="You haven't unlocked any achievements yet. Keep playing to earn them!",
                color=discord.Color.blue(),
            )
        else:
            embed = discord.Embed(
                title="🏆 Your Achievements",
                description=f"You've unlocked {len(achievements)} achievement{'s' if len(achievements) != 1 else ''}!",
                color=discord.Color.blue(),
            )

            # Group by category
            categories = {}
            for ach in achievements:
                cat = ach["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ach)

            for category, achs in categories.items():
                value = "\n".join([f"• **{ach['name']}** - {ach['description']}" for ach in achs])
                embed.add_field(name=category.title(), value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        """View your lifetime statistics."""
        guild_id = ctx.guild.id
        user_id = ctx.author.id

        stats = self.bot.achievement_service.get_user_stats(self.bot.db, guild_id, user_id)

        embed = discord.Embed(
            title="📊 Your Statistics",
            color=discord.Color.green(),
        )

        # Collection stats
        embed.add_field(
            name="📚 Collection",
            value=f"**Unique Mobs:** {stats['unique_mobs']}/{stats['total_mobs']}\n"
            f"**Completion:** {stats['collection_completion']:.1f}%\n"
            f"**Trading Hall:** Tier {stats['trading_hall_level']}",
            inline=True,
        )

        # Economy stats
        embed.add_field(
            name="💎 Economy",
            value=f"**Current Emeralds:** {stats['emeralds']:,}\n**Total Earned:** {stats['total_emeralds_gained']:,}",
            inline=True,
        )

        # Activity stats
        embed.add_field(
            name="🎲 Activity",
            value=f"**Total Rolls:** {stats['total_rolls']:,}\n**Total Claims:** {stats['total_claims']:,}\n",
            inline=True,
        )

        # Trading stats
        embed.add_field(
            name="🤝 Trading",
            value=f"**Farmer Trades:** {stats['total_farmer_trades']:,}\n"
            f"**Cleric Trades:** {stats['total_cleric_trades']:,}\n",
            inline=True,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Achievements(bot))
