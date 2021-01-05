# Computer Network Project Phase 2 - Setup

```
pip install -r requirement.txt
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
    -subj "/C=TW/ST=Taipei/L=Taipei/O=Test/CN=Test" \
    -keyout privkey.pem  -out fullchain.pem
python3 init_db.py
sudo iptables -A PREROUTING -t nat -p tcp --dport 443 -j REDIRECT --to-port 8080
echo "start server"
python3 server.py
```

# Computer Network Project Phase 2 - Features

Currently support only Chrome and Firefox.

## Message Board and Register/Login/Logout

* I used [MongoDB](https://www.mongodb.com) as my database to store cookies, users, messages and video meta informations. 
* The cookies are set as with appropriate expire time, and both `Secure` option and `HttpOnly` option are turned on to prevent cookies being stolen by attacks like [XSS](https://en.wikipedia.org/wiki/Cross-site_scripting) or [MITM](https://en.wikipedia.org/wiki/Man-in-the-middle_attack). I also turned on `SameSite=strict` to prevent [CSRF](https://blog.techbridge.cc/2017/02/25/csrf-introduction/) attack ([SameSite cookie ref](https://web.dev/samesite-cookies-explained/)).

## Async I/O and Persistent HTTP(S)

I used asynchronous I/O to let server handle multiple socket connection at once. I added `Connection: Keep-Alive` in the header to keep the socket alive (persistent HTTP(S)). This reduces the time spent on establishing TLS secure connection, and save lots of time when performing video streaming.

## HTTPS

### Package

Python `ssl` package

### Certificate

I use [Let's Encrypt](https://letsencrypt.org) to create and sign the certificate for me.

```bash
sudo add-apt-repository ppa:certbot/certbot
sudo apt update
sudo apt install certbot
certbot certonly
# fill in requested fields
# leave 80 port open for validation
# (it needs to check that you own the server with the correspond domain name)
# Done!
```

## Video (and sound) streaming

I used [DASH](https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP) streaming for my video player.

### Server side preparation

Suppose you want to stream `demo.mp4`:

```bash
# install package ffmpeg and MP4Box first
# generate auto file
ffmpeg -y -i "demo.mp4" -c:a aac -b:a 192k -vn "demo_audio.m4a"
# generate video file with different maxrate, browser will choose the most suitable rate considering the network connection.
ffmpeg -y -i "demo.mp4" -preset slow -tune film -vsync passthrough -an -c:v libx264 -x264opts 'keyint=25:min-keyint=25:no-scenecut' -crf 22 -maxrate 5000k -bufsize 12000k -pix_fmt yuv420p -f mp4 "demo_5000.mp4"
ffmpeg -y -i "demo.mp4" -preset slow -tune film -vsync passthrough -an -c:v libx264 -x264opts 'keyint=25:min-keyint=25:no-scenecut' -crf 23 -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -f mp4  "demo_3000.mp4"
ffmpeg -y -i "demo.mp4" -preset slow -tune film -vsync passthrough -an -c:v libx264 -x264opts 'keyint=25:min-keyint=25:no-scenecut' -crf 23 -maxrate 1500k -bufsize 3000k -pix_fmt yuv420p -f mp4   "demo_1500.mp4"
ffmpeg -y -i "demo.mp4" -preset slow -tune film -vsync passthrough -an -c:v libx264 -x264opts 'keyint=25:min-keyint=25:no-scenecut' -crf 23 -maxrate 800k -bufsize 2000k -pix_fmt yuv420p -vf "scale=-2:720" -f mp4  "demo_800.mp4"
ffmpeg -y -i "demo.mp4" -preset slow -tune film -vsync passthrough -an -c:v libx264 -x264opts 'keyint=25:min-keyint=25:no-scenecut' -crf 23 -maxrate 400k -bufsize 1000k -pix_fmt yuv420p -vf "scale=-2:540" -f mp4  "demo_400.mp4"
# generate MPD file, which is a manifest file for DASH streaming
MP4Box -dash 2000 -rap -frag-rap  -bs-switching no -profile "dashavc264:live" "demo_5000.mp4" "demo_3000.mp4" "demo_1500.mp4" "demo_800.mp4" "demo_400.mp4" "demo_audio.m4a" -out "demo/demo.mpd"
```

### Client side preparation

You can the official DASH client js script implementation: [github](https://github.com/Dash-Industry-Forum/dash.js)

```html
<video data-dashjs-player width="960" height="540" autoplay="false" controls>
    <source src="path to demo.mp4" type="application/dash+xml">
</video>
<!-- add this to the bottom of <body></body> -->
<script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
```
