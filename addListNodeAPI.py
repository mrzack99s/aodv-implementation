import json
import socket

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

hostname = socket.gethostname()
ownIPv6 = socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[0][4][0]


def getListNodeFromJson():
    with open('listNode.json') as json_file:
        return json.load(json_file)


listNode = getListNodeFromJson()


def writeToListNodeJson():
    with open('listNode.json', 'w') as outfile:
        json.dump(listNode, outfile, indent=2)


def sendRequest(neighborIP=None):
    # Get socket address
    sockAddr = socket.getaddrinfo(listNode[neighborIP]["IP"], listNode[neighborIP]["Port"],
                                  family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

    toNodeMsg = {
        "mode": 1,
        "data": listNode
    }

    with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
        ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
        ss.close()


@app.route('/append', methods=['POST'])
def append():
    dataLoad = request.json

    ipAddr = dataLoad['ipAddr']
    nodeName = dataLoad['nodeName']
    port = dataLoad['port']
    intMacAddr = dataLoad['intMacAddr']
    neighbor = dataLoad['neighbor']

    try:
        nextValId = listNode[ipAddr]["ID"]
    except:
        nextValId = len(listNode)

    node = {
        "ID": int(nextValId),
        "Name": nodeName,
        "IP": ipAddr,
        "Port": int(port),
        "intMacAddr": intMacAddr,
        "neighbors": neighbor,
        "RREQ_MESSAGE": [],
        "ROUTING_TABLE": []
    }

    listNode.update({
        ipAddr: node
    })

    # Update own node
    sendRequest(ownIPv6)

    for myNeighbor in listNode[ownIPv6]["neighbors"]:
        sendRequest(myNeighbor)

    return json.dumps(node, indent=2)


@app.route('/getListNode', methods=['GET'])
def getListNode():
    return json.dumps(listNode, indent=2)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
