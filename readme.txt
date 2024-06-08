程序运行环境：python3.12、numpy3.12

简单说明：tcpserver_v1_1使用超时和循环机制处理客户端的连接，使用多线程来处理每个客户端；tcpserver_v1_2.py 使用select来监听连接，但仍使用多线程来处理每个客户端；tcpserver_v2_2.py使用非阻塞单线程多路复用I/O，用select监听连接，管理连接列表socket_links；tcpserver_v2_2.py使用更高级的selectors，相较于select，简化了操作。
tcpclient.py 没有变化。

ps：单纯只是想尝试多种写法，各版本之间的代码差异其实不大。

client 命令行输入<filename> <server_ip> <server_port> <len_min> <len_max> <mode>。mode为数据的方式：lowercase/ reverse / uppercase/ capitalize。

server 命令行指定端口号。


测试输入：
1. tcpserver_v1_1.py 
    python tcpserver_v1_1.py 50007
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 150 250 lowercase
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 100 200 uppercase

2. tcpserver_v1_2.py 
    python tcpserver_v1_2.py 50007
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 200 240 lowercase
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 100 200 capitalize

3. tcpserver_v2_1.py 
    python tcpserver_v2_1.py 50007
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 100 200 reverse
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 100 200 uppercase

4. tcpserver_v2_2.py
    python tcpserver_v2_2.py 50007
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 200 300 lowercase
    python tcpclient.py D:/桌面/test01.txt 127.0.0.1 50007 100 200 uppercase

4. tcpserver_v2_2.py下的500MB大文件处理
    python tcpserver_v2_2.py 50007
    python tcpclient.py D:/桌面/500MB_ASCII_File.txt 127.0.0.1 50007 100000 120000 lowercase

