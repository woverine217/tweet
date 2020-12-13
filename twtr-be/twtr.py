from flask import Flask, flash, request, jsonify, render_template, redirect, url_for, g, session, send_from_directory, \
    abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_api import status
from redis import Redis
from rejson import Client, Path
from datetime import date, datetime, timedelta
import pytz
import os
import sys
import time
import uuid
import json
import random
import string
import pathlib
import io
from uuid import UUID
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_login import UserMixin
from flask_login import LoginManager

# straight mongo access
from pymongo import MongoClient

# mongo
mongo_client = MongoClient('mongodb://localhost:27017/')

# https://redislabs.com/blog/redis-as-a-json-store/
# https://dzone.com/articles/redis-as-a-json-store
# docker run -p 6379:6379 --name redis-redisjson redislabs/rejson:latest
REDIS_URL = os.getenv('REDIS_URL')

rj = Client(host=REDIS_URL, port=6379, decode_responses=True)
push_to_redis = True

app = Flask(__name__)
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

# config for authentication
app.config['SECRET_KEY'] = 'thisismysecretkeydonotstealit'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Here are my datasets
tweets = dict()

# local collections
collections = (tweets)
prefixes = ('tw')

# database collections
cnames = ('tweets')


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)


def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis


def tryexcept(requesto, key, default):
    lhs = None
    try:
        lhs = requesto.json[key]
        # except Exception as e:
    except:
        lhs = default
    return lhs


def prefix_crud_timestamp_suffix(key):
    prefix = key[:3]
    crud = key[3:4]
    hyphen1 = key.find('-')
    hyphen2 = key[5:].find('-')
    timestamp = key[hyphen1 + 1:hyphen1 + 1 + hyphen2]
    suffix = key[hyphen1 + hyphen2 + 2:]
    return prefix, crud, timestamp, suffix  # coll, op, time, guid


def timestamp_prefix_crud_suffix(key):
    print("key: ", key)
    hyphen1 = key.find('-')
    timestamp = key[:hyphen1]
    prefix = key[hyphen1 + 1:hyphen1 + 4]
    crud = key[hyphen1 + 5:hyphen1 + 6]
    suffix = key[hyphen1 + 7:]
    print("timestamp, prefix, crud, suffix: ", timestamp, prefix, crud, suffix)
    return timestamp, prefix, crud, suffix  # time, coll, op, guid


## seconds since midnight
def ssm():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return str((now - midnight).seconds)


def rjjsonsetwrapper(key, path, r):
    rj.jsonset(key, path, r)


################################################
# Tweets 
################################################

# endpoint to create new tweet
@app.route("/api/tweet", methods=["POST"])
def add_tweet():
    user = request.json['user']
    description = request.json['description']
    private = request.json['private']
    pic = request.json['pic']
    tweet = dict(user=user, description=description, private=private,
                 upvote=0, date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 pic=pic, _id=str(ObjectId()))
    tweets[tweet['_id']] = tweet
    if push_to_redis:
        rjjsonsetwrapper('ttwi-' + ssm() + '-' + tweet['_id'], Path.rootPath(), tweet)
    return jsonify(tweet)


# endpoint to show all of today's tweets
@app.route("/api/tweets-day2", methods=["GET"])
def get_tweets_day2():
    todaystweets = dict(
        filter(lambda elem:
               elem[1]['date'].split(' ')[0] == datetime.now().strftime("%Y-%m-%d"),
               tweets.items())
    )
    return jsonify(todaystweets)


# endpoint to show all tweets
@app.route("/api/tweets", methods=["GET"])
def get_tweets2():
    return jsonify(tweets)


# endpoint to show all of this week's tweets (any user)
@app.route("/api/tweets-week", methods=["GET"])
def get_tweets_week2():
    weekstweets = dict(
        filter(lambda elem:
               (datetime.now() - datetime.strptime(elem[1]['date'].split(' ')[0], '%Y-%m-%d')).days < 7,
               tweets.items())
    )
    return jsonify(weekstweets)


@app.route("/api/tweets-week-results", methods=["GET"])
def get_tweets_week_results():
    weektweets = dict(
        filter(lambda elem:
               (datetime.now() - datetime.strptime(elem[1]['date'].split(' ')[0], '%Y-%m-%d')).days < 7 and
               (
                       False == elem[1]['private']
               ),
               tweets.items())
    )
    # return jsonify(todaystweets)
    return json.dumps({"results":
        sorted(
            [filter_tweet(k) for k in weektweets.keys()],
            key=lambda t: t['date']
        )
    })


# endpoint to show all of today's tweets (user-specific)
def filter_tweet(t):
    tweet = tweets[t]
    return dict(date=tweet['date'], description=tweet['description'],
                private=tweet['private'], user=tweet['user'],
                upvote=tweet['upvote'] if 'upvote' in tweet else 0,
                pic=tweet['pic'])


@app.route("/api/tweets-user-day", methods=["POST"])
def get_tweets_user_day():
    user = request.json['user']
    todaystweets = dict(
        filter(lambda elem:
               elem[1]['date'].split(' ')[0] == datetime.now().strftime("%Y-%m-%d") and
               (
                       False == elem[1]['private'] or
                       user == elem[1]['user']
               ),
               tweets.items())
    )
    # return jsonify(todaystweets)
    return jsonify(
        sorted(
            [filter_tweet(k) for k in todaystweets.keys()],
            key=lambda t: t['date']
        )
    )


# endpoint to show all of this week's tweets (user-specific)
@app.route("/api/tweets-user-week", methods=["POST"])
def get_tweets_user_week():
    user = request.json['user']
    weekstweets = dict(
        filter(lambda elem:
               (datetime.now() - datetime.strptime(elem[1]['date'].split(' ')[0], '%Y-%m-%d')).days < 7 and
               (
                       False == elem[1]['private'] or
                       user == elem[1]['user']
               ),
               tweets.items())
    )
    # return jsonify(weekstweets)
    return jsonify(
        sorted(
            [filter_tweet(k) for k in weekstweets.keys()],
            key=lambda t: t['date']
        )
    )


@app.route("/api/tweets-user-week-results", methods=["GET"])
def get_tweets_user_week_results():
    user = request.json['user']
    weektweets = dict(
        filter(lambda elem:
               (datetime.now() - datetime.strptime(elem[1]['date'].split(' ')[0], '%Y-%m-%d')).days < 7 and
               (
                       False == elem[1]['private'] or
                       user == elem[1]['user']
               ),
               tweets.items())
    )
    # return jsonify(todaystweets)
    return json.dumps({"results":
        sorted(
            [filter_tweet(k) for k in weektweets.keys()],
            key=lambda t: t['date']
        )
    })


# endpoint to get tweet detail by id
@app.route("/api/tweet/<id>", methods=["GET"])
def tweet_detail(id):
    return jsonify(tweets[id])


# endpoint to get tweet detail by user
@app.route("/api/tweetByUser", methods=["GET", 'POST'])
def tweet_details_user():
    user = request.args.get('user')
    print(user)
    details = dict(filter(lambda elem: (user == elem[1]['user']), tweets.items()))
    # return jsonify(details)
    return json.dumps({"results":
        sorted(
            [filter_tweet(k) for k in details.keys()],
            key=lambda t: t['date']
        )
    })


#######################################
# Apply record-level updates from redis
#######################################
def apply(prefix, crud, suffix, record):
    if crud == 'i':
        collections[prefixes.index(prefix)][suffix] = record
    elif record == 'u':
        collections[prefixes.index(prefix)][suffix] = record
    elif record == 'x':
        collections[prefixes.index(prefix)].pop(suffix)


# Goes through redis and finds record-level items to hydrate our collections with
def applyRecordLevelUpdates():
    keys_i = dict()
    keys_u = dict()
    keys_x = dict()
    # import pdb; pdb.set_trace();

    # A: get all 'r'/'i' keys (fresh_keys_downloaded list) and sort by timestamp
    search_pattern = "r"
    for s in search_pattern:
        for i, key in enumerate(rj.keys(s + '*')):
            # get semantics from key
            prefix, crud, timestamp, suffix = prefix_crud_timestamp_suffix(key)
            print("prefix, crud, timestamp, suffix: ", prefix, crud, timestamp, suffix)
            if crud == 'i':
                # print("key, prefix, crud, timestamp, suffix: ", key, prefix, crud, timestamp, suffix)
                # import pdb; pdb.set_trace();
                # I add timestamp first to process chronologically
                keys_i[timestamp + '-' + prefix + '-' + 'i' + '-' + suffix] = key
            elif crud == 'u':
                # print("key, prefix, crud, timestamp, suffix: ", key, prefix, crud, timestamp, suffix)
                # import pdb; pdb.set_trace();
                # I add timestamp first to process chronologically
                keys_u[timestamp + '-' + prefix + '-' + 'u' + '-' + suffix] = key
            elif crud == 'x':
                # print("key, prefix, crud, timestamp, suffix: ", key, prefix, crud, timestamp, suffix)
                # import pdb; pdb.set_trace();
                # I add timestamp first to process chronologically
                keys_x[timestamp + '-' + prefix + '-' + 'x' + '-' + suffix] = key

    # B. apply inserts one by one to current records
    # Note prefix starts with 'r', so get rid of that
    # import pdb; pdb.set_trace()
    for k in sorted(keys_i.items()):
        print("**** :", k)
        timestamp, prefix, crud, suffix = timestamp_prefix_crud_suffix(k[0])
        record = rj.jsonget(k[1], Path.rootPath())
        apply(prefix[1:], 'i', suffix, record)

    # C. apply updates one by one to current records
    for k in sorted(keys_u.items()):
        timestamp, prefix, crud, suffix = timestamp_prefix_crud_suffix(k[0])
        record = rj.jsonget(k[1], Path.rootPath())
        apply(prefix[1:], 'u', suffix, record)

    # D. apply deletes one by one to current records
    for k in sorted(keys_x.items()):
        timestamp, prefix, crud, suffix = timestamp_prefix_crud_suffix(k[0])
        record = rj.jsonget(k[1], Path.rootPath())
        apply(prefix[1:], 'x', suffix, record)


################################################
# Apply collection-level updates from mongo
################################################
def redisAlive():
    print("*** in redisAlive()..")
    try:
        for key in rj.keys('*'):
            print("*** redisjson alive!")
            return True
    except:
        print("*** redisjson dead!")
        return False


def insertgroup(prefix, records):
    # print("prefix: ", prefix)
    # print("prefixes.index(prefix): ", prefixes.index(prefix))
    # print("collections[prefixes.index(prefix)]: ", collections[prefixes.index(prefix)])
    # print("records: ", records)
    # import pdb; pdb.set_trace();
    collections[prefixes.index(prefix)].clear()
    # if the dictionary were a list, I could have done this:
    # collections[prefixes.index(prefix)].extend(list(records.values()))
    for r in records.values():
        collections[prefixes.index(prefix)][r['_id']] = r
    # print("collections[prefixes.index(prefix)]: ", collections[prefixes.index(prefix)])


def updategroup(prefix, records):
    # print("prefix: ", prefix)
    # print("prefixes.index(prefix): ", prefixes.index(prefix))
    # print("collections[prefixes.index(prefix)]: ", collections[prefixes.index(prefix)])
    # print("records: ", records)
    # import pdb; pdb.set_trace();
    for r in records.values():
        # print("r: ", r)
        # print("collections[prefixes.index(prefix)][r['_id']]",
        #        collections[prefixes.index(prefix)][r['_id']])
        collections[prefixes.index(prefix)][r['_id']] = r


# Goes through redis and finds collection-level items to hydrate our collections with
def applyCollectionLevelUpdates():
    # import pdb; pdb.set_trace();
    keys_I = dict()
    keys_U = dict()

    # get all 'k'/'I' and 'k'/'U' keys
    # These contain entire collections (many records per collection)
    search_pattern = "k"
    for s in search_pattern:
        for i, key in enumerate(rj.keys(s + '*')):
            # get semantics from key
            prefix, crud, timestamp, suffix = prefix_crud_timestamp_suffix(key)
            # print("key, prefix, crud, timestamp, suffix: ", key, prefix, crud, timestamp, suffix)
            # import pdb; pdb.set_trace();
            if crud == 'I':
                keys_I[prefix + '-' + crud + '-' + timestamp + '-' + suffix] = key
            elif crud == 'U':
                keys_U[prefix + '-' + crud + '-' + timestamp + '-' + suffix] = key

    # apply collection inserts one by one to current collections
    # import pdb; pdb.set_trace();
    for k in sorted(keys_I.values()):
        # print("key: ", k)
        prefix, _, _, _ = prefix_crud_timestamp_suffix(k)
        # print("prefix: ", prefix)
        # import pdb; pdb.set_trace();
        records = rj.jsonget(k, Path.rootPath())
        insertgroup(prefix[1:], records)

    # apply one by one to current collections
    # Note: Currently I don't foresee there ever being a 'k'/'U' key, but just in case,
    # this is how I'd handle them
    # import pdb; pdb.set_trace();
    for k in sorted(keys_U.values()):
        # print("key: ", k)
        prefix, _, _, _ = prefix_crud_timestamp_suffix(k)
        # print("prefix: ", prefix)
        # import pdb; pdb.set_trace();
        records = rj.jsonget(k, Path.rootPath())
        updategroup(prefix[1:], records)


################################################
# Mock
################################################
@app.route("/api/")
def home():
    db.create_all()
    return """Welcome to online mongo/redis twitter testing ground!<br />
        <br />
        Run the following endpoints:<br />
        From collection:<br/>
        http://localhost:5000/tweets<br />
        http://localhost:5000/tweets-week<br />
        http://localhost:5000/tweets-week-results<br />
        Create new data:<br />
        http://localhost:5000/mock-tweets<br />
        then verify redis keys and values:<br />
        http://localhost:5000/collections-from-redis-cache<br />
        Optionally, to purge redis cache: http://localhost:5000/purge-redis-cache"""


@app.route('/api/purge-redis-cache')
def purge_redis_cache():
    data = dict()
    for key in rj.keys('*'):
        data[key] = rj.jsonget(key, Path.rootPath())
        rj.delete(key)
    return jsonify(data)


@app.route('/api/purge-collection')
def purge_collection():
    tweets.clear()
    return jsonify("done!")


# returns all items from redis
@app.route('/api/collections-from-redis-cache')
def collections_from_redis_cache():
    data = dict()
    try:
        for key in rj.keys('*'):
            # keys.append(key)
            # data.append(rj.jsonget(key, Path.rootPath()))
            # print('data: ', data)
            data[key] = rj.jsonget(key, Path.rootPath())
            # rj.delete(key)
    except:
        print("*** redisjson is dead!")
        # data['oopsie'] = "queue unaccessible"
        # https://www.flaskapi.org/api-guide/status-codes/
        return "Queue inaccessible.", status.HTTP_500_INTERNAL_SERVER_ERROR
    # print()
    # output = []
    # for k,v in zip(keys, data):
    #    output.append(data)
    # return jsonify({'result' : output})
    return jsonify(data)


# get all collections from redis cache 
@app.route("/api/mock-collections-from-redis-cache", methods=["GET"])
def mock_collections_from_redis_cache():
    with app.test_client() as c:
        # json_data = []
        print("calling collections-from endpoint..")
        rv = c.get('/collections-from-redis-cache')
        # json_data.append(rv.get_json())
        # print(jsonify(json_data))

        # return jsonify(json_data)
        return rv.get_json()


# add new tweet, for testing
@app.route("/api/dbg-tweet", methods=["GET"])
def dbg_tweet():
    with app.test_client() as c:
        json_data = []
        name = ''.join(random.choices(string.ascii_lowercase, k=7))
        description = ''.join(random.choices(string.ascii_lowercase, k=50))
        print("posting..")
        rv = c.post('/tweet', json={
            'user': name, 'description': description,
            'private': False, 'pic': None
        })
    return rv.get_json()


# endpoint to mock tweets
BASE_URL = None


@app.route("/api/mock-tweets", methods=["GET"])
def mock_tweets():
    # Hack: Get the base url from one of the first requests
    global BASE_URL
    if BASE_URL is None:
        BASE_URL = request.base_url
        # BASE_URL = request.url
        BASE_URL = BASE_URL.replace('/api/mock-tweets', '')
        print("*** BASE_URL is", BASE_URL)

    # first, clear all collections
    for c in collections:
        c.clear()

    # turn off pre-request-processing
    global turn_off_before_request_func
    turn_off_before_request_func = True
    print("*** mock_tweets(): pre-request-processing turned off! I should see no more calls to HydrateFromMongo()!")

    # second clear redis queue
    try:
        for k in rj.keys('*'):
            rj.delete(k)
    except:
        print("*** mock-tweets(): redisjson is dead!")

    # third, create new data
    json_data_all = []
    with app.test_client() as c:

        # tweets: 30
        print("@@@ mock-tweets(): tweets..")
        json_data_all.append("@@@ tweets")
        for i in range(30):
            description = []
            private = random.choice([True, False])
            for j in range(20):
                w = ''.join(random.choices(string.ascii_lowercase, k=random.randint(0, 7)))
                description.append(w)
            description = ' '.join(description)
            u = ''.join(random.choices(string.ascii_lowercase, k=7))
            img_gender = random.choice(['women', 'men'])
            img_index = random.choice(range(100))
            img_url = 'https://randomuser.me/api/portraits/' + img_gender + '/' + str(img_index) + '.jpg'
            rv = c.post('/tweet', json={
                'user': u, 'private': private,
                'description': description, 'pic': img_url
            })
            # json_data.append(rv.get_json())
        json_data_all.append(tweets)

    # turn on pre-request-processing
    turn_off_before_request_func = False
    print("*** mock_tweets(): pre-request-processing turned back on!")

    # done!
    print("@@@ mock-tweets(): done!")
    return jsonify(json_data_all)


##################
# ADMINISTRATION #
##################

# This runs once before the first single request
# Used to bootstrap our collections
info_level = -1


@app.before_first_request
def before_first_request_func():
    # import pdb; pdb.set_trace()
    # print("This function will run once")
    global info_level
    current_dir = pathlib.Path(__file__).parent
    print("*** operating folder: ", current_dir)
    if os.path.isfile(str(current_dir) + '/print.txt'):
        info_level = 2
        print("*** printing level monitoring active!")
    elif os.path.isfile(str(current_dir) + '/log.txt'):
        info_level = 1
        print("*** logging level monitoring active!")
    else:
        info_level = 0
        print("*** stealth level monitoring active!")

    if redisAlive():
        print("*** before_first_request_func(): Running applyCollectionLevelUpdates()..")
        applyCollectionLevelUpdates()
    else:
        print("*** before_first_request_func(): Redis dead!")


# This runs once before any request
# Used to periodically apply fresh records from redis
# so we don't have to refresh the entire collection
# or have to refresh from mongo for each client, i.e. 
# I can now allow a singleton Timeloop-based app to be
# in charge of that, alleviating mongo-to-cluster comms.
# Note need to ensure our cruds are idempotent
# because I'm bound to reapply my own mods.
turn_off_before_request_func = False
session_refresh = None


@app.before_request
def before_request_func():
    global session_refresh

    if turn_off_before_request_func:
        return

    print("Setting session['last_refresh'] and conditionally running applyRecordLevelUpdates()..")
    if redisAlive():
        if session_refresh == None:
            sessession_refreshion = datetime.now()
            print("****** Added session['last_refresh']")
        elif 3 * 60 <= (datetime.now() - session_refresh).seconds:
            applyRecordLevelUpdates()
            session_refresh = datetime.now()
            print("****** Refreshed!")


############################
# INFO on containerization #
############################

# To containerize a flask app:
# https://pythonise.com/series/learning-flask/building-a-flask-app-with-docker-compose


############################
# For Authentication #
############################

@app.route('/api/login')
def login():
    return """Welcome to online mongo/redis twitter testing ground!<br />"""


@app.route('/api/login', methods=['POST'])
def login_post():
    req_data = request.get_json()
    username = req_data['username']
    password = req_data['password']
    print(password)
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return jsonify("Please check your login details and try again.")

    login_user(user, remember=remember)
    return jsonify("successfully login")


@app.route('/api/signup')
def signup():
    return render_template('signup.html')


@app.route('/api/signup', methods=['POST'])
def signup_post():
    req_data = request.get_json()
    print(req_data)
    username = req_data['username']
    password = req_data['password']
    print("username" + username)
    print("password" + password)
    user = User.query.filter_by(username=username).first()

    if user:
        flash('username already exists')
        return jsonify('username already exists')

    new_user = User(username=username, password=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()

    return jsonify("username" + " " + username)


@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return """Welcome to online mongo/redis twitter testing ground!<br />"""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)