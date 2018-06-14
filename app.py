from flask import Flask, jsonify, request
import requests
import os

username = os.environ.get('GITHUB_USER')
password = os.environ.get('GITHUB_PASS')

app = Flask(__name__)


def create_response():
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
    return result


def merge_bb_data(params, result):
    bb_url = 'https://api.bitbucket.org/1.0/users/{}'.format(params['bitbucket'])
    bb_req = requests.get(bb_url)
    bb_repos = bb_req.json()
    if bb_repos['repositories'] and len(bb_repos['repositories']):
        for repo in bb_repos['repositories']:
            slug = repo['slug']
            if repo['is_fork']:
                result['repo_count']['forked'] += 1
            else:
                result['repo_count']['original'] += 1
            result['account_size'] += repo['size']
            if(repo['language'] and
               repo['language'].lower() not in result['languages']['list']
               ):
                result['languages']['list'].append(repo['language'].lower())
                result['languages']['count'] += 1
            repo_url = 'https://api.bitbucket.org/{}'.format(
                repo['resource_uri'])
            repo_req = requests.get(repo_url)
            if repo_req.status_code == 200:
                repo_data = repo_req.json()
                result['repo_watchers'] += repo_data['followers_count']
                if repo_data['has_issues']:
                    issues_req = requests.get(repo_url + '/issues?status=open')
                    issues_data = issues_req.json()
                    result['open_issues'] += issues_data.get('count')
              
            follower_url = 'https://api.bitbucket.org/1.0/users/{}/followers'.format(
                params['bitbucket']
            )
            follower_req = requests.get(follower_url)
            if follower_req.status_code == 200:
                follower_data = follower_req.json()
                result['user_watchers'] += follower_data['count']
            
            commits_url = 'https://api.bitbucket.org/1.0/repositories/{}/{}/changesets/'.format(
                params['bitbucket'], slug
            )
            commits_req = requests.get(commits_url)
            if commits_req.status_code == 200:
                commits_data = commits_req.json()
                result['commits'] += commits_data.get('count')
    return result


def merge_gh_data(params, result):
    url = 'https://api.github.com/users/{}/repos?per_page=3'.format(
        params.get('github')
        )
    gh_req = requests.get(url, auth=(username, password))
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
                .format(params.get('github'), repo['name'])
                )
            commit_request = requests.get(commit_url, auth=(username, password))
            if commit_request.status_code == 200:
                commits = commit_request.json()
                user_commits = [x for x in commits if x['login'].lower() == params.get('github').lower()]
                result['commits'] += user_commits[0]['contributions']
            result['account_size'] += repo['size']
            if(repo['language'] and
               repo['language'].lower() not in result['languages']['list']
               ):
                result['languages']['list'].append(repo['language'].lower())
                result['languages']['count'] += 1
            topics_url = 'https://api.github.com/repos/{}/{}/topics'.format(
                params.get('github'), repo['name']
            )
            print(topics_url)
            headers = {'Accept': "application/vnd.github.mercy-preview+json"}
            topics_response = requests.get(topics_url, headers=headers, auth=(username, password))
            if(len(topics_response.json())):
                result['repo_topics']['list'] += topics_response.json()['names']
                result['repo_topics']['list'] = list(set(result['repo_topics']['list']))
                result['repo_topics']['count'] = len(result['repo_topics']['list'])
        else:  # malformed repo data
            raise 'Malformed Repository Data returned from Github'
    return result


@app.route('/test', methods=['GET'])
def test():
    return jsonify({'test': True})


@app.route('/mash')
def mash():
    params = {
        'bitbucket': request.args.get('bb_name'),
        'github': request.args.get('gh_name'),
    }
    result = create_response()
    result = merge_gh_data(params, result)
    result = merge_bb_data(params, result)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
