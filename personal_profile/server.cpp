#include <sys/socket.h>
#include <cstdio>
#include <netinet/in.h>
#include <cstring>
#include <string>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <map>
#include <sys/ioctl.h>
#include <boost/algorithm/string.hpp>

std::map<std::string, std::string> parse_http_header(char* s) {
  std::map<std::string, std::string> m;
  std::istringstream ss(s);
  // GET / HTTP/1.1
  std::string method, path, http_version;
  ss >> method >> path >> http_version;
  m["method"] = method; m["path"] = path; m["http_version"] = http_version;
  // other headers
  std::string header;
  std::getline(ss, header);
  int index;
  while(std::getline(ss, header) && header != "\r") {
    index = header.find(':', 0);
    if(index != std::string::npos) {
      m[boost::algorithm::trim_copy(header.substr(0, index))] = \
        boost::algorithm::trim_copy(header.substr(index + 1));
    }
  }

  return m;
}

int main() {
  // socket()
  char buf[1024] = {};
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if(sockfd == -1) {
    std::cerr << "socket fail" << std::endl;
    exit(1);
  }

  // bind info
  sockaddr_in server;
  bzero(&server, sizeof(server));
  server.sin_family = AF_INET;
  server.sin_addr.s_addr = INADDR_ANY;
  server.sin_port = htons(80);

  // bind()
  if(bind(sockfd, (sockaddr*)&server, sizeof(server)) < 0) {
    std::cerr << "failed to bind port 80" << std::endl;
    exit(1);
  };

  // listen()
  listen(sockfd, 1);
  std::cerr << "start listening..." << std::endl;

  while(true) {
    sockaddr_in client;
    socklen_t addrlen = sizeof(client);
    // accept()
    int clientfd = accept(sockfd, (sockaddr*)&client, &addrlen);
    // recv
    int count;
    ioctl(clientfd, FIONREAD, &count);
    std::cerr << "Count: " << count << std::endl;
    if(count > 0) {
      recv(clientfd, buf, sizeof(buf), 0);
      std::cerr << "Request:\n" << std::string(buf) << std::endl;
      auto m = parse_http_header(buf);
      if(m["method"] == "GET" && m["path"] == "/") {
        char resp[] = "HTTP/1.1 200 OK\r\nConnection: Closed\r\nContent-Type: text/html\r\n\r\n<html><meta charset=\"utf-8\"/><h1>Profile of b07902047 羅啟帆</h1><ul><li>Name: 羅啟帆</li><li>Id: B07902047</li><li>Education: National Taiwan Unversity Computer Science and Information Engineering</li><li>Motto: Giver is so strong.</li></html>\r\n\r\n";
        std::cerr << "Reponse:\n" << std::string(resp) << std::endl;
        // send
        send(clientfd, resp, sizeof(resp), 0);
      }
      else {
        char resp[] = "HTTP/1.1 404 Not Found\r\nConnection: Closed\r\nContent-Type: text/html\r\n\r\n";
        std::cerr << "Reponse:\n" << std::string(resp) << std::endl;
        // send
        send(clientfd, resp, sizeof(resp), 0);
      }
    }
    shutdown(clientfd, SHUT_RDWR);
    sleep(1);
    close(clientfd);
  }

  return 0;
}
