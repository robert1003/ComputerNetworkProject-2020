import os
import asyncore
import utils
import urllib.parse
import ssl
import datetime

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
cert_folder = "/etc/letsencrypt/live/phase2.giversostrong.ninja/"
certfile = os.path.join(cert_folder, 'fullchain.pem')
keyfile = os.path.join(cert_folder, 'privkey.pem')
context.load_cert_chain(certfile=certfile, keyfile=keyfile) 

class HTTPHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        request = self.recv(8192).decode()
        if request:
            headers, data = request.split('\r\n\r\n')
            if data:
                data = dict(map(lambda x: tuple(map(urllib.parse.unquote, x.split('='))), data.split('&')))
            headers = headers.split('\r\n')
            print(datetime.datetime.now())
            print(headers[0], flush=True)
            method, path, http_version = headers[0].split(' ')
            headers = {key.strip():val.strip() for key, val in map(lambda x: x.split(': '), headers[1:])}
            headers['method'] = method
            headers['path'] = path
            headers['http_version'] = http_version
            if 'Cookie' in headers:
                headers['Cookie'] = dict(map(lambda x: x.split('='), headers['Cookie'].replace(' ', '').split(';')))

            if method == 'GET':
                if self.handle_get(headers, data) == 303:
                    self.close()
            elif method == 'POST':
                if self.handle_post(headers, data) == 303:
                    self.close()
            else:
                self.send(utils.construct_response(501, 'Not Implemented', 'close', utils.render('template_html/501.html')))
            '''
            elif method == 'DELETE':
                self.handle_delete(headers, data)
            '''
        else:
            self.close()

    def handle_get(self, headers, data):
        route = {'/':{True:'/me',False:'/login'}}
        files = {'/me': './index.html', '/login': './login.html', '/stream': './stream.html', '/assets': './assets'}
        path = headers['path'].replace('..', '.')
        have_cookie = True
        if 'Cookie' not in headers or 'sess_id' not in headers['Cookie'] or not utils.check_cookies({'sess_id':headers['Cookie']['sess_id']}):
            have_cookie = False

        if path in route:
            self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location=route[path][have_cookie]))
            return 303

        if not have_cookie and path != '/login' and any([path.startswith(f) for f in files]):
            self.send(utils.construct_response(403, 'Forbidden', 'Close', utils.get_content_type('html'), utils.render('template_html/403.html')))
            return 403

        if path == '/me':
            messages = utils.get_message(headers['Cookie'])
            username = utils.get_username(headers['Cookie'])
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('./index.html', username=username, messages=messages)))
            return 200
        elif path == '/stream':
            video_meta = utils.get_video_meta()
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('./stream.html', video_meta=video_meta)))


        if path in files:
            path = files[path]
        else:
            path = '.' + path

        if not os.path.isfile(path):
            self.send(utils.construct_response(404, 'Not Found', 'close', utils.get_content_type('html'), utils.render('template_html/404.html')))
            return 404
        else:
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type(path.split('.')[-1]), utils.render(path)))
            return 200

        return 0

    def handle_post(self, headers, data):
        if headers['path'] == '/login':
            cookies = utils.check_and_create_user(data)
            if cookies:
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', cookies=cookies, location='/me'))
                return 303
            else:
                self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('login_error.html')))
                return 200
        else:
            if 'Cookie' not in headers or 'sess_id' not in headers['Cookie'] or not utils.check_cookies({'sess_id':headers['Cookie']['sess_id']}):
                self.send(utils.construct_response(403, 'Forbidden', 'Close', utils.get_content_type('html'), utils.render('template_html/403.html')))
                return 403
            if headers['path'] == '/me':
                utils.add_message(headers['Cookie'], data)
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location='/me'))
                return 303
            elif headers['path'] == '/logout':
                utils.remove_cookies(headers['Cookie'])
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location='/login', erase_cookies=headers['Cookie']))
                return 303
            elif headers['path'] == '/stream':
                video_path = data['video']
                if not utils.check_video_path(video_path):
                    self.send(utils.construct_response(404, 'Not Found', 'close', utils.get_content_type('html'), utils.render('template_html/404.html')))
                    return 404
                video_meta = utils.get_video_meta()
                self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('./stream.html', video_meta=video_meta, video_path=video_path)))
                return 200

        return 0

    def handle_delete(self, headers, data):
        pass

class HTTPServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(100)

    def handle_accepted(self, sock, addr):
        try:
            print('Incoming connection from {}'.format(repr(addr)), flush=True)
            handler = HTTPHandler(context.wrap_socket(sock, server_side=True))
        except Exception as e:
            print(e, flush=True)


server = HTTPServer('0.0.0.0', 443)
asyncore.loop()
