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
            color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-image: url('/static/IMG_20251028_232655.png');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            background-attachment: fixed;
        }
        .panel {
            background: rgba(20,23,36,0.65); /* lower opacity */
            border-radius: 18px;
            box-shadow: 0 0 40px 8px #0ff7ff99, 0 0 0 2px #fd1fff inset;
            border: 2px solid #ff1b99;
            padding: 38px 24px;
            margin: 30px auto;
            width: 380px;
            text-align:left;
        }
        h2 {
            color: #ff1f43;
            letter-spacing: 2px;
            margin-bottom: 10px;
            text-shadow: 0 0 18px #ec35ff, 0 0 32px #160080, 0 0 18px #fff;
            text-align:center;
            font-size: 2rem;
            font-family: 'Orbitron', 'Segoe UI', Arial, sans-serif;
        }
        label {
            color: #fff;
            font-size: 15px;
            text-shadow: 0 0 7px #ff1533, 0 0 12px #fff;
            font-weight: 600;
            letter-spacing:.5px;
        }
        input[type=text], input[type=number], input[type=file] {
            background: rgba(255,255,255,.11);
            color: #140003;
            border: none;
            border-radius: 5px;
            padding: 10px;
            width: 100%;
            font-size: 16px;
            margin-bottom: 18px;
            box-shadow: 0 0 8px #fffdfe99 inset, 0 0 0 2px #ec35ff22;
            font-weight: 800;
            text-shadow: 0 0 7px #fff, 0 0 9px #ff1b99;
        }
        input[type=text]:focus, input[type=number]:focus, input[type=file]:focus {
            outline: 2px solid #fd1fff;
            box-shadow: 0 0 14px #fd46ffbb inset;
        }
        ::placeholder{color: #a5000099;font-weight:600;text-shadow: 0 0 4px #fff;}
        .btn {
            padding: 14px 36px;
            font-size: 21px;
            border-radius: 8px;
            border: none;
            margin-top: 8px;
            margin-bottom: 15px;
            background: linear-gradient(90deg, #fff 10%, #fc233a 80%);
            color: #1b001d;
            font-weight: 700;
            letter-spacing: 1px;
            box-shadow: 0 0 32px #ff1bafa0,0 0 12px #fff inset;
            cursor:pointer;
            outline:none;
            transition:.17s;
            text-shadow: 0 0 11px #fff,0 0 16px #ff1b99;
            border-bottom:3px solid #fd1fff77;
        }
        .btn.stop {background: linear-gradient(90deg, #ff1b99 12%, #fff 70%);}
        .btn.vtd {background: linear-gradient(90deg,#25ffca 12%,#fff 80%);color:#0a0221;}
        .form-group {
            margin-bottom: 16px;
            border-bottom: 1.7px solid #ffedfdbb;
            padding-bottom: 7px;
        }
        .sessionitem{
            background:rgba(255,255,255,0.04);
            border-radius:8px;
            color: #fff;
            padding: 11px 8px;
            font-size:17px;
            display:flex;justify-content:space-between;align-items:center;
            box-shadow:0 0 15px #ff1bffa9;
            border: 2px solid #ff1b99;
            margin-bottom: 14px;
        }
        .sessionlist{background-color:#0c0020de;padding:26px 15px;border-radius:12px;}
        #dialog {
            display:none;
            position:fixed;
            top:0; left:0; width:100vw; height:100vh;
            background:#071b2ecc; z-index:9999;align-items:center;justify-content:center;
        }
        #dialog>div{max-width:420px;margin:auto;}
        .statusMsg {padding: 12px 22px; background: #1d0a22c9; border-radius: 9px; color: #fc35ff; font-size:1.1rem;font-weight:700;box-shadow:0 0 6px #fff;}
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
                        <button onclick="stopSession('${sess.sid}')" class="btn stop" style="font-size:18px;padding:4px 13px;">❌</button>`;
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
            <h3 style="text-align:center;color:#fc35ff;text-shadow:0 0 11px #fff;">Active Sessions</h3>
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
