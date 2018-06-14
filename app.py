from flask import Flask, jsonify, request
import requests

app = Flask(__name__)


@app.route('/test', methods=['GET'])
def test():
    return jsonify({'test': True})


@app.route('/mash')
def mash():
    params = {
        'bitbucket': request.args.get('bb_name'),
        'github': request.args.get('gh_name'),
    }
    url = 'https://api.github.com/users/{}/repos?per_page=1'.format(
        params['github']
        )
    # print(url)
    result = {}
    result['repo_count'] = {
        'original': 0,
        'forked': 0,
    }
    result['repo_watchers'] = 0
    result['user_watchers'] = 0
    result['stars'] = {
        'received': 0,
        'given': 0,
    }
    result['open_issues'] = 0
    result['commits'] = 0
    result['account_size'] = 0
    result['languages'] = {
        'list': [],
        'count': 0
    }
    result['repo_topics'] = {
        'list': [],
        'count': 0,
    }

    gh_req = requests.get(url)
    gh_repos = gh_req.json()
    for repo in gh_repos:
        if repo:
            if repo['fork']:
                result['repo_count']['forked'] += 1
            else:
                result['repo_count']['original'] += 1
            result['repo_watchers'] += repo['watchers']
            result['stars']['received'] += repo['stargazers_count']
            result['open_issues'] += repo['open_issues_count']
            commit_url = (
                'https://api.github.com/repos/{}/{}/contributors'
                .format(params['github'], repo['name'])
                )
            commit_request = requests.get(commit_url)
            if commit_request.status_code == 200:
                commits = commit_request.json()
                user_commits = [x for x in commits if x['login'].lower() == params['github'].lower()]
                print(user_commits)
                result['commits'] += user_commits[0]['contributions']
            result['account_size'] += repo['size']
            if repo['language'] not in result['languages']['list']:
                result['languages']['list'].append(repo['language'])
                result['languages']['count'] += 1
            topics_url = 'https://api.github.com/repos/{}/{}/topics'.format(
                params['github'], repo['name']
            )
            headers = {'Accept': "application/vnd.github.mercy-preview+json"}
            topics_response = requests.get(topics_url, headers=headers)
            result['repo_topics']['list'].append(topics_response.json()['names'])
            result['repo_topics']['list'] = list(set(result['repo_topics']))
            result['repo_topics']['count'] = len(result['repo_topics']['list'])
        else:  # malformed repo data
            raise 'Malformed Repository Data returned from Github'
    return jsonify(result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
