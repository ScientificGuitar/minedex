import time

import discord

from constants import RARITY_EMERALD_REWARDS
from database.collection import Collection
from database.user import User, same_utc_day


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

        user = User.get_user(self.bot.db, self.guild_id, self.user_id)
        last_claim_at = user.last_claim_at if user else 0
        user_tz = user.timezone if user else None
        if same_utc_day(last_claim_at, now, user_tz):
            await interaction.response.send_message("❌ You've already claimed today.", ephemeral=True)
            return

        reward = RARITY_EMERALD_REWARDS[self.mob["rarity"]]

        Collection.add_to_collection(self.bot.db, self.guild_id, self.user_id, self.mob_id)
        User.update_last_claim_at(self.bot.db, self.guild_id, self.user_id, now)
        User.add_emeralds(self.bot.db, self.guild_id, self.user_id, reward)

        button.disabled = True
        message = interaction.message
        if message is None or not message.embeds:
            return
        embed = message.embeds[0]
        embed.set_footer(text=f"🗸 Claimed by: {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(
            f"✅ {self.mob['rarity']} {self.mob['name']} claimed!\n💎 +{reward} emerald{'s' if reward != 1 else ''}!"
        )
        self.stop()
