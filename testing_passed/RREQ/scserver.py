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

                self.rreq_data_packet = json.loads(clientsocket.recv(1024).decode())
                self.rreq_data_packet["hopCount"] += 1

                rreq_message = {
                    "destAddr": self.rreq_data_packet["sourceAddr"],
                    "nextHop": self.rreq_data_packet["sentFrom"],
                    "hopCount": self.rreq_data_packet["hopCount"],
                    "seq": self.rreq_data_packet["seqSource"]
                }

                self.node["rev"].append(rreq_message)
                self.rreq_data_packet["sentFrom"] = self.node["Name"]


                if self.node["Name"] != self.rreq_data_packet["destAddr"] and self.node["Name"] != \
                        self.rreq_data_packet["sourceAddr"]:
                    print(self.node["Name"])
                    for neighbor in self.node["neighbors"]:
                        if neighbor != self.rreq_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.sendRequest(neighborName=neighbor, isRREQ=True)


                clientsocket.close()

    def sendRequest(self, neighborName=None, isRREQ=True):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ss:
            ss.connect((self.listNode[neighborName]["IP"], self.listNode[neighborName]["Port"]))
            ss.send(json.dumps(self.rreq_data_packet).encode())
            ss.close()
