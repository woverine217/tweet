from pymongo import MongoClient
from rejson import Client, Path
import redis
import json
import time
import csv
import os
import dns
from timeloop import Timeloop
from datetime import date, datetime, timedelta
from uuid import UUID
from bson.objectid import ObjectId

########### only for debugging
# pip install rq-dashboard
# rq-dashboard
# docker-machine ip
# http://192.168.99.104:9181

########### This is the singleton data access layer.
# The k8s pods add new inserts or updates to the queue when they happen,
# and read redis every 3 minutes to get new records from other pods and apply them
# (irrespective if the key came from the same pod or not, easier than having to
# deal with provenance). Every 10 minutes, this layer reads redis, saves to mongo,
# and uploads fresh collections that pods can refresh from when they need to (e.g.
# newborn). When it downloads to mongo, it checks the key timestamp and if it's fresher
# than 10 minutes ago, it keeps the record around so that pods can synch up. If it's
# older than 10 minutes ago, it deletes the record from the queue.

# pip install timeloop
tl = Timeloop()
stop_tl = False

# install mongodb
# https://docs.mongodb.com/manual/installation/

# mongo and redis clients
#zk 12/13 edit
client = MongoClient("mongodb://twittermongo:twittermongo@cluster0-shard-00-00.bctrb.mongodb.net:27017,cluster0-shard-00-01.bctrb.mongodb.net:27017,cluster0-shard-00-02.bctrb.mongodb.net:27017/test?ssl=true&replicaSet=atlas-wg8bnf-shard-0&authSource=admin&retryWrites=true&w=majority")
# client = MongoClient('mongodb://localhost:27017/')

REDIS_URL = os.getenv('REDIS_URL')
rj = Client(host=REDIS_URL, port=6379, decode_responses=True)

# rj = Client(host='127.0.0.1', port=6379, decode_responses=True)


def prefix_crud_timestamp_suffix(key):
    prefix = key[:3]
    crud = key[3:4]
    hyphen1 = key.find('-')
    hyphen2 = key[5:].find('-')
    timestamp = key[hyphen1+1:hyphen1+1+hyphen2]
    suffix = key[hyphen1+hyphen2+2:]
    return prefix, crud, timestamp, suffix #coll, op, time, guid

def prefix(key):
    return key[:3]

def crud(key):
    return key[3:4]

def timestamp(key):
    hyphen2 = key[6:].find('-')
    hyphen3 = key[hyphen2+1:].find('-')
    return int(key[6:hyphen3])

def suffix(key):
    hyphen2 = key[6:].find('-')
    hyphen3 = key[hyphen2+1:].find('-')
    return key[hyphen3+1:]

## seconds since midnight
def ssm():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    #print(now, midnight)
    #print((now - midnight).seconds)
    return (now - midnight).seconds


last_action = 2
# consolidate into single time loop
@tl.job(interval=timedelta(seconds=181))
def all_jobs():
    global last_action

    if last_action == 2:
        mongo2redis_ez()
        last_action = 1
    else:
        redis2mongo_ez()
        last_action = 2


# from redis queue to mongo database
def redis2mongo_ez():

    print("****** [" + str(datetime.today()) + "], redis2mongo_ez()..")
    global stop_tl
    if stop_tl: return

    # first, check that redis is up, otherwise exit and retry on next iteration
    try:
        for key in rj.keys('*'):
            print(key)
            prefix, crud, timestamp, suffix = prefix_crud_timestamp_suffix(key)
            print(prefix)
            print(crud)
            print(timestamp)
            print(suffix)
            break
    except:
        print('****** redis2mongo_ez(): redisjson is dead!')
        return

    # db access
    with client:
        db = client['twitter']

        # search_pattern = ""
        # for s in search_pattern:
        #     print(s)
        for key in rj.keys('*'):
            print('search' + key)
            try:
                # get semantics from key
                prefix, crud, timestamp, suffix = prefix_crud_timestamp_suffix(key)
                print(prefix)
                print(crud)
                print(timestamp)
                print(suffix)

                r = rj.jsonget(key)
                print(r)

                mongo_collection = db['tweets']
                #import pdb; pdb.set_trace()

                if crud == 'i':
                    print("...insert_one() to mongo: ", r)
                    try:
                        result = mongo_collection.insert_one(r)
                        print("inserted _ids: ", result.inserted_id)
                    except Exception as e:
                        print(e)

                elif crud == 'u':
                    print("...update_one() to mongo: ", r)
                    try:
                        result = mongo_collection.update_one(
                            {"_id" : r['_id']},
                            {"$set": r},
                            upsert=True)
                        print ("...update_one() to mongo acknowledged:", result.modified_count)
                    except Exception as e:
                        print(e)

                # delete key
                rj.delete(key)

            except Exception as e:
                print(e)


# Upload fresh records from mongo into one grouped insert 'I' cache per collection.
# Bootstrapping clients should hydrate from these records, which refresh every
# hour, then continue refining records from *fresher* 'i' and 'u' redis elements.
def mongo2redis_ez():

    print("****** [" + str(datetime.today()) + "], mongo2redis_ez()..")
    global stop_tl
    if stop_tl: return

    # first, check that redis is up, otherwise exit and retry on next iteration
    try:
        for key in rj.keys('*'):
            break
    except:
        print('****** mongo2redis_ez(): redisjson is dead!')
        return

    with client:
        db = client['twitter']

        # pop old cache collections from redis, if they exist,
        search_pattern = "k"
        print("*** Popping old k-collections from redis..")
        for s in search_pattern:
            for key in rj.keys(s + '*'):
                # get semantics from key
                prefix, crud, timestamp, suffix = prefix_crud_timestamp_suffix(key)
                if (crud == 'I' or crud == 'U'):
                    rj.delete(key)

        # refresh them from mongo
        # Note that the alphabetical ordering will be gone since we replace
        # the first letter of the prefix with a 'k' (for cached). We will rely
        # on timestamp order to apply the cached records.
        mongo_collection = db['tweets']

        # all records!
        records = list(mongo_collection.find({}))
        howmany = len(records)
        print("collection length: ", str(howmany))
        if 0 < howmany:
            indexes = [str(i).zfill(len(str(howmany))) for i in range(howmany)]
            records_dictionary = dict(list(zip(indexes, records)))
            print("records_dictionary: ", records_dictionary)
            # group_key = 'k' + str(records_dictionary.keys()) + 'I-' + str(ssm()) + '-' + str(ObjectId())
            group_key = 'k' + indexes[0][1:] + 'I-' + str(ssm()) + '-' + str(ObjectId())
            print("group_key: ", group_key)
            #import pdb; pdb.set_trace();
            rj.jsonset(group_key, Path.rootPath(), records_dictionary)
            print("*** inserted: " + str(howmany) + " records into redis.")
            #import pdb; pdb.set_trace();


def __del__(self):
  tl.stop()

if __name__ == "__main__":
    tl.start(block=True)