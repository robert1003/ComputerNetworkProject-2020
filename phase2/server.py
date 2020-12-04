import os
import asyncore
import utils
import urllib.parse
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(certfile="host.crt", keyfile="host.key")

class HTTPHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        request = self.recv(8192).decode()
        if request:
            print(request)
            headers, data = request.split('\r\n\r\n')
            if data:
                data = dict(map(lambda x: tuple(map(urllib.parse.unquote, x.split('='))), data.split('&')))
            headers = headers.split('\r\n')
            method, path, http_version = headers[0].split(' ')
            headers = {key.strip():val.strip() for key, val in map(lambda x: x.split(': '), headers[1:])}
            headers['method'] = method
            headers['path'] = path
            headers['http_version'] = http_version
            if 'Cookie' in headers:
                headers['Cookie'] = dict(map(lambda x: x.split('='), headers['Cookie'].replace(' ', '').split(';')))

            if method == 'GET':
                self.handle_get(headers, data)
            elif method == 'POST':
                self.handle_post(headers, data)
            else:
                self.send(utils.construct_response(501, 'Not Implemented', 'close', utils.render('template_html/501.html')))
            '''
            elif method == 'DELETE':
                self.handle_delete(headers, data)
            '''

        self.close()

    def handle_get(self, headers, data):
        route = {'/':{True:'/me',False:'/login'}}
        files = {'/me': './index.html', '/login': './login.html'}
        path = headers['path'].replace('..', '.')
        have_cookie = True
        if 'Cookie' not in headers or 'sess_id' not in headers['Cookie'] or not utils.check_cookies({'sess_id':headers['Cookie']['sess_id']}):
            have_cookie = False

        if path in route:
            self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location=route[path][have_cookie]))
            return

        if not have_cookie and path != '/login' and path in files:
            self.send(utils.construct_response(403, 'Forbidden', 'Close', utils.get_content_type('html'), utils.render('template_html/403.html')))
            return

        if path == '/me':
            messages = utils.get_message(headers['Cookie'])
            username = utils.get_username(headers['Cookie'])
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('./index.html', username=username, messages=messages)))
            return

        if path in files:
            path = files[path]
        else:
            path = '.' + path

        if not os.path.isfile(path):
            self.send(utils.construct_response(404, 'Not Found', 'close', utils.get_content_type('html'), utils.render('template_html/404.html')))
        else:
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type(path.split('.')[-1]), utils.render(path)))

    def handle_post(self, headers, data):
        if headers['path'] == '/login':
            cookies = utils.check_and_create_user(data)
            if cookies:
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', cookies=cookies, location='/me'))
            else:
                self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type('html'), utils.render('login_error.html')))
        else:
            if 'Cookie' not in headers or 'sess_id' not in headers['Cookie'] or not utils.check_cookies({'sess_id':headers['Cookie']['sess_id']}):
                self.send(utils.construct_response(403, 'Forbidden', 'Close', utils.get_content_type('html'), utils.render('template_html/403.html')))
                return
            if headers['path'] == '/me':
                utils.add_message(headers['Cookie'], data)
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location='/me'))
            elif headers['path'] == '/logout':
                utils.remove_cookies(headers['Cookie'])
                self.send(utils.construct_response(303, 'See Other', 'Keep-Alive', location='/login', erase_cookies=headers['Cookie']))

        return

    def handle_delete(self, headers, data):
        pass

class HTTPServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        try:
            print('Incoming connection from {}'.format(repr(addr)))
            handler = HTTPHandler(context.wrap_socket(sock, server_side=True))
        except Exception as e:
            print(e)


server = HTTPServer('0.0.0.0', 443)
asyncore.loop()
