import feedparser
import requests
import hashlib
import json
import os
import sys
import time
import base64
import hmac
from datetime import datetime

# ========= 配置 =========
RSS_URL = os.getenv("RSS_URL", "https://status.linode.com/history.rss")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
CACHE_FILE = "/app/cache/processed.json"
# =========================

def build_feishu_message(title, link, published):
    """构建飞书消息"""
    text = f"🚨 **Linode 状态更新**\n" \
           f"📌 **标题**: {title}\n" \
           f"🔗 **链接**: {link}\n" \
           f"⏰ **发布时间**: {published}"
    
    return {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }

def load_processed():
    """加载已处理的条目ID"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_processed(processed_ids):
    """保存已处理的条目ID"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(list(processed_ids), f)

def generate_feishu_sign(secret, timestamp):
    """生成飞书签名"""
    if not secret:
        return None
    
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    
    return sign

def send_feishu_webhook(title, link, published):
    """发送到飞书 Webhook"""
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL not set", file=sys.stderr)
        return False
    
    payload = build_feishu_message(title, link, published)
    headers = {"Content-Type": "application/json"}
    
    if WEBHOOK_SECRET:
        timestamp = str(int(time.time()))
        sign = generate_feishu_sign(WEBHOOK_SECRET, timestamp)
        
        if sign:
            signature = f"timestamp:{timestamp},sign:{sign}"
            headers["X-Lark-Signature"] = signature
            print(f"[DEBUG] Signature: {signature}")
    
    try:
        print(f"[DEBUG] Sending: {json.dumps(payload, indent=2)}")
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"[DEBUG] Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print(f"[{datetime.now()}] ✅ Feishu message sent: {title}")
                return True
            else:
                print(f"[{datetime.now()}] ❌ Feishu API error: {result}", file=sys.stderr)
                return False
        else:
            print(f"[{datetime.now()}] ❌ HTTP {response.status_code}", file=sys.stderr)
            return False
    
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Exception: {e}", file=sys.stderr)
        return False

def main():
    """主函数"""
    print(f"[{datetime.now()}] Starting RSS check...")
    
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL not set", file=sys.stderr)
        sys.exit(1)
    
    feed = feedparser.parse(RSS_URL)
    if feed.bozo:
        print(f"RSS Parse Error: {feed.bozo_exception}", file=sys.stderr)
        sys.exit(1)
    
    if not feed.entries:
        print("No entries found.")
        sys.exit(0)
    
    processed = load_processed()
    new_items = []
    
    for entry in feed.entries:
        item_id = entry.get('guid', entry.link)
        if item_id not in processed:
            new_items.append({
                'id': item_id,
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', '')
            })
    
    if not new_items:
        print("No new items.")
        sys.exit(0)
    
    # ✅ 直接取第一条（最新的）
    latest = new_items[0]
    print(f"[INFO] Processing latest: {latest['title']}")
    
    if send_feishu_webhook(latest['title'], latest['link'], latest['published']):
        processed.add(latest['id'])
        save_processed(processed)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
