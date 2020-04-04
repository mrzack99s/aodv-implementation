import json

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})


def getListNodeFromJson():
    with open('listNode.json') as json_file:
        return json.load(json_file)


listNode = getListNodeFromJson()


def writeToListNodeJson():
    with open('listNode.json', 'w') as outfile:
        json.dump(listNode, outfile, indent=2)


@app.route('/append', methods=['POST'])
def append():

    dataLoad = request.json

    ipAddr = dataLoad['ipAddr']
    nodeName = dataLoad['nodeName']
    port = dataLoad['port']
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
        "neighbors": neighbor,
        "RREQ_MESSAGE": [],
        "ROUTING_TABLE": []
    }

    listNode.update({
        ipAddr:node
    })

    writeToListNodeJson()
    return json.dumps(node,indent=2)

@app.route('/getListNode', methods=['GET'])
def getListNode():
    return json.dumps(listNode,indent=2)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
