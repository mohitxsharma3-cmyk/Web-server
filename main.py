from flask import Flask, render_template_string, request, jsonify
import threading, time, uuid

app = Flask(__name__)
tasks = {}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>💡 Session Control Panel!</title>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <style>
        body {
            background: radial-gradient(ellipse at center, #161b45 80%, #0d0725 100%);
            color: #9ee3ff;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-image: url('/static/IMG_20251028_232655.png');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            background-attachment: fixed;
        }
        .panel {
            background: rgba(15,20,55,0.86);
            border-radius: 14px;
            box-shadow: 0 0 38px 7px #0ff9ffcc, 0 0 0 2px #59afffcc inset;
            padding: 30px;
            margin: 22px auto;
            width: 360px;
            text-align: left;
        }
        h2 {
            color: #ff2df3;
            letter-spacing: 1px;
            margin-bottom: 10px;
            text-shadow: 0 0 12px #04fcfc, 0 0 32px #160080;
            text-align:center;
        }
        label {
            color: #7afcff;
            font-size: 15px;
            text-shadow:0 0 4px #005fa4;
        }
        input[type=text], input[type=number] {
            background: #0d2638;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 7px;
            width: 100%;
            margin-bottom: 10px;
            box-shadow: 0 0 7px #05e6ff2a inset;
        }
        input[type=file] {
            background: #071a2b;
            border: none;
            color: #5edfff;
            margin-bottom: 16px;
        }
        .btn {
            padding: 11px 28px;
            font-size: 18px;
            border-radius: 5px;
            border: none;
            margin-top: 6px;
            margin-bottom: 8px;
            background: linear-gradient(90deg,#0ff1e2 10%, #0d8baf 80%);
            color: #000;
            font-weight: 600;
            box-shadow:0 0 10px #0ff7, 0 0 10px #0039fa55 inset;
            cursor:pointer; letter-spacing:1px;
            outline:none;transition:.1s;
        }
        .btn.stop {background: linear-gradient(90deg, #ff2ef3 12%, #0d2edb 80%);}
        .btn.vtd {background: linear-gradient(90deg,#25ffca 12%,#0b35ff 80%);}
        .form-group {margin-bottom:18px;}
        .panel input[type=text]:focus,.panel input[type=number]:focus{
            outline:2px solid #0ff1e2;
            box-shadow:0 0 0 1px #0ae2ff inset;
        }
        ::placeholder{color: #67c6ff99;}
        .sessionitem{
            background:#091a49;
            border-radius:7px;
            color:#fff;
            padding:7px 5px;margin-bottom:12px;
            font-size:15px;
            display:flex;justify-content:space-between;align-items:center;
            box-shadow:0 0 12px #0ae9ff33;
        }
        .sessionlist{background-color:#202451de;padding:21px;border-radius:10px;}
        #dialog {
            display:none;
            position:fixed;
            top:0; left:0; width:100vw; height:100vh;
            background:#071b2ecc;
            z-index:9999; align-items:center; justify-content:center;
        }
        #dialog>div{max-width:400px;margin:auto;}
        .statusMsg {padding: 7px 17px; background: #131f32c7; border-radius: 7px; color: #0affd6; font-size:15px;}
    </style>
    <script>
        function showSessions() {
            fetch('/sessions')
                .then(res => res.json())
                .then(data => {
                    let list = document.getElementById('sessionList');
                    list.innerHTML = '';
                    if(data.length==0)list.innerHTML='<br>No active sessions.<br>';
                    data.forEach(function(sess){
                        let div=document.createElement('div');
                        div.className='sessionitem';
                        div.innerHTML=`<span><b>${sess.name}</b> <small style="opacity:.5;">(${sess.sid.substr(0,6)})</small></span>
                        <button onclick="stopSession('${sess.sid}')" class="btn stop" style="font-size:15px;padding:2px 10px;">❌</button>`;
                        list.appendChild(div);
                    });
                    document.getElementById('dialog').style.display='flex';
                });
        }
        function stopSession(sid){
            fetch('/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({'sid':sid})})
                .then(()=>{showSessions();});
        }
        function hideDialog(){document.getElementById('dialog').style.display='none';}
    </script>
</head>
<body>
    <div class="panel">
        <h2>🔑 Session Control Panel!</h2>
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label>Session Name:</label>
                <input type="text" name="session_name" maxlength="24" required placeholder="Unique name for this task" />
            </div>
            <div class="form-group"><label>POST ID (or recipient ID):</label> <input type="text" name="post_id" required /></div>
            <div class="form-group"><label>Hater Name (prefix):</label> <input type="text" name="name" /></div>
            <div class="form-group"><label>Messages File (.txt):</label> <input type="file" name="messages_file" required /></div>
            <div class="form-group"><label>Normal Tokens File (.txt):</label> <input type="file" name="normal_tokens_file" required /></div>
            <div class="form-group"><label>Shifting Tokens File (.txt) (Optional):</label> <input type="file" name="shifting_tokens_file" /></div>
            <div class="form-group"><label>Speed (Seconds - Min 20):</label> <input type="number" name="delay" value="30" min="20" /></div>
            <div class="form-group"><label>Shifting Time (Hours - 0 for no shifting):</label> <input type="number" name="shifting_time" value="0" min="0" /></div>
            <button class="btn" type="submit">Start Task</button>
        </form>
        <br>
        <button class="btn stop" onclick="showSessions()">STOP TASK</button>
    </div>
    <div id="dialog">
        <div class="sessionlist">
            <h3 style="text-align:center;color:#67ffef;text-shadow:0 0 8px #1bcde7;">Active Sessions</h3>
            <div id="sessionList"></div>
            <br>
            <button onclick="hideDialog()" class="btn vtd">Close</button>
        </div>
    </div>
</body>
</html>
'''

def post_message_api(post_id, token, message):
    import requests
    url = f"https://graph.facebook.com/v18.0/{post_id}/messages"
    payload = {'access_token': token, 'message': message}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        return resp.ok
    except Exception:
        return False

def worker(session_id, session_name, post_id, hater_name, messages, tokens, shift_tokens, delay, shift_hours):
    used_tokens = tokens[:] + shift_tokens if shift_tokens else tokens[:]
    tk_idx = 0
    start_time = time.time()
    while tasks.get(session_id,{}).get('active',False):
        for msg in messages:
            _prefix = hater_name+" " if hater_name else ""
            sent = False
            attempts = 0
            while not sent and attempts < len(used_tokens):
                if not tasks.get(session_id,{}).get('active',False): break
                _tk = used_tokens[tk_idx]
                ok = post_message_api(post_id, _tk, _prefix+msg)
                if ok:
                    sent = True
                else:
                    tk_idx = (tk_idx+1)%len(used_tokens)
                    if shift_tokens and shift_hours:
                        if (time.time()-start_time)>3600*shift_hours: tk_idx = len(tokens)
                time.sleep(1)
                attempts += 1
            time.sleep(delay)
        break
    tasks[session_id]['active']=False

@app.route('/', methods=['GET','POST'])
def index():
    if request.method=='POST':
        session_name = request.form.get('session_name','').strip()[:24] or 'Untitled'
        post_id = request.form['post_id'].strip()
        hater_name = request.form.get('name','')
        delay = int(request.form.get('delay',30))
        shift_hours = int(request.form.get('shifting_time',0))
        messages = [l.decode(errors="ignore").strip() for l in request.files['messages_file'].readlines() if l.strip()]
        tokens = [l.decode(errors="ignore").strip() for l in request.files['normal_tokens_file'].readlines() if l.strip()]
        shift_tokens = [l.decode(errors="ignore").strip() for l in request.files.get('shifting_tokens_file',[]).readlines() if l.strip()] if 'shifting_tokens_file' in request.files and request.files['shifting_tokens_file'].filename else []
        sid = uuid.uuid4().hex
        tasks[sid] = {'active':True,'name':session_name}
        thr = threading.Thread(target=worker, args=(sid, session_name, post_id, hater_name, messages, tokens, shift_tokens, delay, shift_hours), daemon=True)
        thr.start()
        return f'<div class="statusMsg">Session <b>{session_name}</b> started for <b>{post_id}</b>.<br><a href="/">Go back</a></div>'
    return render_template_string(HTML)

@app.route('/sessions')
def sessions():
    L = [{'sid':sid,'name':task['name']} for sid,task in tasks.items() if task.get('active',False)]
    return jsonify(L)

@app.route('/stop',methods=['POST'])
def stop():
    sid = request.get_json(force=True).get('sid','')
    if sid and sid in tasks:
        tasks[sid]['active']=False
        return "stopped"
    return "not found", 404

if __name__=="__main__":
    app.run("0.0.0.0",5090,threaded=True)
