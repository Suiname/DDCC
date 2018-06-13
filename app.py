from flask import Flask, jsonify, Response, request

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'test': True})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)