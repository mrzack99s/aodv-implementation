import socket, json
import time

import redis

import multicastSender

shareMemoryData = redis.StrictRedis(host="::1", port=6379, password="passwd", decode_responses=True)


def run():
    ## Start UDP Server
    udpServer = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
    udpServer.bind(("::", 20009))

    while True:

        # Receive the data from udp socket
        revMessage = udpServer.recvfrom(4096)[0]

        # If have message
        if revMessage:

            # Conevert message to dictionary
            revMessage = revMessage.decode()
            revMessage = json.loads(revMessage)

            if revMessage["mode"] == "get":

                sockAddr = socket.getaddrinfo(revMessage["sentFrom"], 20009,
                                              family=socket.AF_INET6, proto=socket.IPPROTO_UDP)
                revMessage["mode"] = "reply"
                multicastSender.sendToMulticast()
                time.sleep(.2)
                revMessage.update({
                    "payload": {
                        "nodeDetail":
                            json.loads(shareMemoryData.get("nodeDetail")) if shareMemoryData.exists("nodeDetail")
                            else [],
                        "routingTable":
                            json.loads(shareMemoryData.get("routing_table")) if shareMemoryData.exists("routing_table")
                            else [],
                        "message": json.loads(shareMemoryData.get("message_recv")) if shareMemoryData.exists(
                            "message_recv")
                        else [],
                        "neighbors": json.loads(shareMemoryData.get("neighbors")) if shareMemoryData.exists("neighbors")
                        else []
                    }
                })

                udpServer.sendto(json.dumps(revMessage).encode(), sockAddr[0][4])


            elif revMessage["mode"] == "reply":
                shareMemoryData.set(revMessage["destAddr"] + ":nodeDetail",
                                    json.dumps(revMessage["payload"]))
