import asyncio
from audioop import mul
import txaio

txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import gamestate
import mcapi as mc
from components.input import multi_split
from math import sin, cos, radians


class Component(ApplicationSession):
    async def onJoin(self, details):
        self.game_tick = 0

        self.camera_angle = 0
        self.origin_angle = 180
        self.pitch = 35

        self.speed = 0.0000000000001
        self.camera = ""
        self.camera = "funyrom"

        default_cmd = [
            "execute in brawl run kill @e[tag=stand]",
            # Sets the command block that spawns a stand if there isn't one
            'execute in brawl run setblock 0 97 0 minecraft:repeating_command_block[conditional=false,facing=up]{auto:1b,powered:0b,LastExecution:148391L,SuccessCount:0,UpdateLastExecution:1b,conditionMet:1b,CustomName:\'{"text":"@"}\',Command:"execute unless entity @e[tag=stand] run summon minecraft:armor_stand ~ ~1 ~ {Tags:[\'stand\'],Invulnerable:1b}",TrackOutput:0b} destroy',
            # Sets the command block that make the stand spin on itself
            f'execute in brawl run setblock 1 98 0 minecraft:repeating_command_block[conditional=false,facing=up]{{auto:1b,powered:0b,LastExecution:140445L,SuccessCount:1,UpdateLastExecution:1b,conditionMet:1b,CustomName:\'{{"text":"@"}}\',Command:"execute as @e[tag=stand] at @s run tp @s ~ ~ ~ ~{self.speed} ~",TrackOutput:0b}} destroy',
            # Sets the command block that makes the camera spin around the stand
            f'execute in brawl run setblock 1 99 0 minecraft:repeating_command_block[conditional=false,facing=up]{{auto:1b,powered:0b,LastExecution:140693L,SuccessCount:1,UpdateLastExecution:1b,conditionMet:1b,CustomName:\'{{"text":"@"}}\',Command:"execute in brawl as {self.camera} at @e[tag=stand] run tp {self.camera} ^1 ^20 ^35 ~180 ~38",TrackOutput:0b}} destroy',
        ]

        for cmd in default_cmd:
            ret = await self.call("minecraft.post", cmd)
            print(ret)

    async def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
