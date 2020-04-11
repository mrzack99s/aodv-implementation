import redis
from flask import Flask, request
from flask_cors import CORS
import aodv_client,json

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
        return json.dumps(routing_table,indent=2)

    return ""



@app.route('/requestDiscoveryPath', methods=['POST'])
def requestDiscoveryPath():
    dataLoad = request.json
    result = aodv_client.requestDiscoveryPath(IP=dataLoad["toIp"])

    return result


if __name__ == '__main__':
    app.run(debug=True, host='::', port=8000)