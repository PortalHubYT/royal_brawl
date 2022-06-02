import logging

from mcstatus import MinecraftServer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def ping(ip, port):
    server = MinecraftServer(ip, port)
    try:
        status = server.status()
    except:
        raise Exception
    return status.latency