#include <sys/socket.h>
#include <netinet/in.h>
#include <cstring>
#include <cstdlib>
#include <iostream>

int main() {
  // socket()
  char buf[256] = {};
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
  server.sin_port = htons(9047);

  // bind()
  bind(sockfd, (sockaddr*)&server, sizeof(server));

  // listen()
  listen(sockfd, 1);

  while(true) {
    sockaddr_in client;
    socklen_t addrlen = sizeof(client);
    // accept()
    int clientfd = accept(sockfd, (sockaddr*)&client, &addrlen);
    // send
    std::cin >> buf;
    send(clientfd, buf, sizeof(buf), 0);
    if(strcmp(buf, "END") == 0) break;
    // recv
    recv(clientfd, buf, sizeof(buf), 0);
    std::cout << buf << std::endl;
    if(strcmp(buf, "END") == 0) break;
  }

  return 0;
}
