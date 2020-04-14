import redis
from flask import Flask, request
from flask_cors import CORS
import aodv_client, json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app, resources={r'/*': {'origins': '*'}})
shareMemoryData = redis.StrictRedis(host="::1", port=6379, password="passwd", decode_responses=True)


@app.route('/', methods=['GET'])
def getDefaultPage():
    return "AODV-API..... It's work!!"


@app.route('/getRoutingTable', methods=['GET'])
def getRoutingTable():
    if shareMemoryData.exists("routing_table"):
        routing_table = json.loads(shareMemoryData.get("routing_table"))
        return json.dumps(routing_table, indent=2)

    return ""


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
        return json.dumps(message_recv, indent=2)

    return "No data"


if __name__ == '__main__':
    app.run(debug=True, host='::', port=8000)
