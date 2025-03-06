import socket
import sys

def send_wol(broadcast_ip='255.255.255.255', port=9):
    mac = "60:CF:84:A4:30:02"
    # 将 MAC 地址转换为字节
    mac_bytes = bytes.fromhex(mac.replace(':', ''))
    # 构造魔术包：6字节 FF + 16次 MAC 地址
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    # 发送 UDP 广播包
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, port))
    print(f"已发送 WOL 魔术包至 {mac}")

if __name__ == '__main__':
    send_wol()
