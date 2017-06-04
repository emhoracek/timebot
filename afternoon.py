from __future__ import print_function
import boto3

import json
import urllib
import urllib2
import urlparse
import base64
from datetime import datetime, timedelta

print('Loading function')

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    if 'trigger' in event:
        handle_trigger(event)
    else:
        bodyJson = event['body-json']
        command = urlparse.parse_qs(bodyJson, keep_blank_values = True)
        print(command['payload'][0])
        if 'payload' in command:
            payload = json.loads(command['payload'][0])
            return handle_button(payload)
        else:
            return hello_handler(command)

def handle_button(command):
    #print(command['original_message']['attachments'])
    slack_user = command['user']['name']
    user = get_user(slack_user)
    if command['callback_id'] == 'verify' and command['actions'][0]['value'] == 'yes':
        user.update_latest()
        return { "text": "Verified!", "replace_original": False }
    else:
        return "????"

def handle_trigger(event):
    slack_user = event['slack_user']
    user = get_user(slack_user)
    json_entries = user.get_toggl_entries()
    attachments = entry_attachments(json_entries)
    payload = json.dumps({"text": "Here's a summary of today's entries",
                          "icon_emoji": ":timer_clock:",
                          "attachments": attachments})
    req = urllib2.Request(user.webhook, payload)
    urllib2.urlopen(req).read()

class User(object):
    def __init__(self, slack_user, toggl_api_key, last_verified, last_checked, webhook):
        self.slack_user = slack_user
        self.toggl_api_key = toggl_api_key
        self.last_verified = last_verified
        self.last_checked = last_checked
        self.webhook = webhook

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

    def update_webhook(self, webhook_url):
        dynamodb.update_item(TableName='timebot_users',
                             Key={'slack_user': {'S': self.slack_user} },
                             UpdateExpression="SET webhook=:webhook",
                             ExpressionAttributeValues={':webhook': {'S': webhook_url }})

    def show(self):
        return self.slack_user + ' ' + self.last_checked + ' ' + self.last_verified

    def get_toggl_entries(self):
        username = self.toggl_api_key
        password = "api_token"
        base64string = base64.b64encode('%s:%s' % (username, password))
        start = urllib.quote(self.since_last_verified())
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
            date = self.last_verified
            #date = datetime.strptime(self.last_verified, "%Y-%m-%dT%H:%M:%S")
            #date = date.strftime("%Y-%m-%dT%H:%M:%S")
        return date + "-05:00"

def get_user(slack_user):
    resp = dynamodb.get_item(TableName='timebot_users',
                             Key={ 'slack_user': { 'S': slack_user } },
                             ProjectionExpression='slack_user, toggl_api_key, last_verified, last_checked, webhook')
    item = resp['Item']

    user = item['slack_user']['S']
    api_key = item['toggl_api_key']['S']
    verified = item['last_verified']['S']
    checked = item['last_checked']['S']
    webhook = item.get('webhook',{'S': 'none'}).get('S')

    user = User(user, api_key, verified, checked, webhook)

    return user

class TogglEntry(object):
    def __init__ (self, json):
        self.start = json['start']
        self.stop = json['stop']
        self.description = json.get('description', 'no description')
        self.duration = timedelta(seconds=int(json['duration']))

    def short_slack_format(self):
        return { "fields": [
                 { "value": self.description,
                   "short": "true"},
                 { "value": str(self.duration),
                   "short": "true" } ] }

    def long_slack_format(self):
        return { "fields": [
                 { "title": "Description",
                   "value": self.description,
                   "short": "true"},
                 { "title": "Duration",
                   "value": str(self.duration),
                   "short": "true" } ] }

def entry_attachments(entries):
    attachments = []
    if len(entries) > 0:
        first_entry = entries.pop()
        te = TogglEntry(first_entry)
        attachments.append(te.long_slack_format())

        for entry in entries:
            te = TogglEntry(entry)
            attachments.append(te.short_slack_format())
    attachments.append(verify_attachment())
    return attachments


def long_slack_format():
    return { "fields": [
             { "title": "Description",
               "value": 'hey',
               "short": "true"},
             { "title": "Duration",
               "value": 'yo',
               "short": "true" } ] }

def verify_attachment():
    return { "text": "Is this correct?",
             "fallback": "Use `/timebot yes` or `/timebot no`",
            "callback_id": "verify",
            "color": "#3AA3E3",
            "attachment_type": "default",
            'actions': [ {'name': 'yes',
                           'text': 'Yes',
                           'type': 'button',
                           'value': 'yes'},
                          {'name': 'no',
                           'text': 'No',
                           'type': 'button',
                           'value': 'no'} ] }

def hello_handler(command):
    user = command['user_name'][0]
    channel = command['channel_name'][0]
    text = command.get('text', '')[0]

    if text == 'entries':
        bot_user = get_user(user)
        entries = bot_user.get_toggl_entries()
        return { 'response_type': 'in_channel',
                 'text': "Here are your entries:",
                 'attachments': entry_attachments(entries) }
    elif text.startswith('hook '):
        webhook_url = text.split(' ')[1]
        bot_user = get_user(user)
        bot_user.update_webhook(webhook_url)
        return { 'response_type': 'in_channel',
                 'text': 'Webhook updated!'}
    elif text.startswith('add '):
        api_key = text.split(' ')[1]
        user = User(user, api_key, "never", "never", "none")
        user.create_user()
        return { 'response_type': 'in_channel',
                 'text': 'User created!' }
    else:
        return { 'response_type': 'ephemeral',
                 'text': "Hello world" }
