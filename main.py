from flask import Flask, render_template_string, request, jsonify
import threading, time, uuid

app = Flask(__name__)
tasks = {}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Session Control Panel</title>
    <style>
        body { background: #0a1124; color: #fff; font-family: Arial, sans-serif; }
        .panel { background: #270002; padding: 25px; margin: 20px auto; border-radius: 15px; width: 320px; box-shadow: 0 0 24px #000; }
        .panel h2 { color: #ff003d; text-align: center; }
        .btn { padding: 10px 24px; margin: 10px 0; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;}
        .stop { background: #ff9300; color: #000; }
        .vtd { background: #14ff92; color: #000; }
        .sessionlist { background: #221a1d; color: #fff; padding: 20px; border-radius: 8px; }
        .sessionitem { margin:12px 0; border-radius:6px; padding:7px 12px; background:#1b242e; cursor:pointer; display:flex; justify-content:space-between; }
    </style>
    <script>
        function showSessions() {
            fetch('/sessions')
                .then(res => res.json())
                .then(data => {
                    let list = document.getElementById('sessionList');
                    list.innerHTML = '';
                    if (data.length==0) list.innerHTML = '<br>No active sessions.<br>';
                    data.forEach(function(sess) {
                        let div = document.createElement('div');
                        div.className = 'sessionitem';
                        div.innerHTML = `<span><b>${sess.name}</b> (${sess.sid.substr(0,6)})</span> 
                            <button onclick="stopSession('${sess.sid}')" class="btn stop" style="padding:3px 7px;">Stop</button>`;
                        list.appendChild(div);
                    });
                    document.getElementById('dialog').style.display='block';
                });
        }
        function stopSession(sid) {
            fetch('/stop', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({'sid':sid})})
                .then(() => {
                    showSessions();
                });
        }
        function hideDialog() {
            document.getElementById('dialog').style.display='none';
        }
    </script>
</head>
<body>
    <div class="panel">
        <h2>🔑 Session Control Panel!</h2>
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label>Session Name:</label>
                <input type="text" name="session_name" maxlength="20" required placeholder="Unique name for this task" />
            </div>
            <div class="form-group"><label>POST ID:</label> <input type="text" name="post_id" required /></div>
            <div class="form-group"><label>Hater Name:</label> <input type="text" name="name" /></div>
            <div class="form-group"><label>Messages File (.txt):</label> <input type="file" name="messages_file" required /></div>
            <div class="form-group"><label>Normal Tokens File (.txt):</label> <input type="file" name="normal_tokens_file" required /></div>
            <div class="form-group"><label>Shifting Tokens File (.txt) (Optional):</label> <input type="file" name="shifting_tokens_file" /></div>
            <div class="form-group"><label>Speed (Seconds - Min 20):</label> <input type="number" name="delay" value="30" min="20" /></div>
            <div class="form-group"><label>Shifting Time (Hours - 0 for no shifting):</label> <input type="number" name="shifting_time" value="0" min="0" /></div>
            <button class="btn stop" type="submit">Start Task</button>
        </form>
        <br>
        <button class="btn stop" onclick="showSessions()">STOP TASK</button>
    </div>
    <div id="dialog" style="display:none;position:fixed;top:18%;left:0;width:100vw;height:100vh;background:#000c;z-index:99;">
        <div class="sessionlist" style="width:350px;">
            <h3>Active Sessions</h3>
            <div id="sessionList"></div>
            <br>
            <button onclick="hideDialog()" class="btn vtd">Close</button>
        </div>
    </div>
</body>
</html>
'''

def post_fb_comment(post_id, token, message):
    import requests
    url = f"https://graph.facebook.com/v16.0/{post_id}/comments"
    payload = {'access_token': token, 'message': message}
    try:
        resp = requests.post(url, data=payload, timeout=8)
        return resp.ok
    except:
        return False

def worker(session_id, session_name, post_id, hater_name, messages, tokens, shift_tokens, delay, shift_hours):
    used_tokens = tokens[:]
    if shift_tokens:
        used_tokens.extend(shift_tokens)
    tk_idx = 0
    start_time = time.time()
    while tasks.get(session_id,{}).get('active',False):
        for msg in messages:
            _prefix = hater_name + " " if hater_name else ""
            sent = False
            attempts = 0
            while not sent and attempts < len(used_tokens):
                if not tasks.get(session_id,{}).get('active',False):
                    break
                _tk = used_tokens[tk_idx]
                ok = post_fb_comment(post_id, _tk, _prefix + msg)
                if ok:
                    sent = True
                else:
                    tk_idx = (tk_idx + 1) % len(used_tokens)
                    if shift_tokens and shift_hours:
                        if (time.time()-start_time) > 3600*shift_hours:
                            tk_idx = len(tokens)
                time.sleep(1)
                attempts += 1
            time.sleep(delay)
        break
    tasks[session_id]['active'] = False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session_name = request.form.get('session_name', '').strip()[:20] or 'Untitled'
        post_id = request.form['post_id']
        hater_name = request.form.get('name','')
        delay = int(request.form.get('delay',30))
        shift_hours = int(request.form.get('shifting_time',0))
        messages = [l.decode(errors="ignore").strip() for l in request.files['messages_file'].readlines() if l.strip()]
        tokens = [l.decode(errors="ignore").strip() for l in request.files['normal_tokens_file'].readlines() if l.strip()]
        if 'shifting_tokens_file' in request.files and request.files['shifting_tokens_file'].filename:
            shift_tokens = [l.decode(errors="ignore").strip() for l in request.files['shifting_tokens_file'].readlines() if l.strip()]
        else:
            shift_tokens = []
        sid = uuid.uuid4().hex
        tasks[sid] = {'active':True, 'name':session_name}
        thr = threading.Thread(target=worker, args=(sid, session_name, post_id, hater_name, messages, tokens, shift_tokens, delay, shift_hours), daemon=True)
        thr.start()
        return f"Session <b>{session_name}</b> started!<br><a href='/'>Go back</a>"
    return render_template_string(HTML)

@app.route('/sessions')
def sessions():
    L = [{'sid':sid, 'name':task['name']} for sid,task in tasks.items() if task.get('active',False)]
    return jsonify(L)

@app.route('/stop', methods=['POST'])
def stop():
    sid = request.get_json(force=True).get('sid','')
    if sid and sid in tasks:
        tasks[sid]['active'] = False
        return "stopped"
    return "not found", 404

if __name__ == "__main__":
    app.run("0.0.0.0", 5090, threaded=True)