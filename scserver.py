import json
import socket
import threading
from datetime import datetime


class UDPSocketServer(threading.Thread):
    global Rrep_time

    def __init__(self, listNode, nodeName):
        super().__init__()
        self.listNode = listNode
        self.node = self.listNode[nodeName]
        self.HEADERSIZE = 10
        self.rreq_data_packet = None
        self.rrep_data_packet = None

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.node["IP"], self.node["Port"]))
        s.listen(5)

        while True:
            # now our endpoint knows about the OTHER endpoint.
            clientsocket, address = s.accept()
            if clientsocket:
                print("At node " + self.node["Name"])

                revMessage = json.loads(clientsocket.recv(1024).decode())
                if revMessage["isRREQ"]:
                    self.rreq_data_packet = revMessage
                    self.rreq_data_packet["hopCount"] += 1
                    rreq_message = {
                        "destAddr": self.rreq_data_packet["sourceAddr"],
                        "nextHop": self.rreq_data_packet["sentFrom"],
                        "hopCount": self.rreq_data_packet["hopCount"],
                        "seq": self.rreq_data_packet["seqSource"]
                    }
                    self.node["RREQ_MESSAGE"].append(rreq_message)
                    self.rreq_data_packet["sentFrom"] = self.node["Name"]

                else:
                    self.rrep_data_packet = revMessage
                    self.rrep_data_packet["hopCount"] += 1

                    rrep_message = {
                        "destAddr": self.rrep_data_packet["sourceAddr"],
                        "nextHop": self.rrep_data_packet["sentFrom"],
                        "hopCount": self.rrep_data_packet["hopCount"],
                        "seq": self.rrep_data_packet["destSeq"]
                    }
                    self.node["RREP_MESSAGE"].append(rrep_message)
                    self.rrep_data_packet["sentFrom"] = self.node["Name"]

                if self.rrep_data_packet is None:
                    if self.node["Name"] != self.rreq_data_packet["destAddr"] and self.node["Name"] != self.rreq_data_packet["sourceAddr"]:
                        print(self.node["Name"])
                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rreq_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.sendRequest(neighborName=neighbor, isRREQ=True)

                    elif self.node["Name"] == self.rreq_data_packet["destAddr"]:
                        self.rrep_data_packet = {
                            "sourceAddr": self.rreq_data_packet["destAddr"],
                            "destAddr": self.rreq_data_packet["sourceAddr"],
                            "destSeq": 120,
                            "hopCount": 0,
                            "sentFrom": self.node["Name"],
                            "isRREQ": False
                        }
                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rrep_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.sendRequest(neighborName=neighbor, isRREQ=False)

                else:
                    if self.node["Name"] != self.rrep_data_packet["destAddr"] and self.node["Name"] != self.rrep_data_packet["sourceAddr"]:
                        print(self.node["Name"])
                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rrep_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.sendRequest(neighborName=neighbor, isRREQ=False)



                clientsocket.close()

    def sendRequest(self, neighborName=None, isRREQ=True):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ss:
            ss.connect((self.listNode[neighborName]["IP"], self.listNode[neighborName]["Port"]))
            if isRREQ:
                ss.send(json.dumps(self.rreq_data_packet).encode())
            else:
                ss.send(json.dumps(self.rrep_data_packet).encode())
            ss.close()
