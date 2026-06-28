import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, section: str | None = None):
        """Show help information for the bot."""
        if section is None:
            embed = discord.Embed(
                title="📘 MobDex - How to Play",
                description=(
                    "Collect Minecraft mobs, earn emeralds, trade duplicates,\n"
                    "and climb the Trading Hall ranks!"
                ),
                color=0x2ECC71,
            )

            embed.add_field(
                name="🎲 Rolling & Claiming",
                value=(
                    f"`{self.bot.command_prefix}roll` - Roll for a random mob (hourly)\n"
                    f"`{self.bot.command_prefix}roll focus` - Focused roll, no Commons (Librarian)\n"
                    f"`{self.bot.command_prefix}roll token <rarity>` - Use a roll token (e.g. uncommon)\n"
                    f"`{self.bot.command_prefix}reroll` - Free reroll (Toolsmith, daily)\n"
                    f"`{self.bot.command_prefix}daily` - Free emeralds + a Common mob\n"
                    f"*Claim via button (once per day) to add to collection*"
                ),
                inline=False,
            )
            embed.add_field(
                name="📚 Collection & Discovery",
                value=(
                    f"`{self.bot.command_prefix}collection` - Browse your mobs\n"
                    f"`{self.bot.command_prefix}missing` - See what you're missing\n"
                    f"`{self.bot.command_prefix}mobs [page|rarity|tag]` - Browse the bestiary\n"
                    f"`{self.bot.command_prefix}mob <id>` - Mob details\n"
                    f"`{self.bot.command_prefix}tags <id>` - Tags and base power\n"
                    f"`{self.bot.command_prefix}leaderboard [emeralds|completion]` - Rankings"
                ),
                inline=False,
            )
            embed.add_field(
                name="💎 Economy & Items",
                value=(
                    f"`{self.bot.command_prefix}balance` - Your emerald wallet\n"
                    f"`{self.bot.command_prefix}inventory` - View tokens and items\n"
                    f"`{self.bot.command_prefix}item <id>` - Item details"
                ),
                inline=False,
            )
            embed.add_field(
                name="🧑‍🌾 Trading & Progression",
                value=(
                    f"`{self.bot.command_prefix}trade` - List tradeable villagers\n"
                    f"`{self.bot.command_prefix}farmer <id> <amt>` - Duplicates → Emeralds\n"
                    f"`{self.bot.command_prefix}cleric <id> <amt>` - Duplicates → Tokens\n"
                    f"`{self.bot.command_prefix}shop` - Village Marketplace\n"
                    f"`{self.bot.command_prefix}villager <id>` - Villager info"
                ),
                inline=False,
            )
            embed.add_field(
                name="🏆 Achievements & Stats",
                value=(
                    f"`{self.bot.command_prefix}achievements` - Unlocked achievements\n"
                    f"`{self.bot.command_prefix}stats` - Lifetime statistics"
                ),
                inline=False,
            )
            embed.add_field(
                name="📖 Learn More",
                value=(
                    f"`{self.bot.command_prefix}help rolling` | `{self.bot.command_prefix}help economy`\n"
                    f"`{self.bot.command_prefix}help collection` | `{self.bot.command_prefix}help trading`\n"
                    f"`{self.bot.command_prefix}help shop` | `{self.bot.command_prefix}help villagers` | `{self.bot.command_prefix}help achievements`"
                ),
                inline=False,
            )

            embed.set_footer(text="Use the & prefix for all commands | Reset Time: 00:00 UTC (Global)")
            await ctx.send(embed=embed)
            return

        section = section.lower()
        prefix = self.bot.command_prefix

        if section == "rolling":
            embed = discord.Embed(
                title="🎲 Rolling & Claiming",
                description="The core gameplay loop: roll for mobs, claim them, and grow your collection.",
                color=0x3498DB,
            )
            embed.add_field(
                name="Standard Roll",
                value=(
                    f"`{prefix}roll` — Roll for a random mob (once per hour).\n"
                    "Rarity weights: Common 55% | Uncommon 25% | Rare 13% | Epic 6% | Legendary 1%.\n"
                    "React with the **Claim** button (once per day) to add it to your collection."
                ),
                inline=False,
            )
            embed.add_field(
                name="Focus Roll",
                value=(
                    f"`{prefix}roll focus` — Requires **Librarian** unlocked (500 emeralds).\n"
                    "Guarantees no Common mobs. Available once per day."
                ),
                inline=False,
            )
            embed.add_field(
                name="Token Roll",
                value=(
                    f"`{prefix}roll token <rarity>` — Consume an Uncommon, Rare, or Epic Roll Token\n"
                    "to guarantee a mob of that exact rarity (e.g. `&roll token uncommon`).\n"
                    "Token rolls bypass the hourly cooldown.\n"
                    "Tokens are obtained via "
                    f"**Cleric trades** (`{prefix}cleric`) or the **shop** (`{prefix}shop`)."
                ),
                inline=False,
            )
            embed.add_field(
                name="Reroll",
                value=(
                    f"`{prefix}reroll` — Requires **Toolsmith** unlocked (250 emeralds).\n"
                    "One free reroll per day. Rerolls bypass the hourly cooldown."
                ),
                inline=False,
            )
            embed.add_field(
                name="Claiming",
                value=(
                    "After rolling, click the **Claim** button to add the mob to your collection.\n"
                    "You can claim **once per day**. Claiming awards emeralds based on rarity:\n"
                    "Common +2 | Uncommon +5 | Rare +10 | Epic +20 | Legendary +50.\n"
                    "Duplicate mobs can still be claimed — they become trade fodder."
                ),
                inline=False,
            )
            await ctx.send(embed=embed)

        elif section == "economy":
            embed = discord.Embed(
                title="💎 Economy & Items",
                description="Emeralds are your main currency. Earn them, spend them, track them.",
                color=0xF1C40F,
            )
            embed.add_field(
                name="Emeralds",
                value=(
                    f"`{prefix}balance` — Check your emerald balance.\n"
                    "Earned by: claiming mobs, daily rewards, and Farmer trades.\n"
                    "Spent at: the Village Marketplace (upgrades and items)."
                ),
                inline=False,
            )
            embed.add_field(
                name="Daily Reward",
                value=(
                    f"`{prefix}daily` — Claim once every 24 hours.\n"
                    "Reward: **2–5 emeralds** + **1 random Common mob**."
                ),
                inline=False,
            )
            embed.add_field(
                name="Inventory",
                value=(
                    f"`{prefix}inventory` — View all items you own (tokens, etc.).\n"
                    f"`{prefix}item <id>` — Detailed info about a specific item.\n\n"
                    "**Roll Tokens:**\n"
                    "• Uncommon Token — guarantees an Uncommon roll\n"
                    "• Rare Token — guarantees a Rare roll\n"
                    "• Epic Token — guarantees an Epic roll"
                ),
                inline=False,
            )
            await ctx.send(embed=embed)

        elif section == "collection":
            embed = discord.Embed(
                title="📚 Collection & Discovery",
                description="Track your progress, browse the bestiary, and compete on leaderboards.",
                color=0x9B59B6,
            )
            embed.add_field(
                name="Your Collection",
                value=(
                    f"`{prefix}collection` — Interactive paginated view of your collected mobs.\n"
                    f"`{prefix}missing` — Shows all mobs you haven't collected, grouped by rarity."
                ),
                inline=False,
            )
            embed.add_field(
                name="Bestiary",
                value=(
                    f"`{prefix}mobs` — All 55+ mobs grouped by rarity (paginated).\n"
                    f"`{prefix}mobs <rarity>` — Filter by Common/Uncommon/Rare/Epic/Legendary.\n"
                    f"`{prefix}mobs <tag>` — Filter your collection by tag (e.g., `{prefix}mobs undead`).\n"
                    f"`{prefix}mob <id>` — Full details, lore, and image."
                ),
                inline=False,
            )
            embed.add_field(
                name="Tags & Power",
                value=(
                    f"`{prefix}tags <id>` — View a mob's tags (overworld, nether, undead, etc.),\n"
                    "base power (used in raids), and traits."
                ),
                inline=False,
            )
            embed.add_field(
                name="Leaderboards",
                value=(
                    f"`{prefix}leaderboard` — Top 5 by both emeralds and completion.\n"
                    f"`{prefix}leaderboard emeralds` — Emerald rankings only.\n"
                    f"`{prefix}leaderboard completion` — Collection completion % rankings."
                ),
                inline=False,
            )
            await ctx.send(embed=embed)

        elif section == "trading":
            embed = discord.Embed(
                title="🧑‍🌾 Trading Duplicate Mobs",
                description=(
                    "Trading uses **duplicate mobs only**.\n"
                    "You always keep **at least one copy** of each mob.\n"
                    "Villagers are unlocked via the **Trading Hall** in the shop."
                ),
                color=0xF1C40F,
            )
            embed.add_field(
                name="Trading Hall Tiers",
                value=(
                    "**Tier 1 — Farmer** (50 💎): Trade dupes for emeralds.\n"
                    "**Tier 2 — Cleric** (100 💎): Convert to roll tokens.\n"
                    "**Tier 3 — Toolsmith** (250 💎): Unlocks reroll.\n"
                    "**Tier 4 — Librarian** (500 💎): Unlocks focus roll.\n\n"
                    "Purchase upgrades with `&shop`."
                ),
                inline=False,
            )
            embed.add_field(
                name="Farmer — Emeralds",
                value=(
                    f"`{prefix}farmer <mob_id> <amount>` or `{prefix}trade farmer <id> <amt>`\n"
                    "Trade duplicate mobs for emeralds. Value depends on mob rarity:\n"
                    "Common 5💎 | Uncommon 20💎 | Rare 50💎 | Epic 100💎 | Legendary 200💎 each."
                ),
                inline=True,
            )
            embed.add_field(
                name="Cleric — Tokens",
                value=(
                    f"`{prefix}cleric <mob_id> <amount>` or `{prefix}trade cleric <id> <amt>`\n"
                    "Convert duplicates into roll tokens. **2 mobs → 1 token**.\n"
                    "Only mobs with a `token_reward` value can be traded (Common→Uncommon token,\n"
                    "Uncommon→Rare token, Rare→Epic token). The amount must be even."
                ),
                inline=True,
            )
            embed.set_footer(text="Both trades require interactive confirm/cancel buttons.")
            await ctx.send(embed=embed)

        elif section == "shop":
            embed = discord.Embed(
                title="🏪 Village Marketplace",
                description=f"Open the shop with `{prefix}shop`. Browse categories with interactive buttons.",
                color=0x9B59B6,
            )
            embed.add_field(
                name="🏛️ Upgrades (Permanent)",
                value=(
                    "• **Farmer's License** — 50 💎 — Unlock Farmer trades\n"
                    "• **Cleric's Ordination** — 100 💎 — Unlock Cleric trades\n"
                    "• **Toolsmith's Apprenticeship** — 250 💎 — Unlock reroll\n"
                    "• **Librarian's Membership** — 500 💎 — Unlock focus roll"
                ),
                inline=False,
            )
            embed.add_field(
                name="🧪 Consumables (Single-Use)",
                value=(
                    "• **Uncommon Roll Token** — 30 💎 — Guarantees Uncommon roll\n"
                    "• **Rare Roll Token** — 75 💎 — Guarantees Rare roll\n"
                    "• **Epic Roll Token** — 150 💎 — Guarantees Epic roll"
                ),
                inline=False,
            )
            embed.set_footer(text="Items are purchased directly from the interactive menu. Confirm with the button.")
            await ctx.send(embed=embed)

        elif section == "villagers":
            embed = discord.Embed(
                title="🧑‍🌾 Your Villagers",
                description=(
                    "Villagers are unlocked through the Trading Hall.\n"
                    "Each one grants new abilities. View details with "
                    f"`{prefix}villager <id>`."
                ),
                color=0xE67E22,
            )
            embed.add_field(
                name="🥕 Farmer — Tier 1 | 50 💎",
                value=(
                    "Unlocks trading duplicate mobs for emeralds.\n"
                    f"Commands: `{prefix}farmer <mob_id> <amount>`"
                ),
                inline=False,
            )
            embed.add_field(
                name="🔮 Cleric — Tier 2 | 100 💎",
                value=(
                    "Unlocks converting duplicate mobs into roll tokens.\n"
                    f"Commands: `{prefix}cleric <mob_id> <amount>`"
                ),
                inline=False,
            )
            embed.add_field(
                name="🔧 Toolsmith — Tier 3 | 250 💎",
                value=(
                    "Unlocks **one free reroll per day**.\n"
                    f"Commands: `{prefix}reroll`"
                ),
                inline=False,
            )
            embed.add_field(
                name="📚 Librarian — Tier 4 | 500 💎",
                value=(
                    "Unlocks **one focus roll per day** (no Common mobs).\n"
                    f"Commands: `{prefix}roll focus`"
                ),
                inline=False,
            )
            await ctx.send(embed=embed)

        elif section == "achievements":
            embed = discord.Embed(
                title="🏆 Achievements & Stats",
                description=(
                    "Track your progress across multiple categories.\n"
                    "Achievements are automatically unlocked as you play."
                ),
                color=0x2ECC71,
            )
            embed.add_field(
                name="Categories",
                value=(
                    "**📚 Collection** — Collect unique mobs, complete rarity sets.\n"
                    "**🗺️ Exploration** — Collect all mobs from each dimension.\n"
                    "**💎 Economy** — Accumulate emeralds.\n"
                    "**🤝 Trading** — Complete trades.\n"
                    "**🎲 Lifetime** — Total rolls, claims, and trades."
                ),
                inline=False,
            )
            embed.add_field(
                name="Commands",
                value=(
                    f"`{prefix}achievements` — View your unlocked achievements.\n"
                    f"`{prefix}stats` — View lifetime stats (collection %, rolls, trades, emeralds, etc.)."
                ),
                inline=False,
            )
            await ctx.send(embed=embed)

        else:
            await ctx.send(
                f"❌ Unknown help section. Available sections:\n"
                f"`{prefix}help`, `{prefix}help rolling`, `{prefix}help economy`, "
                f"`{prefix}help collection`, `{prefix}help trading`, "
                f"`{prefix}help shop`, `{prefix}help villagers`, `{prefix}help achievements`"
            )


async def setup(bot):
    await bot.add_cog(Help(bot))
