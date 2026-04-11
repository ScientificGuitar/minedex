import time

import discord


class FarmerTradeConfirm(discord.ui.View):
    def __init__(self, bot, guild_id, user_id, mob_id, amount, emeralds, timeout=60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.mob_id = mob_id
        self.amount = amount
        self.emeralds = emeralds

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This trade isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = int(time.time())

        self.bot.trade_service.perform_farmer_trade(
            self.bot.db, self.guild_id, self.user_id, self.mob_id, self.amount, self.emeralds
        )

        # Evaluate achievements
        newly_unlocked = self.bot.achievement_service.evaluate_unlocked(
            self.bot.db, self.guild_id, self.user_id, "farmer_trade", now
        )

        button.disabled = True

        embed = discord.Embed(
            title="✅ Trade Completed",
            description=f"You traded **{self.amount}** mobs for **{self.emeralds} emeralds**.{self._format_achievement_notifications(newly_unlocked)}",
            colour=discord.Colour.green(),
        )

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    def _format_achievement_notifications(self, newly_unlocked):
        """Format achievement notifications for embed description."""
        if not newly_unlocked:
            return ""

        achievement_msgs = []
        for ach in newly_unlocked:
            achievement_msgs.append(f"\n🏆 **{ach['name']}** - {ach['description']}")
        return "".join(achievement_msgs)
