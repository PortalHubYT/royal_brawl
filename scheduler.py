import asyncio
from os import environ
import txaio
from time import time
from math import floor
import random

txaio.use_asyncio()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Scheduler(ApplicationSession):
    async def onJoin(self, details):

        self.game_tick = 2
        self.stars_number = 60
        self.increment = 0.5
        i = 0
        while True:
            start = time()

            print(
                "["
                + str("*" * (floor(i % self.stars_number))).ljust(self.stars_number),
                end="",
            )

            if i % self.game_tick == 0:
                self.publish("game.tick")

                """self.call(
                    "minecraft.post",
                    f"bossbar set minecraft:peglin value {int((i % 1000) / 10)}",
                )"""
            if i % 0.5 == 0:
                self.publish("game.half_sec")

            i += self.increment
            await asyncio.sleep(self.increment)
            print("] " + str(self.stars_number) + "seconds")


# txaio.use_asyncio()

if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Scheduler)
