#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script downloads information about all comments, saves data to data.pickle file,
if file already exists it just append new data but remome all dublicates, data is
always sorted by time of comment had posted.

Usage:
    load_comments.py <activity> [--loggin=<login>] [--pass=<password>] [options]

    activity The large nubber from url,6248783577002184704 for example.
    --login=<login> LinkIn login, you could open this script and add deffault [ default: None ].
    --pass=<password>   LinkIn password, you could open this script and add deffault [ default: None ].

    Options
    -c If your query limit per second was exhausted, this option tells the script to get count of comments from file, and use it as offset
"""

#deffault login information you could change it if you need
deffault_login = ''
deffault_password = ''

import requests
import pickle
import json
from BeautifulSoup import BeautifulSoup
import os
from docopt import docopt
import time

basepath = os.path.dirname(__file__)
data_filepath = os.path.abspath(os.path.join(basepath, "data.pickle"))
log_file_name = os.path.abspath(os.path.join(basepath, "log.html"))

arguments = docopt(__doc__)
password = arguments['--pass'] or deffault_password
loggin = arguments['--loggin'] or deffault_login
activity = arguments['<activity>']
do_not_rewrite_file =  bool(arguments['-c'])


start_offset = 0
if do_not_rewrite_file:
    if os.path.isfile(data_filepath):
        with open(data_filepath, 'rb') as f:
            start_offset = len(pickle.load(f))

def create_connection():
    ''' Create a connection to LinkIn service'''

    client = requests.Session()

    HOMEPAGE_URL = 'https://www.linkedin.com'
    LOGIN_URL = 'https://www.linkedin.com/uas/login-submit'

    html = client.get(HOMEPAGE_URL).content
    soup = BeautifulSoup(html)
    csrf = soup.find(id="loginCsrfParam-login")['value']

    login_information = {
        'session_key':loggin,
        'session_password':password,
        'loginCsrfParam': csrf,
    }

    client.post(LOGIN_URL, data=login_information)
    return client


def get_next_chank(start, count, article, client):
    ''' load next chank of comments'''

    url = ('https://www.linkedin.com/pulse-fe/api/v1/comments?urn=urn:li:activity:{}&start={}&count={}&sort=REV_CHRON'.format(
            str(article), str(start), str(count)))
    responce = client.get(url)
    data = client.get(url).text
    return data, responce.status_code

def load_comments(article):
    ''' load comments from article'''

    client = create_connection()
    comments = []
    data_len = 1
    offset = start_offset
    count = 100
    exception_count = 0
    print 'starting from ' + str(offset)
    while data_len:
        if len(comments)>400:
            return comments

        try:
            data, code = get_next_chank(offset, count, article, client)
            if code != 200:
                raise Exception(u"Can't load next chank, {} loaded, code:{}, data:{}".format(len(comments), code,data).encode('utf-8'))

            json_data = json.loads(data)
            elements = json_data['elements']

            total = json_data['paging']['total']

            data_len = len(elements)
            if data_len == 0 and offset + data_len < total:
                print "Server didn, t allow download to fast "
                data_len = 1
                raise Exception("Server didn't allow download to fast")

            comments.extend(elements)
            offset = offset + data_len
            time.sleep(2)
            print 'loaded:{}, from:{}, offset:{}'.format(len(comments), json_data['paging']['total'], offset)
            exception_count = 0
        except Exception as e:

            with open(log_file_name, "a") as log_file:
                log_file.write(str(e))

            exception_count += 1
            time.sleep(1)
            if exception_count > 1:
                print "Something has happened, don't panic :) file with data is fine, just try one more time."
                print e
                return comments
            client = create_connection()

    return comments


comments = load_comments(activity)

#file already exists, read and concatinate
if os.path.isfile(data_filepath) and do_not_rewrite_file:
    with open(data_filepath, 'rb') as f:
        comments.extend(pickle.load(f))

#write to file
with open(data_filepath, 'wb') as f:
    pickle.dump(comments, f)

print "{}: comments is loaded".format(len(comments))
