#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <cstdlib>
#include <iostream>

int main() {
  // socket()
  char buf[256] = {};
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if(sockfd == -1) {
    std::cerr << "socket failure" << std::endl;
    exit(1);
  }

  // connect info
  sockaddr_in client;
  bzero(&client, sizeof(client));
  client.sin_family = AF_INET;
  client.sin_addr.s_addr = inet_addr("127.0.0.1");
  client.sin_port = htons(9047);
    
  // connect()
  if(connect(sockfd, (sockaddr*)&client, sizeof(client)) == -1) {
    std::cerr << "connection error" << std::endl;
    exit(1);
  }

  while(true) {
    recv(sockfd, buf, sizeof(buf), 0);
    std::cout << buf << std::endl;
    if(strcmp(buf, "END") == 0) break;
    std::cin >> buf;
    send(sockfd, buf, sizeof(buf), 0);
    if(strcmp(buf, "END") == 0) break;
  }

  // close()
  close(sockfd); 

  return 0;
}
