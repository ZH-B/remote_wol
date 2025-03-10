import json
import os
import re
import requests
import time
import sys
from datetime import datetime
import host_nat

process_lock_file = "~/.webmonitor.lock"

class WeiboMonitor:
    def __init__(self, config_path="config.json"):
        self.load_config(config_path)
        self.latest_mid = None
        self.load_last_state()
        self.next_check = time.time()

    def load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def load_last_state(self):
        if os.path.exists("last_mid.txt"):
            with open("last_mid.txt", 'r') as f:
                self.latest_mid = f.read().strip()

    def save_last_state(self, mid):
        self.latest_mid=mid
        with open("last_mid.txt", 'w') as f:
            f.write(mid)

    def fetch_weibo(self):
        """ 请求微博API """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
            'Cookie': self.config['cookie']
        }
        params = {
            'type': 'uid',
            'value': self.config['uid'],
            'containerid': f'107603{self.config["uid"]}'
        }
        try:
            response = requests.get(
                'https://m.weibo.cn/api/container/getIndex',
                headers=headers,
                params=params
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"[Error] API请求失败: {e}")
            return None

    def parse_weibo(self, data):
        """ 解析微博数据 """
        if not data or data.get('ok') != 1:
            print("data not ok")
            return []
        
        cards = data['data'].get('cards', [])
        weibos = []
        for card in cards:
            if card.get('card_type') == 9:  # 仅处理原创/转发微博
                mblog = card.get('mblog', {})
                mid = mblog.get('mid')
                text = mblog.get('text', '')
                # 清理HTML标签
                text = re.sub(r'<[^>]+>', '', text)
                weibos.append({'mid': mid, 'text': text})
        return weibos

    def check_new_weibo(self):
        """ 核心检测逻辑 """
        print('check new weibo')
        data = self.fetch_weibo()
        #print(data)
        if not data:
            print('not data')
            return

        weibos = self.parse_weibo(data)
        if not weibos:
            print('notweibo')
            return

        latest = weibos[0]
        if not self.latest_mid or latest['mid'] != self.latest_mid:
            print(f"[{datetime.now()}] 发现新微博: {latest['text'][:30]}...")
            
            if re.search(self.config['keyword'], latest['text'], re.I):
                self.execute_WOL()
                
            self.save_last_state(latest['mid'])
        else:
            print(f"没有找到新的微博 lastmid{self.latest_mid}")

        print('check new weibo done')

    def execute_WOL(self):
        host_nat.send_wol(self.config['mac'])
        self.next_check = time.time() + 60 #WOL 指令已经发送， 停止一分钟
        self.countdown()

    def countdown(self):
        """ 实时显示倒计时 """
        remaining = int(self.next_check - time.time())
        while remaining > 0:
            # 格式化剩余时间为 MM:SS
            mins, secs = divmod(remaining, 60)
            timer = f'{mins:02d}:{secs:02d}'
            print(f"\r下次查询倒计时: {timer}", end="", flush=True)
            time.sleep(1)
            remaining = int(self.next_check - time.time())
        print("\r" + " " * 30 + "\r", end="")  # 清空倒计时行

    def run(self):
        """ 启动定时任务 """
        while True:
            #TODO 检查计算机是否处于开机状态
            if (host_nat.check_host_alive()):
                self.next_check = time.time() + 60 #计算机处于唤醒状态， 每60秒检查一次状态
                self.countdown()
                continue
            self.check_new_weibo()
            self.next_check = time.time() + 15 #计算机未处于唤醒状态， 每15秒进行一次指令检查
            self.countdown()

if __name__ == "__main__":
    monitor = WeiboMonitor()
    monitor.run()
