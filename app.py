from flask import Flask, jsonify, Response, request
import requests

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'test': True})

@app.route('/mash')
def mash():
    params = {
        'bitbucket': request.args.get('bb_name'),
        'github': request.args.get('gh_name')
    }
    url = 'https://api.github.com/users/{}/repos'.format(params['github'])
    # print(url)
    gh_req = requests.get(url)
    gh_repos = gh_req.json()
    return jsonify(gh_repos)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)