from __future__ import print_function

import json
import socket
import subprocess
from datetime import datetime

import redis

from mcastsocket import mcastsocket
import select

shareMemoryData = redis.StrictRedis(host="::1", port=6379, password="passwd", decode_responses=True)
interfaceName = subprocess.check_output("iw dev | awk '$1==\"Interface\"{print $2}'", shell=True).decode().replace("\n","")
hostname = socket.gethostname()
ownIPv6 = [socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[0][4][0],
           socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[1][4][0]]

for ip in ownIPv6:
    if ip[:4] == "fe80":
        local_link_ipv6 = str(ip)
    elif ip[:4] == "2001":
        myIPv6 = str(ip)


def Revc():
    # bind/listen on all interfaces, send with a TTL of 5
    group, port = 'ff02::1', 20002
    interface = "wlan0"

    listen_addr = socket.getaddrinfo(
        '::',
        port,
        socket.AF_INET6,
        socket.SOCK_DGRAM
    )[0][-1]
    sock = mcastsocket.create_socket(
        listen_addr,
        TTL=1,
        family=socket.AF_INET6
    )

    mcastsocket.join_group(
        sock,
        group=group,
        iface=interface,
    )

    try:
        print('Listening for traffic on %s:%s on ip %s' % (group, port, interface))
        while True:
            readable, _, _ = select.select([sock], [], [], .5)

            if readable:

                message, address = sock.recvfrom(65000)
                message = json.loads(message.decode())

                if address[0] != local_link_ipv6:
                    sockAddr = socket.getaddrinfo(address[0], 20003,
                                                  family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

                    with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
                        msg = {
                            "replyFrom": local_link_ipv6,
                            "requestTime": message["requestTime"]
                        }
                        ss.sendto(json.dumps(msg).encode(), sockAddr[0][-1])
                        ss.close()

    finally:
        mcastsocket.leave_group(
            sock,
            group=group,
            iface=interface,
        )


def RecvReply():

    listNeighbors = {
        "latestUpdate": None,
        "neighbors": {}
    }
    udpServer = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
    udpServer.bind(("::", 20003))

    while True:
        # Receive the data from udp socket
        revMessage = udpServer.recvfrom(2048)[0]
        revMessage = json.loads(revMessage.decode())

        if revMessage:

            nowTime = datetime.now()
            listNeighbors["latestUpdate"] = datetime.timestamp(datetime.now()) if listNeighbors["latestUpdate"] is\
                                                                                  None else listNeighbors["latestUpdate"]
            durationListNeighbors = nowTime - datetime.fromtimestamp(
                listNeighbors["latestUpdate"]
            )

            if durationListNeighbors.seconds > 60:
                listNeighbors["neighbors"].clear()

            duration = nowTime - datetime.fromtimestamp(
                revMessage["requestTime"]
            )
            Latency_Time = duration.microseconds * (10 ** -3)

            if Latency_Time < 100:

                node = {
                    "IP": revMessage["replyFrom"],
                    "Latency": Latency_Time
                }

                listNeighbors["neighbors"].update({
                    revMessage["replyFrom"]:node
                })

                listNeighbors["latestUpdate"] = datetime.timestamp(datetime.now())

            shareMemoryData.set("neighbors",json.dumps(listNeighbors["neighbors"]))

