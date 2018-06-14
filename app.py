from flask import Flask, jsonify, request
import requests
import os
import re

# get username and password from env variables
username = os.environ.get('GITHUB_USER')
password = os.environ.get('GITHUB_PASS')

app = Flask(__name__)


def create_response():
    """Format Response JSON, referred to as result throughout.
    """

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
    """Using reqests, perform a get on the appropriate URL.
    Return the json if you get a 200 status code on the response,
    otherwise return an empty object."""

    req = requests.get(url, auth=auth, headers=headers)
    if req.status_code == 200:
        return req.json()
    else:
        return {}


def merge_bb_data(params, result):
    """Retrieve all data from Bitbucket's API and merge into the
    result object.  Further detail of logic is explained in
    inline comments."""

    # retrieve the list of all repositories from the user endpoint
    bb_url = 'https://api.bitbucket.org/1.0/users/{}'.format(
        params['bitbucket']
    )
    bb_repos = get_json(bb_url)
    if bb_repos.get('repositories') and len(bb_repos['repositories']):
        # loop through each repository in the list
        for repo in bb_repos['repositories']:
            slug = repo['slug']
            # check if the repo is a fork or not
            if repo['is_fork']:
                result['repo_count']['forked'] += 1
            else:
                result['repo_count']['original'] += 1
            # add to the running total of account size
            result['account_size'] += repo['size']
            # check if the language of the repo is already in the running list
            # if not, add it to the list and increment the count.
            if(repo['language'] and
               repo['language'].lower() not in result['languages']['list']
               ):
                result['languages']['list'].append(repo['language'].lower())
                result['languages']['count'] += 1
            # hit the individual repo endpoint
            repo_url = 'https://api.bitbucket.org/{}'.format(
                repo['resource_uri'])
            repo_data = get_json(repo_url)
            # Add the number of repo followers of the repo to the running total
            result['repo_watchers'] += repo_data.get('followers_count', 0)
            # check if there are open issues
            if repo_data.get('has_issues'):
                # perform lookup of only open issues and add to count
                issues_data = get_json(repo_url + '/issues?status=open')
                result['open_issues'] += issues_data.get('count', 0)
            # get number of user followers to the running count
            follower_url = (
                'https://api.bitbucket.org/1.0/users/{}/followers'.format(
                    params['bitbucket'])
            )
            follower_data = get_json(follower_url)
            result['user_watchers'] += follower_data.get('count', 0)
            # get the total number of commits across all branches
            commits_url = (
                'https://api.bitbucket.org/1.0/repositories/{}/{}/changesets/'
                .format(
                    params['bitbucket'], slug)
            )
            commits_data = get_json(commits_url)
            result['commits'] += commits_data.get('count', 0)
    return result


def merge_gh_data(params, result):
    """Retrieve all data from Github's API and merge into the
    result object.  Further detail of logic is explained in
    inline comments."""
    # get user followers from user profile, add to count
    follower_url = 'https://api.github.com/users/{}'.format(
        params.get('github')
    )
    followers_data = get_json(follower_url, auth=(username, password))
    result['user_watchers'] += followers_data.get('followers', 0)
    # lookup the list of users' starred repos, set page size to 1
    star_url = 'https://api.github.com/users/{}/starred?per_page=1'.format(
        params.get('github')
    )
    stars_req = requests.get(star_url, auth=(username, password))
    if stars_req.status_code == 200:
        # because page size=1, the "last" url will contain star total
        stars_last_url = stars_req.headers['Link'].split(',')[1]
        # use regex to extract the last page value
        num_stars = re.search(r".*&page=([0-9]*)>;", stars_last_url)
        # cast as a number from string and add to count
        result['stars']['given'] += int(num_stars.group(1))
    more = True
    page = 0
    gh_repos = []
    # loop through list of github repos, 100 at a time
    while more:
        # get the next page of results
        page += 1
        repo_url = (
            'https://api.github.com/users/{}/repos?per_page=100&page={}'
            .format(params.get('github'), page)
        )
        repo_json = get_json(repo_url, auth=(username, password))
        if len(repo_json):  # result is an array
            gh_repos += repo_json
        else:  # no results, exit loop
            more = False
    for repo in gh_repos:
        if repo:
            # check if the repo is fork or original
            if repo['fork']:
                result['repo_count']['forked'] += 1
            else:
                result['repo_count']['original'] += 1
            # add to the number of repo watchers
            result['repo_watchers'] += repo['watchers']
            # update stars received
            result['stars']['received'] += repo['stargazers_count']
            # update count of open issues
            result['open_issues'] += repo['open_issues_count']
            # lookup all commits of the repo
            commit_url = (
                'https://api.github.com/repos/{}/{}/contributors'
                .format(params.get('github'), repo['name'])
                )
            commits = get_json(commit_url, auth=(username, password))
            # filter list of commits to only the user
            user_commits = (
                [x for x in commits
                    if x['login'].lower() == params.get('github').lower()]
            )
            # add to the commits count
            if user_commits and user_commits[0]:
                result['commits'] += user_commits[0].get('contributions', 0)
            # add to the account size total
            result['account_size'] += repo['size']
            # check if the repo language is not already in the list
            if(repo['language'] and
               repo['language'].lower() not in result['languages']['list']
               ):
                # append it to the list and increment the count
                result['languages']['list'].append(repo['language'].lower())
                result['languages']['count'] += 1
            # get all topics, experimental feature so needs special header
            topics_url = 'https://api.github.com/repos/{}/{}/topics'.format(
                params.get('github'), repo['name']
            )
            headers = {'Accept': "application/vnd.github.mercy-preview+json"}
            topics = get_json(
                topics_url,
                headers=headers,
                auth=(username, password)
                )
            if(topics.get('names')):
                # concatenate array of topics
                result['repo_topics']['list'] += topics['names']
                # dedupe the list
                result['repo_topics']['list'] = list(
                    set(result['repo_topics']['list'])
                    )
                # set the count
                result['repo_topics']['count'] = len(
                    result['repo_topics']['list']
                    )
    return result


@app.route('/test', methods=['GET'])
def test():
    """Heartbeat route to ensure app is running."""
    return jsonify({'heartbeat': True})


@app.route('/merge')
def mash():
    """Route to merge the github and bitbucket profiles.
    Takes 2 query params, the bitbucket account name
    and the github account name, then creates the response
    object and merges the data from each profile into it.
    """
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
