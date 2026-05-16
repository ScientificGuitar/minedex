import discord

from constants import RARITY_EMOJIS


class CollectionView(discord.ui.View):
    def __init__(self, bot, user_id: int, guild_id: int, rows: list, current_page: int = 1):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.rows = rows
        self.current_page = current_page

        data = bot.collection_service.build_collection_embed_data(rows, page=current_page)
        total_pages = data.get("total_pages", 1)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "prev":
                    item.disabled = current_page <= 1
                elif item.custom_id == "next":
                    item.disabled = current_page >= total_pages

    def _embed_from_data(self, data: dict, display_name: str) -> discord.Embed:
        if "error" in data:
            return discord.Embed(
                title="❌ Error",
                description=data["error"],
                colour=discord.Colour.red(),
            )

        embed = discord.Embed(
            title=f"{display_name}'s Collection",
            colour=discord.Colour.green(),
            description=f"Page {data['current_page']}/{data['total_pages']} ({data['total_entries']} mobs total) - {data['completion_pct']:.1f}% Complete",
        )

        for rarity_name, entries in data["entries"].items():
            embed.add_field(
                name=f"{RARITY_EMOJIS[rarity_name]} {rarity_name}",
                value="\n".join(entries),
                inline=False,
            )

        embed.set_footer(text="Use the buttons below to navigate or DM your full collection.")
        return embed

    async def build_embed(self, page: int, display_name: str) -> discord.Embed:
        data = self.bot.collection_service.build_collection_embed_data(self.rows, page=page)
        return self._embed_from_data(data, display_name)

    async def _update_message(self, interaction: discord.Interaction):
        data = self.bot.collection_service.build_collection_embed_data(self.rows, page=self.current_page)
        embed = self._embed_from_data(data, interaction.user.display_name)
        total_pages = data.get("total_pages", 1)

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "prev":
                    item.disabled = self.current_page <= 1
                elif item.custom_id == "next":
                    item.disabled = self.current_page >= total_pages

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self._update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self._update_message(interaction)

    @discord.ui.button(label="📨 DM Full Collection", style=discord.ButtonStyle.primary, custom_id="dm")
    async def dm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pages = self.bot.collection_service.get_full_collection_data(self.rows)
        embeds = [self._page_to_embed(p, interaction.user.display_name) for p in pages]
        try:
            await interaction.user.send(embeds=embeds)
            await interaction.response.send_message("✅ Your full collection has been sent via DM!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't DM you. Please enable DMs from server members and try again.", ephemeral=True
            )

    def _page_to_embed(self, page: dict, display_name: str) -> discord.Embed:
        embed = discord.Embed(
            title=page["title"],
            colour=discord.Colour.green(),
        )
        if page.get("description"):
            embed.description = page["description"]
        for field in page["fields"]:
            rarity_name = field["name"]
            embed.add_field(
                name=f"{RARITY_EMOJIS.get(rarity_name, '')} {rarity_name}",
                value=field["value"],
                inline=False,
            )
        if page["title"] == "Full Collection":
            embed.set_author(name=display_name)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This collection viewer isn't for you.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        message = self.message
        if message:
            await message.edit(view=self)
