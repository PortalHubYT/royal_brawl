import asyncio
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import gamestate
import mcapi as mc


class Component(ApplicationSession):
    async def onJoin(self, details):
        async def on_spawn(channel_id: str) -> int:
            """Returns the number of coins of the player"""
            coins = await self.call("gamestate.coin.add", channel_id, 10)
            print(f"o-> Added 10 coins to {channel_id[:8]} on spawn")
            return coins

        async def on_death(channel_id: str):
            """Returns the number of coins of the player"""
            coins = await self.call("gamestate.coin.add", channel_id, 10)
            print(f"o-> Added 10 coins to {channel_id[:8]} on death")
            return coins

        async def update_name():
            alives = await self.call("gamestate.alive.get")

            for mob_uid in alives:
                display_name = await self.call("gamestate.get_display_name", mob_uid)
                if display_name is None:
                    continue
                coins = await self.call("gamestate.coin.get", alives[mob_uid])
                nbt = mc.NBT(
                    {
                        "CustomName": '[{"text":"'
                        + display_name
                        + '"},{"text":" ["},{"text":"'
                        + str(coins)
                        + '","color":"gold","bold":true},{"text":"]"}]'
                    }
                )
                cmd = (
                    f"data merge entity @e[tag={mob_uid},tag=name_holder,limit=1] {nbt}"
                )
                await self.call("minecraft.post", cmd)
                print(f"o-> Updated name of {mob_uid}")

        await self.subscribe(update_name, "game.tick")
        await self.subscribe(update_name, "shop.spawn")
        await self.register(on_spawn, "gamestate.alive.add")
        await self.register(on_death, "gamestate.death")

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


class Coins:
    def __init__(self, crossbar):
        self.crossbar = crossbar

    def add_coin(self, channel_id: str, amount: int):
        self.crossbar.call("gamestate.")


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
