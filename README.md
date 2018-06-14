# DivvyDose Code Challenge
Flask application to merge bitbucket and github API information and return as single JSON object

## Installation instructions
Using python3.6, create a virtual environment
```
python3 -m venv /path/to/env
source /path/to/env/bin/activate
```
Install requirements with pip:
```
pip install -r requirements.txt
```

NOTE: The rate limiting from the github API is pretty restrictive unless you authenticate as a github user when making requests.  I am currently importing github username and password via the environment variables `GITHUB_USER` and `GITHUB_PASS`.  Set these how you would like, my example sets them at the command line at runtime.  Also note that basic auth does NOT work if your user has 2-factor authentication enabled, so either temporarily disable it or create a dummy account without 2-factor auth.

Run Flask:
```
GITHUB_USER=username GITHUB_PASS=password FLASK_APP=app.py python -m flask run
```
Follow the link in console to your running app, usually http://127.0.0.1:5000

## Usage
The route to merge the profiles is exposed at `/merge`.  This route takes two query parameters, `bb_name` for the bitbucket user and `gh_name` for the github user.  Here's an example url: `http://127.0.0.1:5000/merge?bb_name=pygame&gh_name=miguelgrinberg`

## Data Format
Here's an annotated sample JSON output
```
{
	account_size: 40307881, # size of the merged accounts
	commits: 8875, # total commits of the merged accounts across all branches
	languages: { 
		count: 11, # total number of unique languages use
		list: [ # a deduped list of languages used
			"python",
			"shell",
			"batchfile",
			"html",
			"javascript",
			"css",
			"coffeescript",
			"ruby",
			"c",
			"c++",
			"hcl"
		]
	},
	open_issues: 355, # total open issues
	repo_count: {
		forked: 57, # number of forked repositories
		original: 72 # number of non-forked repositories
	},
	repo_topics: {
		count: 48, # count of all topics across all github repos
		list: [
			"webapp",
			"unittest",
			"serverless-deployments",
			...etc
		]
	},
	repo_watchers: 15430, # total number of watchers/followers across repos
	stars: {
		given: 218, # total github repos users have starred
		received: 15165 # total numbers of stars on users own github repos
	},
	user_watchers: 5866 # total number of users following both merged accounts
}
```

## Notes and Considerations
- Chose GET as the REST verb, since you are retrieving read-only data and nothing is being altered
- Since using GET, chose to expose query params to set the user accounts to merge
- Currently all responses are checked for 200 status, if the APIs return anything else, the response is just ignored and the data from that particular call is not incremented.  If given more time I would try to handle this with retries and depending on the data being retrieved, return an error response instead of the data if unsuccessful.
- Code is not terribly efficient, there are many REST calls being made (4x at least per repo).  I also didn't refactor for efficiency, only readability.  If given more time I would try to reduce the number of API calls by studying the API documentation more thoroughly and refactor the code to run faster probably by reducing iterations where possible.
- Used Flake8 standard for linting
- Did not have enough time to write unit tests.  As is, I would try to unit test by mocking the requests library response with truncated real JSON responses from the github and bitbucket API.  
- I tried to make my code run as a series of function calls so I could test each logical segment individually, however even the three functions I made to create the data object, merge in the github data, and merge in the bitbucket data could be further broken down (function for getting follwer data, commit data, etc).  This would help the readability, maintainability, and testability of the code.
- Bitbucket doesn't have topics or stars, so the data for those is from github only