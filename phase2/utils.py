import random
import string
from pymongo import MongoClient
from datetime import datetime, timedelta
from copy import deepcopy
from pathlib import Path

conn = MongoClient()

content_type_mapping = {
        'html': 'text/html;charset=utf-8',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'css': 'text/css',
        'ttf': 'font/ttf',
        'mov': 'video/mp4',
        'mp4': 'video/mp4',
        'mpd': 'application/dash+xml'
    }

def get_content_type(name):
    if name not in content_type_mapping:
        return 'text/plain'
    else:
        return content_type_mapping[name]

def now(**kwargs):
    return (datetime.now() + timedelta(**kwargs)).astimezone().strftime('%a, %d %b %Y %H:%M:%S %Z')

def to_datetime(s):
    return datetime.strptime(s, '%a, %d %b %Y %H:%M:%S %Z')

def rand_string(k):
    return ''.join(random.choices(string.hexdigits, k=k))

def construct_response(status_code, message, connection, content_type='', data=b'', cookies={}, erase_cookies={}, content_range='', **kwargs):
    response = 'HTTP/1.1 {} {}\r\n'.format(status_code, message)
    print(response, flush=True)
    response += 'Date: {}\r\n'.format(now())
    response += 'Connection: {}\r\n'.format(connection)
    #if connection == 'Keep-Alive':
    #    response += 'Keep-Alive: timeout=5, max=1000\n'
    if content_type:
        response += 'Content-Type: {}\r\n'.format(content_type)
    if data:
        response += 'Content-Length: {}\r\n'.format(len(data))
    if content_range:
        response += 'Content-Range: {} {}-{}/{}\r\n'.format(*content_range)
    for k, v in cookies.items():
        response += 'Set-Cookie: {}={}; Expires={}; Secure; HttpOnly;\r\n'.format(k, v, now(days=15))
    for k, v in erase_cookies.items():
        response += 'Set-Cookie: {}={}; Expires={}; Secure; HttpOnly;\r\n'.format(k, v, now(days=-15))
    for k, v in kwargs.items():
        response += '{}: {}\r\n'.format(k, v)
    response += '\r\n'
    response = response.encode() + data
    
    return response

def add_cookies(cookies):
    session = conn['phase2']['session']
    cursor = session.insert_one(deepcopy(cookies))

def check_cookies(cookies):
    try:
        session = conn['phase2']['session']
        cursor = session.find(cookies)
        if cursor.count() == 0:
            return False
        for cookie in cursor:
            if cookie['expires'] < to_datetime(now()):
                session.delete_one(cookies)
                return False
            else:
                return True
    except Exception as e:
        print('Check cookie exception:', e, flush=True)
        return False

def remove_cookies(cookies):
    session = conn['phase2']['session']
    session.delete_one(cookies)

def check_and_create_user(data):
    user = conn['phase2']['user']
    cursor1 = user.find(data)
    cursor2 = user.find({'user':data['user']})
    if cursor1.count() == 0:
        if cursor2.count() != 0:
            return {}
        else:
            result = user.insert_one(data)

    data = next(cursor1)
    cookies = {'sess_id':rand_string(16), 'user':data['_id'], 'expires': to_datetime(now(days=15))}
    add_cookies(cookies)
    return {'sess_id':cookies['sess_id']}

def get_username(cookies):
    session = conn['phase2']['session']
    user_id = next(session.find(cookies))['user']
    user = conn['phase2']['user']
    name = next(user.find({'_id':user_id}))['user']
    return name

def add_message(cookie, data):
    session = conn['phase2']['session']
    user_id = next(session.find(cookie))['user']
    message = conn['phase2']['message']
    data['user'] = user_id
    message.insert_one(data)

def get_message(cookie):
    session = conn['phase2']['session']
    user_id = next(session.find(cookie))['user']
    message = conn['phase2']['message']
    cursor = message.find({'user':user_id})
    messages = []
    for item in cursor:
        messages.append((item['title'], item['message']))
    return messages

def get_video_meta():
    video_meta = conn['phase2']['video_meta']
    cursor = video_meta.find()
    video_metas = []
    for item in cursor:
        video_metas.append((item['path'], item['title'], item['description']))
    return video_metas

def check_video_path(path):
    video_meta = conn['phase2']['video_meta']
    cursor = video_meta.find({'path':path});
    return cursor.count() == 1

def render(path, username='', messages=[], video_meta=[], video_path=''):
    if 'index.html' in path:
        front, mid, back = Path(path).read_text().split('{% tag %}')
        front = front.split('{% name %}')
        front = front[0] + front[1].format(username) + front[2]
        
        midd = ''
        for message in messages:
            midd += mid.format(*message)

        return (front + midd + back).encode()
    elif 'stream.html' in path:
        front, mid, back = Path(path).read_text().split('{% tag %}')
        front = front.split('{% video %}')
        if video_path:
            front = front[0] + front[1].format(video_path) + front[3]
        else:
            front = front[0] + front[2] + front[3]

        midd = ''
        for idx, meta in enumerate(video_meta):
            midd += mid.format(idx, idx, meta[1], meta[0], idx, idx, meta[2])

        return (front + midd + back).encode()
    else:
        return Path(path).read_bytes()
