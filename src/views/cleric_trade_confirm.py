import time

import discord


class ClericTradeConfirm(discord.ui.View):
    def __init__(self, bot, guild_id, user_id, mob_id, mob_amount, token_id, token, timeout=60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.mob_id = mob_id
        self.mob_amount = mob_amount
        self.token_id = token_id
        self.token = token

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This trade isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = int(time.time())
        token_count = self.mob_amount // 2

        self.bot.trade_service.perform_cleric_trade(
            self.bot.db, self.guild_id, self.user_id, self.mob_id, self.mob_amount, self.token_id, token_count
        )

        # Evaluate achievements
        newly_unlocked = self.bot.achievement_service.evaluate_unlocked(
            self.bot.db, self.guild_id, self.user_id, "cleric_trade", now
        )

        button.disabled = True

        embed = discord.Embed(
            title="✅ Trade Completed",
            description=f"You traded **{self.mob_amount}** mobs for **{token_count} {self.token['name']}** tokens.{self._format_achievement_notifications(newly_unlocked)}",
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
