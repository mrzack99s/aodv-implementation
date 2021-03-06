import json
import socket
import subprocess

import redis
import threading
import time
from datetime import datetime

import multicastSender
import neighborDiscovery

globalPort = 20001
shareMemoryData = redis.StrictRedis(host="::1", port=6379, password="passwd", decode_responses=True)

def TimeChecker():
    idleTime = {}

    while True:

        if shareMemoryData.exists("routing_table"):

            routing_table = json.loads(shareMemoryData.get("routing_table"))
            for route in routing_table:

                toDatetime = datetime.fromtimestamp(route["Lastest_used"])
                diffTime = datetime.now() - toDatetime

                try:
                    idleTime[route["ID"]] = divmod(diffTime.seconds, 60)[0]
                except:
                    idleTime.update({
                        route["ID"]: divmod(diffTime.seconds, 60)[0]
                    })

                if (idleTime[route["ID"]] >= route["Lifetime"]) and route["Lifetime"] != 0:
                    command = "ip -6 route del " + route["destAddr"]
                    subprocess.call(command, shell=True)

                    routing_table.pop(routing_table.index(route))

                    shareMemoryData.set("routing_table", json.dumps(routing_table))

        time.sleep(1)


class AODVService(threading.Thread):
    bufferSize = 2048

    def __init__(self):
        super().__init__()

        hostname = socket.gethostname()
        ownIPv6 = [socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[0][4][0],
                   socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[1][4][0]]

        self.node = {
            "IP": None,
            "link_local_IPv6": None,
            "Port": globalPort,
        }

        for ip in ownIPv6:
            if ip[:4] == "fe80":
                self.node["link_local_IPv6"] = str(ip)
            elif ip[:4] == "2001":
                self.node["IP"] = str(ip)

        self.RREQ_MESSAGE = []
        self.rreq_data_packet = None
        self.rrep_data_packet = None
        self.sequence = {}

        shareMemoryData.flushdb()
        shareMemoryData.set("nodeDetail", json.dumps(self.node))

    def getNode(self):
        return

    def runExpireTimer(self):
        print("################## AODV Service start at " + self.node["IP"] + " ###############")
        t = threading.Thread(target=TimeChecker)
        t.setDaemon(True)
        t.start()

    def run(self):

        ## Start UDP Server
        udpServer = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
        udpServer.bind(("::", self.node["Port"]))

        ## Call to Expiretimer tread
        self.runExpireTimer()

        while True:

            # Receive the data from udp socket
            revMessage = udpServer.recvfrom(AODVService.bufferSize)[0]

            # If have message
            if revMessage:

                # Conevert message to dictionary
                revMessage = revMessage.decode()
                revMessage = json.loads(revMessage)

                if revMessage["mode"] == 0:

                    # Is RREQ and not source node
                    if revMessage["data"]["isRREQ"] and revMessage["data"]["sourceAddr"]["IP"] != self.node["IP"]:

                        self.aodvRREQ(revMessage["data"])

                    # Is RREP and not source node ( Destination from source )
                    elif not revMessage["data"]["isRREQ"] and revMessage["data"]["sourceAddr"] != self.node["IP"]:

                        self.aodvRREP(revMessage["data"])

                    # RREQ
                    if self.rrep_data_packet is None and revMessage["data"]["sourceAddr"]["IP"] != self.node["IP"]:

                        neighbors = json.loads(shareMemoryData.get("neighbors"))

                        # From source boardcast to neighbor
                        if self.node["IP"] != self.rreq_data_packet["destAddr"] and self.node["IP"] != \
                                self.rreq_data_packet["sourceAddr"]["IP"] and revMessage["data"]["sentFrom"][
                            "link_local_IPv6"] not in neighbors:
                            # print(self.node["Name"])
                            for neighbor in neighbors:
                                if neighbors[neighbor]["IP"] != self.rreq_data_packet["sourceAddr"]["link_local_IPv6"]:
                                    # print(neighbor)
                                    self.__sendRequest(neighborIP=neighbor, isRREQ=True)

                        # At Destination node is end of RREQ packet and set to RREP packet then sent back from next hop
                        # of RREQ message
                        elif self.node["IP"] == self.rreq_data_packet["destAddr"]:

                            self.rrep_data_packet = {
                                "sourceAddr": self.rreq_data_packet["destAddr"],
                                "destAddr": self.rreq_data_packet["sourceAddr"],
                                "destSeq": self.rreq_data_packet["destSeq"],
                                "hopCount": 0,
                                "sentFrom": {
                                    "IP": self.node["IP"],
                                    "link_local_IPv6": self.node["link_local_IPv6"],
                                },
                                "isRREQ": False,
                                "Lifetime": 2  # if 0 is not expire || unit is min
                            }

                            for message in self.RREQ_MESSAGE:
                                if self.rrep_data_packet["destSeq"] == message["destSeq"]:
                                    self.__sendRequest(neighborIP=message["nextHop"], isRREQ=False)
                                    self.RREQ_MESSAGE.remove(message)

                            self.rrep_data_packet = None


                    # RREP
                    elif self.rrep_data_packet is not None and revMessage["data"]["sourceAddr"] != self.node["IP"]:

                        # RREP packet then sent back from next hop of RREQ message
                        if self.node["IP"] != self.rrep_data_packet["destAddr"] and self.node["IP"] != \
                                self.rrep_data_packet["sourceAddr"]:
                            # print(self.node["Name"])
                            for message in self.RREQ_MESSAGE:
                                if self.rrep_data_packet["destSeq"] == message["destSeq"]:
                                    self.__sendRequest(neighborIP=message["nextHop"], isRREQ=False)
                                    self.RREQ_MESSAGE.remove(message)

                        self.rrep_data_packet = None


                    # If from requestDiscoveryPath
                    else:

                        self.rreq_data_packet = revMessage["data"]

                        self.conditionCheckForNeighborDiscovery(destAddr=revMessage["data"]["destAddr"])
                        neighbors = json.loads(shareMemoryData.get("neighbors"))

                        for neighbor in neighbors:
                            if neighbors[neighbor]["IP"] != self.rreq_data_packet["sourceAddr"]["link_local_IPv6"]:
                                # print(neighbor)
                                self.__sendRequest(neighborIP=neighbor, isRREQ=True)

                # Send message
                elif revMessage["mode"] == 1:
                    if self.node["IP"] != revMessage["data"]["destAddr"]:

                        if shareMemoryData.exists("routing_table"):
                            routing_table = json.loads(shareMemoryData.get("routing_table"))
                            for route in routing_table:
                                if route["destAddr"] == revMessage["data"]["destAddr"]:
                                    self.__sendData(IP=route["nextHop"], data=revMessage)
                                    routing_table[routing_table.index(route)]["Lastest_used"] = datetime.timestamp(
                                        datetime.now())
                                    shareMemoryData.set("routing_table", json.dumps(routing_table))
                                    break


                    else:
                        message_recv = revMessage["data"]
                        shareMemoryData.set("message_recv", json.dumps(message_recv))


    def conditionCheckForNeighborDiscovery(self, destAddr=None):

        routingTable = []

        if shareMemoryData.exists("routing_table"):
            routingTable = json.loads(shareMemoryData.get("routing_table"))

        haveRoute = False
        for route in routingTable:
            if route["destAddr"] == destAddr:
                haveRoute = True
                break

        if not haveRoute:
            shareMemoryData.delete("neighbors")
            self.neighborDiscovery()

        while not shareMemoryData.exists("neighbors"):
            pass

        return True

    def neighborDiscovery(self):
        multicastSender.sendToMulticast()

    def __sendData(self, IP=None, data=None):

        # Get socket address
        sockAddr = socket.getaddrinfo(IP, globalPort,
                                      family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
            ss.sendto(json.dumps(data).encode(), sockAddr[0][4])
            ss.close()

    def __sendRequest(self, neighborIP=None, isRREQ=True):

        # Get socket address
        sockAddr = socket.getaddrinfo(neighborIP, globalPort,
                                      family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
            toNodeMsg = {
                "mode": 0,
                "data": self.rreq_data_packet if isRREQ else self.rrep_data_packet
            }

            ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
            ss.close()

    def requestDiscoveryPath(self, toNodeIP=None):

        if toNodeIP[:9] != "2001:3234":
            return {
                "status": "error",
                "response": "Invalid site prefix"
            }

        if shareMemoryData.exists("routing_table"):
            routing_table = json.loads(shareMemoryData.get("routing_table"))
            for route in routing_table:
                if toNodeIP == route["destAddr"]:
                    return {
                        "status": "haveRoute",
                        "response": route
                    }

        while not self.conditionCheckForNeighborDiscovery(destAddr=toNodeIP):
            pass

        sockAddr = socket.getaddrinfo(self.node["link_local_IPv6"], self.node["Port"], family=socket.AF_INET6,
                                      proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:

            try:
                seqNumber = self.sequence[toNodeIP]
                self.sequence[toNodeIP] += 1
            except:
                seqNumber = 1
                self.sequence.update({
                    toNodeIP: seqNumber
                })

            rreq_id_generate = self.node["IP"][-9:] + "_" + str(seqNumber)
            destSeqGen = toNodeIP[-4:] + "_" + str(121 - seqNumber)
            sourceSeqGen = self.node["IP"][-4:] + "_" + str(seqNumber)
            rreq_data_packet = {
                "sourceAddr": {
                    "IP": self.node["IP"],
                    "link_local_IPv6": self.node["link_local_IPv6"],
                },
                "seqSource": sourceSeqGen,
                "RreqId": rreq_id_generate,
                "destAddr": toNodeIP,
                "destSeq": destSeqGen,
                "hopCount": 0,
                "sentFrom": {
                    "IP": self.node["IP"],
                    "link_local_IPv6": self.node["link_local_IPv6"],
                },
                "isRREQ": True,
                "RequestTime": {}
            }

            rreq_data_packet["RequestTime"].update({
                self.node["IP"]: datetime.timestamp(datetime.now())
            })

            toNodeMsg = {
                "mode": 0,
                "data": rreq_data_packet
            }

            self.rreq_data_packet = None
            ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
            ss.close()

            return {
                "status": "wait",
                "response": None
            }

    def aodvRREQ(self, revMessage):

        self.conditionCheckForNeighborDiscovery(destAddr=revMessage["destAddr"])
        neighbors = json.loads(shareMemoryData.get("neighbors"))
        if revMessage["sentFrom"]["link_local_IPv6"] in neighbors:
            pass

        self.rreq_data_packet = revMessage
        self.rreq_data_packet["hopCount"] += 1
        self.rreq_data_packet["RequestTime"].update({
            self.node["IP"]: datetime.timestamp(datetime.now())
        })

        rreq_message = {
            "destAddr": self.rreq_data_packet["sourceAddr"],
            "nextHop": self.rreq_data_packet["sentFrom"]["link_local_IPv6"],
            "hopCount": self.rreq_data_packet["hopCount"],
            "srcSeq": self.rreq_data_packet["seqSource"],
            "destSeq": self.rreq_data_packet["destSeq"],
        }
        self.RREQ_MESSAGE.append(rreq_message)
        self.rreq_data_packet["sentFrom"] = {
            "IP": self.node["IP"],
            "link_local_IPv6": self.node["link_local_IPv6"],
        }

    def aodvRREP(self, revMessage):

        routingTable = []
        if shareMemoryData.exists("routing_table"):
            routingTable = json.loads(shareMemoryData.get("routing_table"))

        self.rrep_data_packet = revMessage
        self.rrep_data_packet["hopCount"] += 1

        rrep_message = {
            "ID": len(routingTable) + 1,
            "destAddr": self.rrep_data_packet["sourceAddr"],
            "nextHop": self.rrep_data_packet["sentFrom"]["IP"],
            "hopCount": self.rrep_data_packet["hopCount"],
            "destSeq": self.rrep_data_packet["destSeq"]
        }

        RREP_Time = datetime.now()
        duration = RREP_Time - datetime.fromtimestamp(
            self.rreq_data_packet["RequestTime"][self.node["IP"]]
        )
        Latency_Time = duration.microseconds * (10 ** -3)
        rrep_message.update({
            "LatencyTime": str(Latency_Time) + " ms",
            "Lifetime": self.rrep_data_packet["Lifetime"],
            "Lastest_used": datetime.timestamp(datetime.now())
        })

        foundInRoutingTable = False
        for route in routingTable:
            if route["destAddr"] == rrep_message["destAddr"]:
                foundInRoutingTable = True
                break

        if not foundInRoutingTable:
            routingTable.append(rrep_message)
            shareMemoryData.set("routing_table", json.dumps(routingTable))

            command = "ip -6 route add " + rrep_message[
                "destAddr"] + " dev " + neighborDiscovery.interfaceName + " via " + \
                      rrep_message["nextHop"] \
                      + " proto static metric 1024 pref medium"
            subprocess.call(command, shell=True)

        self.rrep_data_packet["sentFrom"] = {
            "IP": self.node["IP"],
            "link_local_IPv6": self.node["link_local_IPv6"],
        }

    def sendMessage(self, recv=None):

        routeTable = recv["route"]
        sockAddr = socket.getaddrinfo(routeTable["nextHop"], globalPort,
                                      family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

        routingTable = []
        if shareMemoryData.exists("routing_table"):
            routingTable = json.loads(shareMemoryData.get("routing_table"))

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:

            toNodeMsg = {
                "mode": 1,
                "data": {
                    "sentFrom": self.node["IP"],
                    "destAddr": routeTable["destAddr"],
                    "message": recv["message"],
                    "timestamp": datetime.timestamp(datetime.now())
                }
            }

            ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
            ss.close()

        for route in routingTable:
            if route["destAddr"] == routeTable["destAddr"]:
                routingTable[routingTable.index(route)]["Lastest_used"] = datetime.timestamp(datetime.now())
                shareMemoryData.set("routing_table", json.dumps(routingTable))
                break
