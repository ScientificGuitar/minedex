import time

import discord


class Claim(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, mob_id: str, mob: dict):
        super().__init__(timeout=3600)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.mob_id = mob_id
        self.mob = mob

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Only the player who rolled this card can claim it.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Claim!", style=discord.ButtonStyle.secondary, emoji="🔥")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = int(time.time())

        reward = self.bot.roll_service.claim_mob(self.bot.db, self.guild_id, self.user_id, self.mob_id, self.mob, now)

        # Evaluate achievements
        newly_unlocked = self.bot.achievement_service.evaluate_unlocked(
            self.bot.db, self.guild_id, self.user_id, "claim", now
        )

        button.disabled = True
        message = interaction.message
        if message is None or not message.embeds:
            return
        embed = message.embeds[0]
        embed.set_footer(text=f"🗸 Claimed by: {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=self)

        # Send claim message
        claim_msg = (
            f"✅ {self.mob['rarity']} {self.mob['name']} claimed!\n💎 +{reward} emerald{'s' if reward != 1 else ''}!"
        )

        # Add achievement notifications
        if newly_unlocked:
            achievement_msgs = []
            for ach in newly_unlocked:
                achievement_msgs.append(f"🏆 **{ach['name']}** - {ach['description']}")
            claim_msg += "\n\n" + "\n".join(achievement_msgs)

        await interaction.followup.send(claim_msg)
        self.stop()
