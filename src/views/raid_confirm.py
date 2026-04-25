import discord


class RaidConfirmView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, mob_id: str, amount: int, power: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.mob_id = mob_id
        self.amount = amount
        self.power = power
        self.confirmed = False

    @discord.ui.button(label="Confirm Donation", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot confirm this donation.", ephemeral=True)

        result = self.bot.raid_service.donate_mob(self.bot.db, self.guild_id, self.user_id, self.mob_id, self.amount)
        
        if result["success"]:
            self.confirmed = True
            embed = discord.Embed(
                title="⚔️ Donation Successful!",
                description=f"You sacrificed **{self.amount}x {result['mob_name']}** and contributed **{result['power_donated']} Power** to the village defenses!",
                color=discord.Color.green()
            )
            
            if result["phase_completed"]:
                if result["raid_finished"]:
                    # Get the results and trigger the announcement in the cog
                    rewards = self.bot.raid_service.calculate_rewards(self.bot.db, self.guild_id)
                    raid_cog = self.bot.get_cog("RaidCog")
                    if raid_cog:
                        await raid_cog.announce_victory(self.guild_id, result["mob_name"], rewards)
                else:
                    embed.add_field(name="🚀 PHASE COMPLETE!", value="The server has advanced to the next phase of the raid!", inline=False)
            
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
        else:
            await interaction.response.send_message(f"❌ Error: {result['error']}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Donation cancelled.", embed=None, view=None)
        self.stop()
