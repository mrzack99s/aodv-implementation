import pickle
from flask import Flask, request
from flask_cors import CORS
import aodv_client,json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app, resources={r'/*': {'origins': '*'}})

scAPI = 20003

@app.route('/', methods=['GET'])
def getDefaultPage():
    return "AODV-API..... It's work!!"


@app.route('/getRoutingTable', methods=['GET'])
def getRoutingTable():
    mrzFile = open("routing_table.mrz", 'rb')
    routing_table  = pickle.load(mrzFile)
    mrzFile.close()

    return json.dumps(routing_table,indent=2)



@app.route('/requestDiscoveryPath', methods=['POST'])
def requestDiscoveryPath():
    dataLoad = request.json
    aodv_client.requestDiscoveryPath(IP=dataLoad["toIp"])

    return "wait for getrouting"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)