from flask import Flask, jsonify, request
import requests
import os
import re

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


def get_json(url, auth=None, headers=None):
    req = requests.get(url, auth=auth, headers=headers)
    if req.status_code == 200:
        return req.json()
    else:
        return {}


def merge_bb_data(params, result):
    bb_url = 'https://api.bitbucket.org/1.0/users/{}'.format(params['bitbucket'])
    bb_repos = get_json(bb_url)
    if bb_repos.get('repositories') and len(bb_repos['repositories']):
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
            repo_data = get_json(repo_url)
            result['repo_watchers'] += repo_data.get('followers_count', 0)
            if repo_data.get('has_issues'):
                issues_data = get_json(repo_url + '/issues?status=open')
                result['open_issues'] += issues_data.get('count', 0)

            follower_url = 'https://api.bitbucket.org/1.0/users/{}/followers'.format(
                params['bitbucket']
            )
            follower_data = get_json(follower_url)
            result['user_watchers'] += follower_data.get('count', 0)
            
            commits_url = 'https://api.bitbucket.org/1.0/repositories/{}/{}/changesets/'.format(
                params['bitbucket'], slug
            )
            commits_data = get_json(commits_url)
            result['commits'] += commits_data.get('count', 0)
    return result


def merge_gh_data(params, result):
    follower_url = 'https://api.github.com/users/{}'.format(
        params.get('github')
    )
    followers_data = get_json(follower_url, auth=(username, password))
    result['user_watchers'] += followers_data.get('followers', 0)

    star_url = 'https://api.github.com/users/{}/starred?per_page=1'.format(
        params.get('github')
    )
    stars_req = requests.get(star_url, auth=(username, password))
    if stars_req.status_code == 200:
        # get the last page from the header to find the number of stars
        stars_last_url = stars_req.headers['Link'].split(',')[1]
        num_stars = re.search(r".*&page=([0-9]*)>;", stars_last_url)
        result['stars']['given'] += int(num_stars.group(1))

    repo_url = 'https://api.github.com/users/{}/repos?per_page=100'.format(
        params.get('github')
    )
    gh_repos = get_json(repo_url, auth=(username, password))
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
            commits = get_json(commit_url, auth=(username, password))
            user_commits = [x for x in commits if x['login'].lower() == params.get('github').lower()]
            if user_commits and user_commits[0]:
                result['commits'] += user_commits[0].get('contributions', 0)
            result['account_size'] += repo['size']
            if(repo['language'] and
               repo['language'].lower() not in result['languages']['list']
               ):
                result['languages']['list'].append(repo['language'].lower())
                result['languages']['count'] += 1
            topics_url = 'https://api.github.com/repos/{}/{}/topics'.format(
                params.get('github'), repo['name']
            )
            headers = {'Accept': "application/vnd.github.mercy-preview+json"}
            topics = get_json(topics_url, headers=headers, auth=(username, password))
            if(topics.get('names')):
                # concatenate array of topics
                result['repo_topics']['list'] += topics['names']
                # dedupe the list
                result['repo_topics']['list'] = list(set(result['repo_topics']['list']))
                # set the count
                result['repo_topics']['count'] = len(result['repo_topics']['list'])
    return result


@app.route('/test', methods=['GET'])
def test():
    result = get_json('https://api.bitbucket.org/2.0/repositories/Suiname/expedia/commits')
    return jsonify(result)


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
