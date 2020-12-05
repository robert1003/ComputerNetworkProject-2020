
## Persistent HTTP

I added `Connection: Keep-Alive` in the header to keep the socket alive. This slightly reduces the loading time of the webpage as the number of Connecting/TLS setup decreases (the setup is only needed when establishing a socket connection).

## Message Board and Register/Login/Logout

* I used [MongoDB](https://www.mongodb.com) as my database to store cookies, users and messages. 
* The cookies are set as with appropriate expire time, and both `Secure` option and `HttpOnly` option are turned on to prevent cookies being stolen by attacks like [XSS](https://en.wikipedia.org/wiki/Cross-site_scripting) or [MITM](https://en.wikipedia.org/wiki/Man-in-the-middle_attack).

## HTTPS

### Package

Python `ssl` package

### Certificate

I use [Let's Encrypt](https://letsencrypt.org) to create and sign the certificate for me.

```
sudo add-apt-repository ppa:certbot/certbot
sudo apt update
sudo apt install certbot
certbot certonly
# fill in requested fields
# leave 80 port open for validation
# (it needs to check that you own the server with the correspond domain name)
# Done!
```
