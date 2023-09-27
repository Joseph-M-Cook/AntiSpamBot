import sys
sys.path.insert(0, 'vendor')

import os
import requests
import random
import json
import requests
from bs4 import BeautifulSoup
import re    # regex


API_ROOT = 'https://api.groupme.com/v3/'
FLAGGED_PHRASES = (
    'essay written by professionals',
    'paper writing service',
    'academic writing service',
    'student paper assignments',
    'getting professional academic help from us is easy',
    'cutt.us',
    'inyurl.com/muxz7h',
)


def get_memberships(group_id, token):
    response = requests.get(f'{API_ROOT}groups/{group_id}', params={'token': token}).json()['response']['members']
    return response


def get_membership_id(group_id, user_id, token):
    memberships = get_memberships(group_id, token)
    for membership in memberships:
        if membership['user_id'] == user_id:
            return membership['id']


def remove_member(group_id, membership_id, token):
    response = requests.post(f'{API_ROOT}groups/{group_id}/members/{membership_id}/remove', params={'token': token})
    print('Tried to kick user, got response:')
    print(response.text)
    return response.ok


def delete_message(group_id, message_id, token):
    response = requests.delete(f'{API_ROOT}conversations/{group_id}/messages/{message_id}', params={'token': token})
    return response.ok


def kick_user(group_id, user_id, token):
    membership_id = get_membership_id(group_id, user_id, token)
    remove_member(group_id, membership_id, token)


def extract_urls(message):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, message)


def fetch_and_process_url(url):
    for url in urls:
        try:
            response = requests.get(url, timeout=10)  
            print(f"URL: {url} -> Status Code: {response.status_code}")

            return response
            
        except requests.RequestException as e:
            print(f"Error fetching URL: {url}. Error: {e}")
            
            return -1

def flagged(message, bot_id):
    kick_user(message['group_id'], message['user_id'], message['token'])
    delete_message(message['group_id'], message['id'], message['token'])
    send('Kicked ' + message['name'] + ' due to apparent spam post.', bot_id)


def receive(event, context):
    message = json.loads(event['body'])
    urls = extract_urls(message)
    
    bot_id = message['bot_id']
    # Process the original message
    for phrase in FLAGGED_PHRASES:
        if phrase in message['text'].lower():
            flagged(message, bot_id)
            break

    # Check the URL/s
    for url in urls:
        response = fetch_and_process_url(url)
        soup = BeautifulSoup(response.text)
        try:
            title = soup.find("meta",  property="og:title")
            description = soup.find("meta",  property="og:description")
            for phrase in FLAGGED_PHRASES:
                if phrase in description.lower() or phrase in title.lower():
                    flagged(message, bot_id)
                    break
                    
    return {
        'statusCode': 200,
        'body': 'ok'
    }


def send(text, bot_id):
    url = 'https://api.groupme.com/v3/bots/post'

    message = {
        'bot_id': bot_id,
        'text': text,
    }
    r = requests.post(url, json=message)
