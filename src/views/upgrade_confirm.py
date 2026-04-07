import discord


class UpgradeTradingView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, villager: dict):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.villager = villager

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Only the player upgrading can use these buttons.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm Upgrade", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.bot.shop_service.perform_trading_hall_upgrade(self.bot.db, self.guild_id, self.user_id)

        if not result["success"]:
            await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
            self.stop()
            return

        message = interaction.message
        if message is None or not message.embeds:
            return
        embed = message.embeds[0]
        embed.title = "✅ Trading Hall Upgraded!"
        embed.color = discord.Color.green()
        embed.add_field(name="Unlocked", value=f"{result['upgraded_to']['name']}", inline=False)

        button.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"🏛️ Your Trading Hall is now **Tier {result['upgraded_to']['level']}**!")

        self.stop()
