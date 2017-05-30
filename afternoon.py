from __future__ import print_function
import boto3

import json
import urllib
import urllib2
import urlparse
import base64
from datetime import datetime

print('Loading function')

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    bodyJson = event['body-json']
    command = urlparse.parse_qs(bodyJson, keep_blank_values = True)

    #if command['command'][0] == '/prop':
    #    resp = prop_handler(command)
    #else:
    #    resp = tweet_handler(command)
    #return resp

    return hello_handler(command)

class User(object):
    def __init__(self, slack_user, toggl_api_key, last_verified, last_checked):
        self.slack_user = slack_user
        self.toggl_api_key = toggl_api_key
        self.last_verified = last_verified
        self.last_checked = last_checked

    def create_user(self):
        dynamodb.put_item(TableName='timebot_users',
                          Item={ 'slack_user': { 'S': self.slack_user },
                                 'toggl_api_key': { 'S': self.toggl_api_key },
                                 'last_verified': { 'S': self.last_verified },
                                 'last_checked': { 'S': self.last_checked }
                          })
        return "Success!"

    def update_latest(self):
        now = datetime.now()
        now_string = now.strftime("%Y-%m-%dT%H:%M:%S")
        dynamodb.update_item(TableName='timebot_users',
                             Key={'slack_user': { 'S': self.slack_user} },
                             UpdateExpression="SET last_verified=:date",
                             ExpressionAttributeValues={':date': {'S': now_string }})
        return "Success!"

    def update_checked(self):
        now = datetime.now()
        now_string = now.strftime("%Y-%m-%dT%H:%M:%S")
        dynamodb.update_item(TableName='timebot_users',
                             Key={'slack_user': { 'S': self.slack_user} },
                             UpdateExpression="SET last_checked=:date",
                             ExpressionAttributeValues={':date': {'S': now_string }})
        return "Success!"

    def show(self):
        return self.slack_user + ' ' + self.last_checked + ' ' + self.last_verified

    def get_toggl_entries(self):
        username = self.toggl_api_key
        password = "api_token"
        base64string = base64.b64encode('%s:%s' % (username, password))
        start = urllib.quote(self.last_verified)
        req = urllib2.Request("https://www.toggl.com/api/v8/time_entries?start_date=" + start)
        req.add_header('Authorization', "Basic %s" % base64string)
        raw_entries = urllib2.urlopen(req).read()
        entries = json.loads(raw_entries)
        return entries

    def since_last_verified(self):
        if self.last_verified == "never":
            date = datetime.today() - timedelta(1)
            date = date.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            date = datetime.strptime(self.last_verified, "%Y-%m-%dT%H:%M:%S")
        return date + "-05:00"

def get_user(slack_user):
    resp = dynamodb.get_item(TableName='timebot_users',
                             Key={ 'slack_user': { 'S': slack_user } },
                             ProjectionExpression='slack_user, toggl_api_key, last_verified, last_checked')
    item = resp['Item']

    user = item['slack_user']['S']
    api_key = item['toggl_api_key']['S']
    verified = item['last_verified']['S']
    checked = item['last_checked']['S']

    user = User(user, api_key, verified, checked)

    return user

def hello_handler(command):
    user = command['user_name'][0]
    channel = command['channel_name'][0]
    text = command.get('text', '')[0]

    if text != '':
        if text == 'entries':
            bot_user = get_user(user)
            entries = bot_user.get_toggl_entries()
            if len(entries) > 0:
                entry_description = '#entries: ' + len(entries) + ' ' + entries[0]['description']
            else:
                entry_description = "no entries"
            return { 'response_type': 'in_channel',
                     'text': 'what entries, ' + bot_user.show() + ' ' + entry_description }
        else:
            api_key = text
            user = User(user, api_key, "never", "never")
            user.create_user()
            return { 'response_type': 'in_channel',
                     'text': 'User created!' }
                #    'attachments': [ generate_tweet_attachment(str(uid), text) ] }`
    else:
        return { 'response_type': 'ephemeral',
                 'text': "Hello world" }


#OLD STUFF


def generate_tweet_attachment(uid_string, tweet_text):
    return { 'title': "Position Dev @positiondev",
             'thumb_url': 'https://s3.amazonaws.com/misc.positiondev.com/Twitter-500x500.png',
             'text': tweet_text,
             'color': '#4099FF',
             'footer': 'Tweet id: ' + uid_string }

def prop_handler(command):
    user = command['user_name'][0]
    channel = command['channel_name'][0]
    text = command.get('text', '')[0]

    if text != '':
        api_key = text
        user = User(user, api_key, "never", "never")
        store_tweet(uid, text)
        return { 'response_type': 'in_channel',
                 'text': user + ' would like to tweet:',
                 'attachments': [ generate_tweet_attachment(str(uid), text) ] }
    else:
        return { 'response_type': 'ephemeral',
                 'text': "Please attach a tweet that you'd like to propose." }

def tweet_handler(command):
    user = command['user_name'][0]
    channel = command['channel_name'][0]
    text = command.get('text', '')[0]

    if text != '':
        uid = uuid.uuid4()
        store_tweet(uid, text)
        tweet_text = text
        tweet_uuid = str(uid)
    else:
        resp = dynamodb.get_item(TableName='tweets',
                                 Key={ 'uuid': { 'S': 'latest'} },
                                 ProjectionExpression='tweet_text, tweet_uuid')
        item = resp['Item']
        tweet_text = item['tweet_text']['S']
        tweet_uuid = item['tweet_uuid']['S']

    return { 'response_type': 'in_channel',
             'text': 'Are you sure you want to tweet this?',
             'attachments': [ generate_tweet_attachment(tweet_uuid, tweet_text),
                              { 'title': 'Yes, tweet it!',
                                'title_link': 'https://pwz6r8tpo0.execute-api.us-east-1.amazonaws.com/test/tweet?uuid=' + tweet_uuid,
                                'color': 'good' } ] }
