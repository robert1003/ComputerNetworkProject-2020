from pymongo import MongoClient
import hashlib

conn = MongoClient()

def add_sample_user():
    user = conn['phase2']['user']
    data = {'user': 'test', 'pass': '123'}
    data['pass'] = hashlib.sha256(data['pass'].encode()).hexdigest()
    result = user.insert_one(data)
    print('added user with username "test" and password "123"')

def add_sample_message():
    user = conn['phase2']['user']
    message = conn['phase2']['message']
    user_id = next(user.find({'user':'test'}))['_id']
    data = {'user': user_id, 'title': 'Computer Network Phase2', 'message': 'This is an example message.'}
    result = message.insert_one(data)
    print('added 1 message for user "test"')

def add_sample_video_meta():
    video_meta = conn['phase2']['video_meta']
    data = {'path': '/assets/video/demo_phase1/demo_phase1.mpd', 'title': 'Phase1 demo video:', 'description': 'demo video of computer network project phase 1'}
    result = video_meta.insert_one(data)
    print('added 1 video')

if __name__ == '__main__':
    add_sample_user()
    add_sample_message()
    add_sample_video_meta()
