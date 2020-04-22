import time
import redis, socket
import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import aodv_client, json
import multicastSender

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app, resources={r'/*': {'origins': '*'}})
shareMemoryData = redis.StrictRedis(host="::1", port=6379, password="passwd", decode_responses=True)

hostname = socket.gethostname()
ownIPv6 = [socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[0][4][0],
           socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[1][4][0]]

for ip in ownIPv6:
    if ip[:4] == "fe80":
        local_link_ipv6 = str(ip)
    elif ip[:4] == "2001":
        myIPv6 = str(ip)


@app.route('/', methods=['GET'])
def getDefaultPage():
    return "AODV-API..... It's work!!"


@app.route('/getRoutingTable', methods=['GET'])
def getRoutingTable():
    if shareMemoryData.exists("routing_table"):
        routing_table = json.loads(shareMemoryData.get("routing_table"))
        return make_response(jsonify(routing_table))

    return ""


@app.route('/getNodeDetail', methods=['GET'])
def getNodeDetail():
    if shareMemoryData.exists("nodeDetail"):
        routing_table = json.loads(shareMemoryData.get("nodeDetail"))
        return make_response(jsonify(routing_table))

    return ""


@app.route('/getAllNode', methods=['GET'])
def getAllNode():
    shareMemoryData.set("getAllNode", 1)
    multicastSender.sendToMulticast()
    while not shareMemoryData.exists("allNeighbors"):
        pass

    time.sleep(.2)

    shareMemoryData.delete("getAllNode")
    neighbors = json.loads(shareMemoryData.get("allNeighbors"))

    for ip in neighbors:
        # Get socket address
        sockAddr = socket.getaddrinfo(ip, 20009,
                                      family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
            msg = {
                "sentFrom": local_link_ipv6,
                "destAddr": ip,
                "mode": "get"
            }
            ss.sendto(json.dumps(msg).encode(), sockAddr[0][4])
            ss.close()

        time.sleep(.3)

    allNodeDetail = json.loads(shareMemoryData.get("allNodeDetail"))
    allNodeDetail.update({
        str(len(allNodeDetail)):{
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

    multicastSender.sendToMulticast()
    time.sleep(.2)
    shareMemoryData.delete("allNodeDetail")

    return make_response(jsonify(allNodeDetail))


@app.route('/sendMessage', methods=['POST'])
def sendMessage():
    dataLoad = request.json

    dataSend = {
        "route": None,
        "message": dataLoad["message"]
    }

    result = aodv_client.requestDiscoveryPath(IP=dataLoad["toIp"])

    if result["status"] == "wait":

        waitRouting = True
        # Wait for response for routing
        while waitRouting:
            if shareMemoryData.exists("routing_table"):
                routing_table = json.loads(shareMemoryData.get("routing_table"))
                for route in routing_table:
                    if route["destAddr"] == dataLoad["toIp"]:
                        dataSend["route"] = route
                        waitRouting = False
                        break

    elif result["status"] == "haveRoute":
        dataSend["route"] = result["response"]
    elif result["status"] == "error":
        return result["response"]

    aodv_client.sendMessage(recv=dataSend)
    neighbors = json.loads(shareMemoryData.get("neighbors"))
    print(neighbors)

    return "Sending message to node ip " + dataLoad["toIp"]


@app.route('/getMessage', methods=['GET'])
def getMessage():
    if shareMemoryData.exists("message_recv"):
        message_recv = json.loads(shareMemoryData.get("message_recv"))
        return make_response(jsonify(message_recv))

    return "No data"


if __name__ == '__main__':
    app.run(debug=True, host='::', port=8000)
