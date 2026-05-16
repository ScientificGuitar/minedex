import time

import discord
from discord.ext import commands, tasks

from database.user import User
from views.raid_confirm import RaidConfirmView


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_check.start()

    def cog_unload(self):
        self.raid_check.cancel()

    async def announce_victory(self, guild_id: int, final_mob: str, rewards: list):
        """Broadcast raid victory and rewards to the server."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.system_channel or next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
        )
        if not channel:
            return

        embed = discord.Embed(
            title="🎊 RAID VICTORY! 🎊",
            description=f"The final sacrifice of **{final_mob}** was enough! The village is saved!",
            color=discord.Color.gold(),
        )

        # Format Top Contributors
        if rewards:
            # Sort rewards to show Top 3
            sorted_rewards = sorted(rewards, key=lambda r: r["power"], reverse=True)
            leaderboard_lines = []
            for idx, r in enumerate(sorted_rewards[:5], 1):
                member = guild.get_member(r["user_id"])
                name = member.display_name if member else f"User {r['user_id']}"
                icon = "💎" if r["tier"] == "diamond" else "🥇" if r["tier"] == "gold" else "🥈"
                leaderboard_lines.append(f"{idx}. **{name}** - {r['power']} Power {icon}")

            embed.add_field(name="🏆 Hall of Fame", value="\n".join(leaderboard_lines), inline=False)

            # Summary of loot
            total_emerald_payout = sum(r["loot"]["emeralds"] for r in rewards)
            embed.add_field(
                name="💰 Total Village Loot",
                value=f"{total_emerald_payout} Emeralds distributed across {len(rewards)} heroes!",
                inline=False,
            )

        embed.add_field(
            name="✨ Victory Boon Active",
            value="The village is celebrating! All emerald gains are increased by **15%** for the next 12 hours!",
            inline=False,
        )

        await channel.send(embed=embed)

    @tasks.loop(minutes=5)
    async def raid_check(self):
        """Background task to check for expired raids."""
        now = int(time.time())
        duration_sec = self.bot.raid_service.config["raid_duration_hours"] * 3600

        # We need a way to get all guilds the bot is in to check each one
        for guild in self.bot.guilds:
            raid = self.bot.raid_service.get_active_raid(self.bot.db, guild.id)
            if not raid:
                continue

            if now > raid.spawned_at + duration_sec:
                # Raid expired!
                self.bot.raid_service.complete_raid(self.bot.db, guild.id)

                # Notify the server
                channel = guild.system_channel or next(
                    (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
                )
                if channel:
                    embed = discord.Embed(
                        title="⌛ RAID EXPIRED",
                        description="The time has run out! The boss has vanished, leaving the village in disarray.",
                        color=discord.Color.dark_red(),
                    )
                    await channel.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def raid(self, ctx):
        """Show current raid status and progress."""
        guild_id = ctx.guild.id
        User.ensure_user(self.bot.db, guild_id, ctx.author.id)

        raid = self.bot.raid_service.get_active_raid(self.bot.db, guild_id)
        if not raid:
            await ctx.send("🏰 **Village Status:** Peaceful. No boss raids are active right now.")
            return

        boss_template = self.bot.raid_service.boss_data[raid.boss_id]
        phase_config = boss_template["phases"][raid.current_phase - 1]

        # Build progress bar
        progress_pct = (raid.current_power / raid.target_power) * 100 if raid.target_power > 0 else 0
        filled_blocks = int(progress_pct / 10)
        progress_bar = "🟢" * filled_blocks + "⚪" * (10 - filled_blocks)

        embed = discord.Embed(
            title=f"⚔️ RAID ALERT: {boss_template['name']}",
            description=f"{phase_config['description']}\n\n"
            f"**Phase {raid.current_phase}/3**\n"
            f"{progress_bar} {progress_pct:.1f}%\n"
            f"⚡ **Progress:** {raid.current_power} / {raid.target_power} Power",
            color=discord.Color.red(),
        )

        if raid.target_tag:
            embed.add_field(name="🏷️ Required Tag", value=f"**{raid.target_tag.capitalize()}**", inline=True)

        if "allowed_rarities" in phase_config:
            rarities = ", ".join(phase_config["allowed_rarities"])
            embed.add_field(name="💎 Allowed Rarities", value=f"**{rarities}**", inline=True)

        # Time remaining
        remaining_sec = (raid.spawned_at + (self.bot.raid_service.config["raid_duration_hours"] * 3600)) - int(
            time.time()
        )
        if remaining_sec > 0:
            hours = remaining_sec // 3600
            mins = (remaining_sec % 3600) // 60
            embed.set_footer(text=f"Time Remaining: {hours}h {mins}m | Use &raid donate <mob_id> <amount>")
        else:
            embed.set_footer(text="TIME EXPIRED! The village is in danger!")

        embed.set_thumbnail(url=boss_template["image"])

        await ctx.send(embed=embed)

    @raid.command(name="donate")
    async def donate(self, ctx, mob_id: str, amount: int = 1):
        """Donate mobs to the current raid phase."""
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)

        if amount <= 0:
            await ctx.send("❌ You must donate at least 1 mob.")
            return

        raid = self.bot.raid_service.get_active_raid(self.bot.db, guild_id)
        if not raid:
            await ctx.send("❌ There is no active raid to donate to.")
            return

        mob = self.bot.mobs.get(mob_id.lower())
        if not mob:
            await ctx.send("❌ That mob does not exist.")
            return

        # Check if they own the mob first (quick check before view)
        from database.collection import Collection as CollectionDB

        owned = CollectionDB.get_mob_count(self.bot.db, guild_id, user_id, mob_id.lower()) or 0
        if owned < amount:
            await ctx.send(f"❌ You only have **{owned}** copies of this mob.")
            return

        total_power = mob.get("base_power", 0) * amount

        embed = discord.Embed(
            title="⚔️ Confirm Raid Contribution",
            description=f"You are about to sacrifice **{amount}x {mob['name']}**.\n\n"
            f"💪 **Total Power Contribution:** {total_power}\n\n"
            f"⚠️ **Warning:** This will permanently remove these mobs from your collection.",
            color=discord.Color.orange(),
        )

        view = RaidConfirmView(self.bot, guild_id, user_id, mob_id.lower(), amount, total_power)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(RaidCog(bot))
