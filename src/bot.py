import asyncio
import logging
import logging.handlers
import os
from typing import List

import discord
from discord.ext import commands

from database.db import get_session, init_db
from services.collection_service import CollectionService
from services.economy_service import EconomyService
from services.roll_service import RollService
from services.shop_service import ShopService
from services.trade_service import TradeService
from utils import item_loader, mob_loader, villager_loader


class MyBot(commands.Bot):
    def __init__(self, *args, extentions: List[str], mobs, mobs_by_rarity, villagers, items, db, **kwargs):
        super().__init__(*args, command_prefix="&", help_command=None, **kwargs)
        self.extentions = extentions
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity
        self.villagers = villagers
        self.items = items
        self.db = db

        # Initialize services
        self.collection_service = CollectionService(mobs, mobs_by_rarity)
        self.economy_service = EconomyService(mobs, mobs_by_rarity, items)
        self.roll_service = RollService(mobs, mobs_by_rarity, villagers)
        self.shop_service = ShopService(villagers)
        self.trade_service = TradeService(mobs, villagers, items)
        self.trade_service = TradeService(mobs, villagers, items)

    async def setup_hook(self) -> None:
        for extention in self.extentions:
            await self.load_extension(extention)
            print(f"loaded {extention}")

    async def on_ready(self) -> None:
        print(f"We have logged in as {self.user}")


async def main():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)
    log_path = os.path.join(os.getenv("LOG_DIR", "logs"), "discord.log")

    handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=3,  # Rotate through 3 files
    )
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    mobs, mobs_by_rarity = mob_loader.load_mob_data()
    villagers = villager_loader.load_villagers()
    items = item_loader.load_items()
    init_db()

    extentions = [
        "cogs.rolls",
        "cogs.shop",
        "cogs.collection",
        "cogs.economy",
        "cogs.villagers",
        "cogs.trade",
        "cogs.help",
    ]
    intents = discord.Intents.default()
    intents.message_content = True
    async with MyBot(
        extentions=extentions,
        intents=intents,
        mobs=mobs,
        mobs_by_rarity=mobs_by_rarity,
        villagers=villagers,
        items=items,
        db=get_session,
    ) as bot:
        await bot.start(os.getenv("DISCORD_TOKEN", ""))


asyncio.run(main())
