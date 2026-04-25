import discord
from discord.ext import commands

from database.user import User


class ShopCategoryButton(discord.ui.Button):
    def __init__(self, category_id: str, label: str, emoji: str, row: int):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary, row=row)
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_category(interaction, self.category_id)


class ShopItemSelect(discord.ui.Select):
    def __init__(self, category_id: str, items: list):
        options = []
        for item in items:
            description = f"{item['price']} Emeralds - {item['description']}"
            if len(description) > 100:
                description = description[:97] + "..."
                
            options.append(discord.SelectOption(
                label=item["name"],
                value=item["id"],
                description=description,
                emoji="💎"
            ))
            
        super().__init__(placeholder="Select an item to buy...", options=options)
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_item_details(interaction, self.category_id, self.values[0])


class ShopView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        
        # Initial category buttons
        self.add_item(ShopCategoryButton("permanent_upgrades", "Upgrades", "🏛️", 0))
        self.add_item(ShopCategoryButton("consumables", "Items", "🧪", 0))

    async def show_category(self, interaction: discord.Interaction, category_id: str):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu isn't for you!", ephemeral=True)

        inventory = self.bot.shop_service.get_shop_inventory(self.bot.db, self.guild_id, self.user_id, category_id)
        
        embed = discord.Embed(
            title=f"{'🏛️ Village Upgrades' if category_id == 'permanent_upgrades' else '🧪 Marketplace Items'}",
            description=f"💎 **Balance:** {inventory['emeralds']} Emeralds\n\nSelect an item from the menu below to view details and purchase.",
            color=discord.Color.gold()
        )
        
        # Update view
        self.clear_items()
        self.add_item(ShopCategoryButton("permanent_upgrades", "Upgrades", "🏛️", 0))
        self.add_item(ShopCategoryButton("consumables", "Items", "🧪", 0))
        self.add_item(ShopItemSelect(category_id, inventory["items"]))
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_item_details(self, interaction: discord.Interaction, category_id: str, item_id: str):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu isn't for you!", ephemeral=True)

        # Re-fetch inventory to get current state
        inventory = self.bot.shop_service.get_shop_inventory(self.bot.db, self.guild_id, self.user_id, category_id)
        item = next((i for i in inventory["items"] if i["id"] == item_id), None)
        
        if not item:
            return await interaction.response.send_message("Item not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"Purchase: {item['name']}",
            description=f"{item['description']}\n\n"
                        f"💰 **Price:** {item['price']} Emeralds\n"
                        f"💎 **Your Balance:** {inventory['emeralds']} Emeralds",
            color=discord.Color.blue()
        )
        
        if item["state"] == "owned":
            embed.set_footer(text="✅ You already own this upgrade.")
            can_buy = False
        elif item["state"] == "locked":
            embed.set_footer(text="🔒 You don't meet the requirements for this.")
            can_buy = False
        elif inventory["emeralds"] < item["price"]:
            embed.set_footer(text="❌ You don't have enough emeralds.")
            can_buy = False
        else:
            can_buy = True

        # Purchase confirm button
        confirm_button = discord.ui.Button(
            label="Confirm Purchase", 
            style=discord.ButtonStyle.green, 
            disabled=not can_buy,
            emoji="💰"
        )
        
        async def confirm_callback(btn_interaction: discord.Interaction):
            result = self.bot.shop_service.perform_purchase(self.bot.db, self.guild_id, self.user_id, item_id, category_id)
            if result["success"]:
                purchase_embed = discord.Embed(
                    title="🎉 Purchase Successful!",
                    description=f"You bought **{item['name']}** for **{item['price']}** Emeralds.",
                    color=discord.Color.green()
                )
                await btn_interaction.response.edit_message(embed=purchase_embed, view=None)
            else:
                await btn_interaction.response.send_message(f"❌ Error: {result['error']}", ephemeral=True)

        confirm_button.callback = confirm_callback
        
        # Add a back button
        back_button = discord.ui.Button(label="Back to List", style=discord.ButtonStyle.gray)
        async def back_callback(btn_interaction: discord.Interaction):
            await self.show_category(btn_interaction, category_id)
        back_button.callback = back_callback

        self.clear_items()
        self.add_item(confirm_button)
        self.add_item(back_button)
        
        await interaction.response.edit_message(embed=embed, view=self)


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        User.ensure_user(self.bot.db, guild_id, user_id)
        
        emeralds = self.bot.shop_service.get_user_emeralds(self.bot.db, guild_id, user_id)

        embed = discord.Embed(
            title="🏪 Marketplace", 
            description=f"Welcome to the Village Shop!\n\n💎 **Your Balance:** {emeralds} Emeralds\n\nClick a category below to start browsing.", 
            color=discord.Color.gold()
        )
        embed.add_field(name="🏛️ Village Upgrades", value="Permanent improvements and villager licenses.", inline=True)
        embed.add_field(name="🧪 Marketplace Items", value="Single-use tokens and boosters.", inline=True)

        view = ShopView(self.bot, guild_id, user_id)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))
