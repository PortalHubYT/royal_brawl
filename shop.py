import asyncio
import txaio
import pickle
import mcapi as mc
import random
import uuid


txaio.use_asyncio()
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from components.input import sanitize_less_strict, sanitize_very_strict


class ShopItem:
    def __init__(
        self, session, name, price, icon, index, mob_type="zombie", more_nbt=""
    ):

        self.call = session.call
        self.name = name
        self.price = price
        self.icon = icon
        self.index = index
        self.more_nbt = more_nbt
        self.mob_type = mob_type

        self.coords = f"^{6 - index * 2} ^4 ^7"

    async def place(self):
        self.name_nbt = mc.NBT(
            {
                "Tags": ["shop", f"shop{self.index}"],
                "Particle": "block air",
                "CustomNameVisible": 1,
                "Duration": 2400000,
                "CustomName": '{ "text": "' + f"[{self.price}]{self.name}" + '"}',
            }
        )
        cmd = f"execute at funyrom run summon area_effect_cloud {self.coords} {self.name_nbt}"
        print(cmd)
        ret = await self.call("minecraft.post", cmd)

        self.item_nbt = mc.NBT(
            {
                "Marker": 1,
                "Invisible": 1,
                "Marker": 1,
                #  'NoGravity':1,
                "Passengers": [
                    {
                        "id": "Item",
                        "tag": {"Item": {"id": "minecraft:stone", "Count": 1}},
                    }
                ],
            }
        )

        cmd = f"execute at funyrom run summon minecraft:item {self.coords} {self.item_nbt}"

        ret = await self.call("minecraft.post", cmd)

    async def refresh(self):
        cmd = f"execute at funyrom run tp @e[tag=shop{self.index}] {self.coords}"
        await self.call("minecraft.post", cmd)


class Component(ApplicationSession):
    async def refresh_shop(self):
        for s in self.shop:
            await s.refresh()

    async def spawn_shop(self):
        self.shop = [
            ShopItem(self, "sword", 30, "minecraft:iron_sword", 0, mob_type="zombie"),
            ShopItem(
                self,
                "skeleton",
                50,
                "minecraft:iron_sword",
                1,
                "skeleton",
                more_nbt="""HandItems:[{id:"minecraft:bow",Count:1b},{}]""",
            ),
            ShopItem(
                self,
                "diamond sword",
                100,
                "minecraft:diamond_sword",
                2,
                more_nbt="""HandItems:[{id:"minecraft:bow",Count:1b},{}]""",
            ),
            # ShopItem( self, "buy skeleton", 70, "minecraft:diamond_sword", 2),
            # ShopItem( self, "buy armor", 50, "minecraft:diamond_sword", 3)
        ]

        for s in self.shop:
            await s.place()

    async def onJoin(self, details):
        self.call("minecraft.post", "kill @e[tag=shop]")
        await self.spawn_shop()
        self.subscribe(self.message_handler, "chat.message")
        self.subscribe(self.refresh_shop, "game.half_sec")

    async def spawn_mob(self, player_data):
        mob_uid = str(uuid.uuid4())[:8]
        # nbt = get_nbt(player_data['display_name'], "122", mob_uid)
        nbt = get_nbt(
            player_data["display_name"],
            player_data["channel_id"],
            mob_uid,
            player_data["more_nbt"],
        )
        coords = get_random_pos()
        cmd = f"execute in minecraft:brawl run summon {player_data['mob_type']} {coords} {nbt}"
        print(cmd)
        ret = await self.call("minecraft.post", cmd)
        self.publish("shop.spawn", [player_data["channel_id"], mob_uid])

    async def message_handler(self, message):
        message = pickle.loads(message)

        player_data = {
            "display_name": sanitize_very_strict(f'[{message["author"]["name"]}]'),
            "channel_id": message["author"]["channelId"],
            "message": sanitize_less_strict(
                "".join(s for s in message["messageEx"] if isinstance(s, str))
            ),
            "more_nbt": "",
            "mob_type": "zombie",
        }
        print(player_data["display_name"])

        if message["message"].startswith("buy "):
            for shop_item in self.shop:
                if message["message"].startswith(f"buy {shop_item.name}"):
                    player_data["more_nbt"] = shop_item.more_nbt
                    player_data["mob_type"] = shop_item.mob_type

        await self.spawn_mob(player_data)

        # message["author"]["isChatModerator"]:
        # message["author"]["isChatSponsor"]
        # message["author"]["isChatOwner"]
        # message["author"]["isVerified"]

        def stuff(self):
            holding = "diamond_sword"

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


def get_nbt(name, channel_id, mob_uid, more_nbt):

    tag = str(channel_id)
    nbt = mc.NBT(
        {
            "Size": 1,
            "Tags": [tag, mob_uid, "mob"],
            "Passengers": [
                {
                    "id": "minecraft:area_effect_cloud",
                    "Tags": [tag, mob_uid],
                    "Particle": "block air",
                    "Duration": 120000,
                    "Passengers": [
                        {
                            "id": "minecraft:area_effect_cloud",
                            "Particle": "block air",
                            "Tags": [tag, mob_uid],
                            "Duration": 120000,
                            "Passengers": [
                                {
                                    "id": "minecraft:area_effect_cloud",
                                    "Particle": "block air",
                                    "Tags": [tag, "name_holder", mob_uid],
                                    "Duration": 120000,
                                    "CustomNameVisible": 1,
                                    "CustomName": '{ "text": "' + f"{name}" + '"}',
                                }
                            ],
                        }
                    ],
                }
            ],
            "ArmorItems": [{}, {}, {}, {"id": "minecraft:stone_button", "Count": 1}],
            "ActiveEffects": [
                {
                    "Id": 28,
                    "Amplifier": 255,
                    "Duration": 0,
                    "Duration": 999999,
                    "ShowParticles": 0,
                },
            ],
        }
    )
    if len(more_nbt):
        return "{" + more_nbt + "," + str(nbt)[1:]
    else:
        return nbt


WIDTH = 14


def get_random_pos():
    x = random.randrange(-WIDTH, WIDTH)
    y = 130
    z = random.randrange(-WIDTH, WIDTH)
    return f"{x} {y} {z}"


if __name__ == "__main__":
    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "realm1")
    runner.run(Component)
