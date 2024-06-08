import socket
import selectors
import threading
import sys
import time

sel = selectors.DefaultSelector()  # 创建默认选择器对象，用于处理多路复用I/O
is_running = True  # 控制服务器的运行状态
client_info = {}  # 存储所有客户端的信息，key为client_socket，value为{N,mode}
mode_type = {
    1: 'reverse',
    2: 'uppercase',
    3: 'lowercase',
    4: 'capitalize'
}


# 确保读取固定数量的字节的函数
def recv_all(sock, num_bytes):
    buffer = b''
    while len(buffer) < num_bytes:
        try:
            data = sock.recv(num_bytes - len(buffer))
            if not data:
                raise ConnectionError("Connection closed")
            buffer += data
        except BlockingIOError:
            # 非阻塞模式下没有数据可读时会抛出该异常
            continue
    return buffer


# 建立与客户端的连接
def tcp_client_build_link(client_socket, mask):
    # 获取客户端地址
    client_address = client_socket.getpeername()
    try:
        # 如果有可读事件
        if mask & selectors.EVENT_READ:
            # 接收Initialization报文
            data = recv_all(client_socket, 7)
            # 检查报文长度和类型
            if len(data) == 7 and data[:2] == b'\x00\x01':
                # 提取N和mode
                N = int.from_bytes(data[2:6], byteorder='big')
                mode = data[6]
                mode_str = mode_type.get(mode, 'unknown')
                print(f"Initialization received: N={N}, Mode={mode_str}")

                # 发送agree报文
                client_socket.sendall(b'\x00\x02')

                # 保存mode和N到附加信息
                client_info[client_socket] = {'mode': mode, 'N': N}

                # 修改可读事件
                sel.modify(client_socket, selectors.EVENT_READ, data_process)
    except Exception as e:
        # 处理异常情况
        sel.unregister(client_socket)  # 异常，注销可读事件
        client_socket.close()
        if client_socket in client_info:
            del client_info[client_socket]


def data_process(client_socket, mask):
    # 获取客户端地址
    client_address = client_socket.getpeername()
    try:
        # 如果有可读事件
        if mask & selectors.EVENT_READ:
            # 处理reverseRequest报文
            header = recv_all(client_socket, 6)
            # 检查报文长度和类型
            if len(header) == 6 and header[:2] == b'\x00\x03':
                # 提取数据长度和内容
                length = int.from_bytes(header[2:6], byteorder='big')
                content = recv_all(client_socket, length).decode('ansi')

                # 根据模式处理内容
                mode = client_info[client_socket]['mode']  # 使用保存的mode
                if mode == 1:  # reverse
                    processed_content = content[::-1]
                elif mode == 2:  # uppercase
                    processed_content = content.upper()
                elif mode == 3:  # lowercase
                    processed_content = content.lower()
                elif mode == 4:  # capitalize
                    processed_content = content.title()

                # 发送reverseAnswer报文
                response = b'\x00\x04' + len(processed_content).to_bytes(4, byteorder='big') + processed_content.encode(
                    'ansi')
                client_socket.sendall(response)
            else:
                print("Invalid reverseRequest message format")
    except Exception as e:
        # 处理异常情况
        mode = client_info[client_socket]['mode']  # 使用保存的mode

        print(f"Error reading client {client_address}: {e}")
        sel.unregister(client_socket)
        client_socket.close()

        if client_socket in client_info:
            del client_info[client_socket]

        mode_str = mode_type.get(mode, 'unknown')
        print(f"来自客户端 {client_address} 的 {mode_str} 处理已完成。")
        print(f"来自客户端 {client_address} 的连接已关闭。")


def accept_clients(sock, mask):
    # 接受新的客户端连接
    client_socket, client_address = sock.accept()
    print(f"----接受来自 {client_address} 的连接----")
    client_socket.setblocking(False)  # 将客户端套接字设置为非阻塞
    # 初始化附加信息字典
    client_info[client_socket] = {}
    # 注册可读事件
    sel.register(client_socket, selectors.EVENT_READ, tcp_client_build_link)


# 监听命令行的exit
def listen_for_exit():
    global is_running
    while True:
        cmd = input()
        if cmd.strip().lower() == 'exit':
            print("关闭客户端...")
            is_running = False
            sel.close()
            break
        else:
            print("无效命令！")
        time.sleep(1)  # 休眠1秒，减轻资源的损耗


# 启动 TCP 服务器，处理多个客户端
def start_server(port):
    global is_running
    try:
        # 创建服务器套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', port))  # 绑定指定端口，绑定到 '0.0.0.0' 用于在所有网络接口上监听连接
        server_socket.listen(6)  # 监听连接请求，最多监听6个客户端

        server_socket.setblocking(False)  # 设置服务器为非阻塞

        # 启动一个线程来监听exit命令
        print("输入 exit 可以关闭服务器")
        exit_listener = threading.Thread(target=listen_for_exit)
        exit_listener.start()

        # 注册服务器套接字的可读事件
        sel.register(server_socket, selectors.EVENT_READ, accept_clients)
        print(f"服务器正在端口 {port} 上监听连接请求...")

        try:
            while is_running:
                # 使用select进行I/O多路复用，增加超时以便检查running状态
                events = sel.select(timeout=1)
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
        except KeyboardInterrupt:
            print("Server is shutting down.")
            is_running = False

    except OSError as e:
        # 如果端口号被占用，捕获 OSError 并显示错误信息
        if 'Address already in use' in str(e):
            print(f"端口 {port} 已被占用。请选择一个不同的端口。")
        else:
            print(f"服务器已关闭。")

    finally:
        sel.close()
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("参数不足！未指定端口号！")
    server_port = int(sys.argv[1])  # 端口号必须是整数

    # 启动服务器
    start_server(server_port)
