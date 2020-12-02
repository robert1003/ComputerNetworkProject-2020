import random
import string
from pymongo import MongoClient
from datetime import datetime, timedelta
from copy import deepcopy

conn = MongoClient()

content_type_mapping = {
        'html': 'text/html;charset=utf-8',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'jpg': 'image/jpeg'
    }

def get_content_type(name):
    if name not in content_type_mapping:
        return 'text/plain'
    else:
        return content_type_mapping[name]

def now(**kwargs):
    return (datetime.now() + timedelta(**kwargs)).astimezone().strftime('%a, %d %b %Y %H:%M:%S %Z')

def rand_string(k):
    return ''.join(random.choices(string.hexdigits, k=k))

def construct_response(status_code, message, connection, content_type, data, cookies={}):
    response = 'HTTP/1.1 {} {}\r\n'.format(status_code, message)
    response += 'Date: {}\r\n'.format(now())
    response += 'Connection: {}\r\n'.format(connection)
    if connection == 'Keep-Alive':
        response += 'Keep-Alive: timeout=5, max=1000\n'
    response += 'Content-Type: {}\r\n'.format(content_type)
    response += 'Content-Length: {}\r\n'.format(len(data))
    for k, v in cookies.items():
        response += 'Set-Cookie: {}={}; Expires={}; Secure; HttpOnly\r\n'.format(k, v, now(days=15))
    response += '\r\n'
    print(response)
    response = response.encode() + data
    
    return response

def add_cookies(cookies):
    session = conn['phase2']['session']
    cursor = session.insert_one(deepcopy(cookies))

def check_cookies(cookies):
    try:
        session = conn['phase2']['session']
        cursor = session.find(cookies)
        return cursor.count() == 1
    except Exception as e:
        print('Check cookie exception:', e)
        return False

