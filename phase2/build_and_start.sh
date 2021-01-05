#!/bin/bash
pip install -r requirement.txt
# optional: generate temporary key file
#openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
#    -subj "/C=TW/ST=Taipei/L=Taipei/O=Test/CN=Test" \
#    -keyout privkey.pem  -out fullchain.pem
python3 init_db.py
sudo iptables -A PREROUTING -t nat -p tcp --dport 443 -j REDIRECT --to-port 8080
echo "start server"
python3 server.py
