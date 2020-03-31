import json
import socket
import threading
import time
from datetime import datetime


def A(routing_table):
    idleTime = {}
    while True:
        if routing_table:
            for route in routing_table:
                toDatetime = datetime.fromtimestamp(route["Lastest_used"])
                diffTime = datetime.now() - toDatetime

                try:
                    idleTime[route["ID"]] = divmod(diffTime.seconds, 60)[0]
                except:
                    idleTime.update({
                        route["ID"]:divmod(diffTime.seconds, 60)[0]
                    })

                if idleTime[route["ID"]] >= route["Lifetime"]:
                    print("Route ID ",route["ID"],"is expire")
                    routing_table.pop(routing_table.index(route))

                # if checkingTime >= routing_table["Lifetime"]:
                #     print("Expire")
            #print(datetime.now().second - toDatetime.second)

        time.sleep(10)
    # while True:
    #     if routing_table:
    #         divv = datetime.fromtimestamp(routing_table["Lastest_used"])
    #         print(divv.second - routing_table["Lifetime"] *60)
    #         time.sleep(5)


class UDPSocketServer(threading.Thread):

    def __init__(self, listNode, nodeName):

        super().__init__()
        self.listNode = listNode
        self.node = self.listNode[nodeName]
        self.rreq_data_packet = None
        self.rrep_data_packet = None
        self.trickFirstRouting = False

    def getNode(self):
        return

    def runExpireTimer(self):
        print("################## Timer at "+self.node["Name"]+" Start ###############")
        self.trickFirstRouting = True
        t = threading.Thread(target=A, args=(self.node["ROUTING_TABLE"],))
        t.setDaemon(True)
        t.start()

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.node["IP"], self.node["Port"]))
        s.listen(5)

        self.runExpireTimer()

        while True:

            # now our endpoint knows about the OTHER endpoint.
            clientsocket, address = s.accept()
            if clientsocket:
                # print("At node " + self.node["Name"])

                revMessage = json.loads(clientsocket.recv(1024).decode())
                if revMessage["isRREQ"] and revMessage["sourceAddr"] != self.node["Name"]:
                    self.aodvRREQ(revMessage)

                elif not revMessage["isRREQ"] and revMessage["sourceAddr"] != self.node["Name"]:
                    self.aodvRREP(revMessage)

                if self.rrep_data_packet is None and revMessage["sourceAddr"] != self.node["Name"]:
                    if self.node["Name"] != self.rreq_data_packet["destAddr"] and self.node["Name"] != \
                            self.rreq_data_packet["sourceAddr"]:
                        # print(self.node["Name"])
                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rreq_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.__sendRequest(neighborName=neighbor, isRREQ=True)

                    elif self.node["Name"] == self.rreq_data_packet["destAddr"]:
                        self.rrep_data_packet = {
                            "sourceAddr": self.rreq_data_packet["destAddr"],
                            "destAddr": self.rreq_data_packet["sourceAddr"],
                            "destSeq": 120,
                            "hopCount": 0,
                            "sentFrom": self.node["Name"],
                            "isRREQ": False,
                            "Lifetime": 1  # if 0 is not expire || unit is min
                        }

                        self.__sendRequest(neighborName=self.node["RREQ_MESSAGE"][-1]["nextHop"], isRREQ=False)


                elif self.rrep_data_packet is not None and revMessage["sourceAddr"] != self.node["Name"]:
                    if self.node["Name"] != self.rrep_data_packet["destAddr"] and self.node["Name"] != \
                            self.rrep_data_packet["sourceAddr"]:
                        # print(self.node["Name"])
                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rrep_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.__sendRequest(neighborName=neighbor, isRREQ=False)
                else:
                    self.rreq_data_packet = revMessage

                    for neighbor in self.node["neighbors"]:
                        if neighbor != self.rreq_data_packet["sourceAddr"]:
                            # print(neighbor)
                            self.__sendRequest(neighborName=neighbor, isRREQ=True)

                clientsocket.close()


    def __sendRequest(self, neighborName=None, isRREQ=True):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ss:
            ss.connect((self.listNode[neighborName]["IP"], self.listNode[neighborName]["Port"]))
            if isRREQ:
                ss.send(json.dumps(self.rreq_data_packet).encode())
            else:
                ss.send(json.dumps(self.rrep_data_packet).encode())
            ss.close()

    def requestDiscoveryPath(self, toNode=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ss:
            ss.connect((self.node["IP"], self.node["Port"]))
            rreq_data_packet = {
                "sourceAddr": self.node["Name"],
                "seqSource": 1,
                "RreqId": self.node["ID"],
                "destAddr": toNode,
                "destSeq": None,
                "hopCount": 0,
                "sentFrom": self.node["Name"],
                "isRREQ": True,
                "RequestTime": {}
            }
            rreq_data_packet["RequestTime"].update({
                self.node["Name"]: datetime.timestamp(datetime.now())
            })
            ss.send(json.dumps(rreq_data_packet).encode())
            ss.close()

    def getRoutingTable(self):
        for reccord in self.node["ROUTING_TABLE"]:
            print("Routing table of node " + self.node["Name"])
            print(reccord, end="\n\n")

    def aodvRREQ(self, revMessage):

        self.rreq_data_packet = revMessage
        self.rreq_data_packet["hopCount"] += 1
        self.rreq_data_packet["RequestTime"].update({
            self.node["Name"]: datetime.timestamp(datetime.now())
        })

        rreq_message = {
            "destAddr": self.rreq_data_packet["sourceAddr"],
            "nextHop": self.rreq_data_packet["sentFrom"],
            "hopCount": self.rreq_data_packet["hopCount"],
            "seq": self.rreq_data_packet["seqSource"]
        }
        self.node["RREQ_MESSAGE"].append(rreq_message)
        self.rreq_data_packet["sentFrom"] = self.node["Name"]

    def aodvRREP(self, revMessage):

        self.rrep_data_packet = revMessage
        self.rrep_data_packet["hopCount"] += 1

        rrep_message = {
            "ID":len(self.node["ROUTING_TABLE"])+1,
            "destAddr": self.rrep_data_packet["sourceAddr"],
            "nextHop": self.rrep_data_packet["sentFrom"],
            "hopCount": self.rrep_data_packet["hopCount"],
            "seq": self.rrep_data_packet["destSeq"]
        }

        RREP_Time = datetime.now()
        duration = RREP_Time - datetime.fromtimestamp(
            self.rreq_data_packet["RequestTime"][self.node["Name"]]
        )
        Latency_Time = duration.microseconds * (10 ** -3)
        rrep_message.update({
            "LatencyTime": str(Latency_Time) + " ms",
            "Lifetime": self.rrep_data_packet["Lifetime"],
            "Lastest_used": datetime.timestamp(datetime.now())
        })

        self.node["ROUTING_TABLE"].append(rrep_message)
        self.rrep_data_packet["sentFrom"] = self.node["Name"]


