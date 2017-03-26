#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script downloads information about all comments, saves data to data.pickle file,
if file already exists it just append new data but remome all dublicates, data is
always sorted by time of comment had posted.

Usage:
    load_comments.py activity [--login=<login>] [--pass=<password>]

Options:
    activity The large nubber from url,6248783577002184704 for example.
    --login=<login> LinkIn login, you could open this script and add deffault [ default: None ].
    --pass=<password>   LinkIn password, you could open this script and add deffault [ default: None ].
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


def create_connection(loggin, password):
    ''' Create a connection to LinkIn service'''

    client = requests.Session()

    HOMEPAGE_URL = 'https://www.linkedin.com'
    LOGIN_URL = 'https://www.linkedin.com/uas/login-submit'

    login_information = {
        'session_key':loggin,
        'session_password':password,
        'loginCsrfParam': csrf,
    }

    html = client.get(HOMEPAGE_URL).content
    soup = BeautifulSoup(html)
    csrf = soup.find(id="loginCsrfParam-login")['value']

    client.post(LOGIN_URL, data=login_information)
    return client


def get_next_chank(start,count,article,client):
    ''' load next chank of comments'''

    url = ('https://www.linkedin.com/pulse-fe/api/v1/comments?urn=urn:li:activity:{}&start={}&count={}&sort=REV_CHRON'.format(
            str(article),str(start),str(count)))
    responce = client.get(url)
    data = client.get(url).text
    return data, responce.code

def load_comments(article,client):
    ''' load comments from article'''

    comments = []
    data_len = 1
    offset = 0
    count = 200
    exception_count = 0
    while data_len:
        try:
            data ,code = get_next_chank(offset,count,article,client)
            if code != 200:
                raise "Can't load next chank, {} loaded, code:{}".format(len(comments),code)

            json_data = json.loads(data)
            elements = json_data['elements']

            data_len = len(elements)
            offset = offset + data_len

            comments.extend([ (element['commenter']['name'], element['message'],element['createdDate']) for element in elements ])
            offset = offset + data_len
            print 'loaded:{}, from:{}'.format(len(comments),json_data['paging']['total'])
            exception_count = 0
        except Exception as e:
            exception_count += 1
            if exception_count > 3:
                print "Something has happened, don't panic :) file with data is fine, just try one more time."
                print e
                exit()


basepath = os.path.dirname(__file__)
data_filepath = os.path.abspath(os.path.join(basepath, "data.pickle"))

arguments = docopt(__doc__)
password = arguments['--pass'] or deffault_password
loggin = arguments['--loggin'] or deffault_login
activity = arguments['activity']

client = create_connection(loggin, password)
comments = load_comments(activity,client)

#file already exists, read and concatinate
if os.path.isfile(data_filepath):
    with open(data_filepath,'rb') as f:
        comments.extend(pickle.load(f))

#remove dublicates
comments = list(set(comments))

#sort by time
elements.sort(key = lambda e: e[2])

#write to file
with open(data_filepath,'wb') as f:
    pickle.dump(comments, f)
