from flask import Flask, render_template_string, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# ========== 从 config.json 读取 ==========
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        return None

config = load_config()
if not config:
    print("❌ 请检查 config.json 文件")
    exit(1)

API_KEY = config.get('API_KEY', '').strip()
BASE_URL = config.get('BASE_URL', '').rstrip('/')
MODEL = config.get('MODEL', 'deepseek-chat')

print("="*50)
print("✅ DeepSeek 配置加载成功")
print(f"   BASE_URL: {BASE_URL}")
print(f"   MODEL: {MODEL}")
print(f"   API_KEY: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 10 else ''}")
print("="*50)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DeepSeek 编程助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; height: 100vh; display: flex; flex-direction: column; }
        #header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
        #header h1 { font-size: 18px; }
        #header .model { font-size: 12px; color: #8b949e; background: #21262d; padding: 4px 12px; border-radius: 20px; }
        .deepseek-badge { background: #4d6bfe; padding: 2px 10px; border-radius: 12px; font-size: 11px; margin-left: 8px; }
        #messages { flex: 1; overflow-y: auto; padding: 24px; }
        .msg { max-width: 80%; margin-bottom: 16px; padding: 12px 16px; border-radius: 12px; white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }
        .user { background: #1f6feb; color: white; margin-left: auto; }
        .assistant { background: #21262d; color: #e6edf3; border: 1px solid #30363d; }
        .error { background: #3d1a1a; color: #f85149; border: 1px solid #f85149; }
        #input-area { padding: 16px 24px; border-top: 1px solid #30363d; display: flex; gap: 12px; background: #0d1117; }
        #input-area textarea { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #30363d; background: #161b22; color: #e6edf3; resize: none; font-size: 14px; outline: none; font-family: inherit; }
        #input-area textarea:focus { border-color: #4d6bfe; }
        #input-area button { padding: 12px 32px; background: #4d6bfe; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; }
        #input-area button:hover { background: #6b85ff; }
        #input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .loading { color: #8b949e; font-style: italic; }
        .code-block { background: #0d1117; padding: 12px; border-radius: 6px; border: 1px solid #30363d; margin: 8px 0; overflow-x: auto; }
        .system-msg { color: #8b949e; font-style: italic; padding: 8px; border-bottom: 1px solid #30363d; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div id="header">
        <div>
            <h1>🤖 DeepSeek 编程助手</h1>
            <span class="deepseek-badge">🚀 DeepSeek</span>
        </div>
        <span class="model">{{ model }}</span>
    </div>
    <div id="messages">
        <div class="system-msg">💡 输入你的编程问题，DeepSeek 会帮你解答</div>
        <div class="system-msg">📌 支持: 代码编写、调试、解释、算法设计、系统重构等</div>
    </div>
    <div id="input-area">
        <textarea id="input" rows="2" placeholder="输入你的编程问题..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
        <button onclick="send()" id="sendBtn">发送</button>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        let conversation = [];

        function addMessage(role, content, isError = false) {
            const div = document.createElement('div');
            div.className = `msg ${role}`;
            if (isError) div.classList.add('error');
            try {
                content = content.replace(/```(\\w+)?\\n([\\s\\S]*?)```/g, '<div class="code-block"><code>$2</code></div>');
            } catch(e) {}
            div.innerHTML = content.replace(/\\n/g, '<br>');
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addSystemMsg(text) {
            const div = document.createElement('div');
            div.className = 'system-msg';
            div.textContent = 'ℹ️ ' + text;
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        async function send() {
            const text = input.value.trim();
            if (!text) {
                addMessage('error', '⚠️ 请输入内容', true);
                return;
            }
            input.value = '';
            sendBtn.disabled = true;
            sendBtn.textContent = '发送中...';
            
            addMessage('user', text);
            conversation.push({role: 'user', content: text});

            const loading = document.createElement('div');
            loading.className = 'msg assistant loading';
            loading.textContent = '⏳ 思考中...';
            messagesDiv.appendChild(loading);

            try {
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({messages: conversation})
                });
                
                const data = await resp.json();
                loading.remove();
                
                if (data.error) {
                    addMessage('error', '❌ ' + data.error, true);
                } else {
                    addMessage('assistant', data.reply);
                    conversation.push({role: 'assistant', content: data.reply});
                }
            } catch (e) {
                loading.remove();
                addMessage('error', '❌ 网络错误: ' + e.message, true);
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = '发送';
                input.focus();
            }
        }

        window.onload = function() {
            input.focus();
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, model=MODEL)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.7
    }
    
    print(f"\n{'='*50}")
    print(f"📨 请求URL: {url}")
    print(f"🤖 模型: {MODEL}")
    print(f"📝 消息数: {len(messages)}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"📊 状态码: {resp.status_code}")
        
        if resp.status_code != 200:
            error_text = resp.text[:500] if resp.text else "无响应"
            print(f"❌ 错误: {error_text}")
            return jsonify({"error": f"HTTP {resp.status_code}: {error_text}"}), resp.status_code
        
        result = resp.json()
        reply = result["choices"][0]["message"]["content"]
        print(f"✅ 成功，回复长度: {len(reply)} 字符")
        return jsonify({"reply": reply})
        
    except requests.exceptions.Timeout:
        print("❌ 超时")
        return jsonify({"error": "⏰ 请求超时"}), 504
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        return jsonify({"error": f"🔌 连接失败: {str(e)}"}), 502
    except Exception as e:
        print(f"❌ 错误: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 DeepSeek 编程助手启动中...")
    print(f"🌐 端口: {port}")
    print("💡 按 Ctrl+C 停止服务")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=port)
