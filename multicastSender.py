from __future__ import print_function

import json
from datetime import datetime
import socket

from mcastsocket import mcastsocket
import select


def sendToMulticast():
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
        TTL=2,
        family=socket.AF_INET6,
        loop=True,
    )
    mcastsocket.join_group(
        sock,
        group=group,
        iface=interface,
    )
    try:
        _, writable, _ = select.select([], [sock], [], .5)
        if writable:
            msg = {
                "requestTime": datetime.timestamp(datetime.now())
            }
            sock.sendto(json.dumps(msg).encode() , (group, port))
    finally:
        mcastsocket.leave_group(
            sock,
            group=group,
            iface=interface,
        )


