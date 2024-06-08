import socket
import os
import random
import sys


def tcp_client(filename, server_ip, server_port, len_min, len_max, mode):
    try:
        # 以只读的方式打开文件
        with open(filename, 'r', encoding='ansi') as file:
            data = file.read()
    except IOError as e:
        print(f"无法读取文件 '{filename}'：{e}")
        sys.exit(1)

    # 数据分块
    blocks = []
    total_len = len(data)
    index = 0
    while index < total_len:
        block_size = random.randint(len_min, len_max)
        if index + block_size > total_len:
            block_size = total_len - index
        blocks.append(data[index:index + block_size])
        index += block_size

    N = len(blocks)

    try:
        # 创建TCP连接
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))
        client.settimeout(2)  # 设置超时时间，以防服务器无响应
    except socket.error as e:
        print(f"无法连接到服务器 {server_ip}:{server_port}：{e}")
        sys.exit(1)

    try:
        # 发送Initialization报文
        initialization_message = b'\x00\x01' + N.to_bytes(4, byteorder='big') + bytes([mode])
        client.sendall(initialization_message)

        # 接收agree报文
        try:
            agree_message = client.recv(2)
        except socket.timeout:
            print("等待服务器响应超时。")
            client.close()
            sys.exit(1)

        if agree_message != b'\x00\x02':
            print("Initialization报文未被server接收！")
            client.close()
            sys.exit(1)

        print("Initialization报文已被server接收。")
        processed_alldata = []  # 处理后的数据

        # 发送reverseRequest报文
        for i, block in enumerate(blocks):  # 序列解包列表，返回字典
            request_message = b'\x00\x03' + len(block).to_bytes(4, byteorder='big') + block.encode('ansi')
            client.sendall(request_message)

            # 接收reverseAnswer报文
            try:
                answer_header = client.recv(6)
            except socket.timeout:
                print(f"第 {i + 1} 块请求等待服务器响应超时。")
                continue

            if answer_header[:2] == b'\x00\x04':
                answer_len = int.from_bytes(answer_header[2:6], byteorder='big')
                processed_data = client.recv(answer_len).decode('ansi')
                print(f"第 {i + 1} 块: {processed_data}")
                if mode == 1:  # 反转的特殊处理
                    processed_alldata.insert(0, processed_data)
                else:
                    processed_alldata.append(processed_data)

        # 保存处理后的数据
        path = os.path.splitext(filename)[0]  # 获取不带扩展名的文件路径
        new_filename = path + "_" + process_type + ".txt"  # 生成新的文件名
        with open(new_filename, 'w', encoding='ansi') as file:
            file.write(''.join(processed_alldata))

        print(f"处理后的文件已保存为 '{new_filename}'")

    except socket.error as e:
        print(f"通信过程中出现错误：{e}")

    finally:
        # 关闭客户端连接
        client.close()


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("参数不足！ <filename> <server_ip> <server_port> <len_min> <len_max> <mode>")
        sys.exit(1)

    # 获取对应参数
    filename = sys.argv[1]
    server_ip = sys.argv[2]
    server_port = int(sys.argv[3])
    len_min = int(sys.argv[4])
    len_max = int(sys.argv[5])
    process_type = sys.argv[6]

    mode_map = {
        "reverse": 1,
        "uppercase": 2,
        "lowercase": 3,
        "capitalize": 4
    }

    # 判断处理方式是否存在
    if process_type not in mode_map:
        print(f"不存在的处理方式 '{process_type}' ！使用 'reverse', 'uppercase', 'lowercase', 'capitalize'")
        sys.exit(1)

    mode = mode_map[process_type]

    # 判断文件是否存在
    if not os.path.isfile(filename):
        print(f"文件 '{filename}' 不存在！")
        sys.exit(1)

    tcp_client(filename, server_ip, server_port, len_min, len_max, mode)
