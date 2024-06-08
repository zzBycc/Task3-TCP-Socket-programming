import socket
import sys
import threading
import time
import select

is_running = True  # 控制监听客户端连接线程
mode_type = {
    1: 'reverse',
    2: 'uppercase',
    3: 'lowercase',
    4: 'capitalize'
}


def tcp_client_link(client_socket, client_address):
    try:
        # 接收Initialization报文
        data = client_socket.recv(7)
        if len(data) == 7 and data[:2] == b'\x00\x01':
            N = int.from_bytes(data[2:6], byteorder='big')
            mode = data[6]
            mode_str = mode_type.get(mode, 'unknown')
            print(f"Initialization received: N={N}, Mode={mode_str}")

            # 发送agree报文
            client_socket.sendall(b'\x00\x02')

        # 处理reverseRequest报文
        for _ in range(N):
            header = client_socket.recv(6)
            if len(header) >= 6 and header[:2] == b'\x00\x03':
                length = int.from_bytes(header[2:6], byteorder='big')
                data = client_socket.recv(length).decode()

                # 根据模式处理内容，python 没有 switch case
                if mode == 1:  # reverse
                    processed_data = data[::-1]
                elif mode == 2:  # uppercase
                    processed_data = data.upper()
                elif mode == 3:  # lowercase
                    processed_data = data.lower()
                elif mode == 4:  # capitalize
                    processed_data = data.title()

                # 发送reverseAnswer报文
                response = b'\x00\x04' + len(processed_data).to_bytes(4, byteorder='big') + processed_data.encode()
                client_socket.sendall(response)
            else:
                print("reverseRequest 报文格式错误！")

    finally:
        # 关闭连接
        client_socket.close()
        print(f"来自客户端 {client_address} 的 {mode_str} 处理已完成。")
        print(f"来自客户端 {client_address} 的连接已关闭。")


def listen_for_exit(server_socket):
    global is_running
    while True:
        cmd = input()
        if cmd.strip().lower() == 'exit':
            print("关闭服务器...")
            is_running = False
            server_socket.close()  # 关闭服务器套接字，触发select中的异常处理
            break
        else:
            print("无效命令！")
        time.sleep(1)  # 休眠1秒，减轻资源的损耗


# 用来接收客户端连接的线程
def accept_clients(server_socket):
    global is_running
    socket_links = [server_socket]
    while is_running:

        readable, _, _ = select.select(socket_links, [], [], 1.0)  # 1秒超时，以便定期检查running状态
        for s in readable:
            if s is server_socket:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"----接受来自 {client_address} 的连接----")
                    client_thread = threading.Thread(target=tcp_client_link, args=(client_socket, client_address))
                    client_thread.start()
                except OSError:
                    break  # 服务器关闭

    print("停止接受新的客户端连接")


# 启动 TCP 服务器，处理多个客户端
def start_server(port):
    try:
        # 创建服务器套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 绑定指定端口，绑定到 '0.0.0.0' 用于在所有网络接口上监听连接
        server_socket.bind(('0.0.0.0', port))

        # 监听连接请求，最多监听6个客户端
        server_socket.listen(6)
        print(f"服务器正在端口 {port} 上监听连接请求...")

        # 启动一个线程来监听exit命令
        print("输入 exit 可以关闭服务器")
        exit_listener = threading.Thread(target=listen_for_exit, args=(server_socket,))
        exit_listener.start()

        # 启动一个线程来接受客户端连接
        accept_thread = threading.Thread(target=accept_clients, args=(server_socket,))
        accept_thread.start()

        # 等待accept_thread完成
        accept_thread.join()

    except OSError as e:
        # 如果端口号被占用，捕获 OSError 并显示错误信息
        if 'Address already in use' in str(e):
            print(f"端口 {port} 已被占用。请选择一个不同的端口。")
        else:
            print(f"服务器已关闭。")

    finally:
        # 关闭服务器套接字
        try:
            server_socket.close()
        except OSError:
            pass


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("参数不足！未指定端口号！")
        sys.exit(1)

    server_port = int(sys.argv[1])  # 端口号必须是整数

    # 启动服务器
    start_server(server_port)
