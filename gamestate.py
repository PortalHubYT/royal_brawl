from ast import Str
import asyncio
from dis import dis
import txaio

txaio.use_asyncio()
import os
import pickle
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import json


class GameState(ApplicationSession):
    async def onJoin(self, details):

        self.coins = {}
        self.alives = {}
        self.game_tick = 0
        self.to_save = ["alives", "coins"]

        for store_name in self.to_save:
            print(f"o-> Loading {store_name} from file")
            try:
                ret = self.load_from_file("db", store_name)
                print(ret)
                setattr(self, store_name, ret)
            except Exception or json.decoder.JSONDecodeError as e:
                if isinstance(e, json.decoder.JSONDecodeError):
                    print(f"o-> The file {store_name} is empty")
                else:
                    print(f"o-> Probably the files don't exist yet")

        async def add_alive(player_info: tuple) -> dict:
            channel_id = player_info[0]
            mob_uid = player_info[1]

            print(f"o-> Returning: Spawned {mob_uid}")
            self.alives[mob_uid] = channel_id

            if channel_id not in self.coins:
                self.coins[channel_id] = 0

            await self.call("gamestate.alive.add", channel_id)
            return self.alives

        async def remove_alive(mob_uid: str) -> dict:

            print(f"o-> Returning: Killing {mob_uid}")

            display_name = await get_display_name(mob_uid)

            msg = f"{display_name} has died and received 10 coins ({self.coins[self.alives[mob_uid]]}"
            self.call("minecraft.post", f'title funyrom actionbar "{msg}"')

            if mob_uid in self.alives:
                self.alives.pop(mob_uid)
                print(f"o-> Returning: Killed {mob_uid}")
            else:
                print(f"o-> Returning: {mob_uid} is not alive")

            self.call("minecraft.post", f"kill @e[tag={mob_uid}]")
            return self.alives

        def get_alives() -> list:
            return self.alives

        def set_coin(channel_id: str, coin: int) -> int:
            self.coins[channel_id] = coin
            print(
                f"o-> Returning: ({channel_id[:8]}) coin set to {self.coins[channel_id]}"
            )
            return self.coins[channel_id]

        def get_coin(channel_id: str) -> bool:
            return self.coins[channel_id]

        def add_coin(channel_id: str, coin: int) -> int:

            self.coins[channel_id] += coin
            print(
                f"o-> Returning: ({channel_id[:8]}) coin set to {self.coins[channel_id]}"
            )
            return self.coins[channel_id]

        def remove_coin(channel_id: str, coin: int) -> int:
            self.coins[channel_id] -= coin
            print(
                f"o-> Returning: ({channel_id[:8]}) coin set to {self.coins[channel_id]}"
            )
            return self.coins[channel_id]

        async def check_alive():

            to_kill = []
            self.game_tick += 1

            copy_of = self.alives.copy()
            for id in copy_of:
                cmd = f"execute if entity @e[tag={id},tag=mob]"
                result = await self.call("minecraft.post", cmd)
                if "Test failed" in result:
                    await self.call("gamestate.death", self.alives[id])
                    await remove_alive(id)

            if self.game_tick % 5 == 0:
                print(f"o-({len(copy_of)})-> Currently alives: {[x for x in copy_of]}")
                display = []
                for alive in copy_of:
                    display.append({copy_of[alive][:8]: self.coins[copy_of[alive]]})
                print(f"o-({len(display)})-> Currently coins: {display}")
                print(f"o-> To remove from alives: {to_kill}")

        async def get_display_name(mob_uid: str) -> str:
            cmd = f"data get entity @e[tag={mob_uid},tag=name_holder,limit=1]"
            ret = await self.call("minecraft.post", cmd)
            display_name = ret.split("CustomName: '")[1].split("',")[0]
            print(display_name)
            if "extra" in display_name:
                display_name = display_name.split("],")[1]
            print(display_name)
            display_name = dict(display_name)
            return display_name

        await self.register(get_display_name, "gamestate.get_display_name")
        await self.subscribe(add_alive, "shop.spawn")  # (channel_id, mob_uid)
        await self.register(remove_alive, "gamestate.alive.remove")  # (channel_id)
        await self.register(get_alives, "gamestate.alive.get")  # ()

        await self.register(set_coin, "gamestate.coin.set")  # (channel_id, int)
        await self.register(get_coin, "gamestate.coin.get")  # (channel)
        await self.register(add_coin, "gamestate.coin.add")  # (channel_id, int)
        await self.register(remove_coin, "gamestate.coin.remove")  # (channel_id, int)

        await self.subscribe(check_alive, "game.tick")  # ()

        async def send_default_cmds(self):
            default_cmds = [
                f"gamerule mobGriefing false",
                f"region flag -w world __global__ tnt deny",
                f"whitelist on",
                f"time set noon",
                f"gamerule sendCommandFeedback false",
                f'title @e[type=player] title "Restarting..."',
                f'title @e[type=player] subtitle "Type anything to join the game"',
                f"gamerule doDaylightCycle false",
                f"gamerule doWeatherCycle false"
                # f'bossbar add minecraft:peglin "default"',
                # f'bossbar set minecraft:peglin name "High score: {0}"',
                # f"bossbar set minecraft:peglin visible true",
                # f"bossbar set minecraft:peglin players @a",
                # f"bossbar set minecraft:peglin style progress",
            ]

            for cmd in default_cmds:
                await self.call("minecraft.post", cmd)

        await send_default_cmds(self)

        await self.register(send_default_cmds, "gamestate.default.cmds")  # ()

    def ensure_file(self, dir, store_name):
        filepath = f"{dir}/{store_name}.json"
        if not os.path.exists(f"{dir}"):
            os.mkdir(dir)
        if not os.path.exists(filepath):
            open(filepath, "w+").close()

        print(f"o-> Ensuring {store_name} file exists")

    def load_from_file(self, dir, store_name):

        self.ensure_file(dir, store_name)
        with open(f"{dir}/{store_name}.json", "r") as f:
            try:
                data = json.load(f)
            except EOFError:
                print("Empty store")
                data = None

        print(f"o-> Loading {store_name} from file")
        return data

    def store_to_file(self, store_name):

        data = getattr(self, store_name)
        with open(f"db/{store_name}.json", "w", encoding="utf8") as f:
            json.dump(data, f)

        print(f"o-> Saving {store_name} to file")

    async def onDisconnect(self):
        for store_name in self.to_save:
            print(f"o-> Saving {store_name} to file")
            self.store_to_file(store_name)
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(GameState)
