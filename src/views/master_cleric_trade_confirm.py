import time

import discord


class MasterClericTradeConfirm(discord.ui.View):
    def __init__(self, bot, guild_id, user_id, mob_id, mob_amount, token_id, token, fee, timeout=60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.mob_id = mob_id
        self.mob_amount = mob_amount
        self.token_id = token_id
        self.token = token
        self.fee = fee

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This trade isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = int(time.time())

        # Re-validate: dupes + fee may have changed since the offer was shown
        check = self.bot.trade_service.can_trade_with_master_cleric(
            self.bot.db, self.guild_id, self.user_id, self.mob_id, self.mob_amount
        )
        if not check["can_trade"]:
            await interaction.response.send_message(f"❌ {check['error']}", ephemeral=True)
            return

        trade_data = self.bot.trade_service.calculate_master_cleric_trade(
            check["mob"], self.mob_amount
        )
        token_count = trade_data["token_count"]
        fee = trade_data["fee"]

        self.bot.trade_service.perform_master_cleric_trade(
            self.bot.db,
            self.guild_id,
            self.user_id,
            self.mob_id,
            self.mob_amount,
            trade_data["token_id"],
            token_count,
            fee,
        )

        # Evaluate achievements (reuse cleric_trade event so no new wiring needed)
        newly_unlocked = self.bot.achievement_service.evaluate_unlocked(
            self.bot.db, self.guild_id, self.user_id, "cleric_trade", now
        )

        button.disabled = True

        embed = discord.Embed(
            title="✅ Trade Completed",
            description=f"You traded **{self.mob_amount}x {check['mob']['name']}** + **{fee} emeralds** for **{token_count}x {trade_data['token']['name']}**.{self._format_achievement_notifications(newly_unlocked)}",
            colour=discord.Colour.gold(),
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
