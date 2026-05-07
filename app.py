from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests, time, os, socket, boto3, logging
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# 📝 LOGGING CONFIG
log_file = 'logs/dashboard-access.log'


# Ensure the directory exists
log_dir = os.path.dirname(log_file)
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create log directory {log_dir}: {e}")

logger = logging.getLogger('user_access')
logger.setLevel(logging.INFO)
if not logger.handlers:
    try:
        # File Handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(fh)
        
        # Stream Handler (to see logs in console/docker logs)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(sh)
        
        logger.info("User access logging initialized.")
    except Exception as e:
        print(f"Error: Could not initialize log file {log_file}: {e}")

def log_access(message):
    try:
        client_ip = request.remote_addr
        full_message = f"IP: {client_ip} - {message}"
        logger.info(full_message)
        for handler in logger.handlers:
            handler.flush()
    except Exception as e:
        print(f"Logging error: {e}")


JENKINS_URL = os.getenv("JENKINS_URL")
USER = os.getenv("USER")
TOKEN = os.getenv("TOKEN")

# 👥 MULTI-USER CONFIG
USERS = { os.getenv("APP_USER", "admin"): os.getenv("APP_PASS", "admin123") }
users_str = os.getenv("USERS_LIST", "")
if users_str:
    for pair in users_str.split(","):
        if ":" in pair:
            u, p = pair.split(":", 1)
            USERS[u] = p

API_KEY = os.getenv("API_KEY")

# 🖥️ AWS EC2 CONFIG
INSTANCE_1_ID = os.getenv("INSTANCE_1_ID")
INSTANCE_2_ID = os.getenv("INSTANCE_2_ID")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

ec2 = boto3.client(
    'ec2',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

def get_instance_status(instance_id):
    try:
        res = ec2.describe_instances(InstanceIds=[instance_id])
        state = res['Reservations'][0]['Instances'][0]['State']['Name']
        return "UP" if state == 'running' else "DOWN"
    except Exception as e:
        print(f"Error checking status for {instance_id}: {e}")
        return "ERROR"


JOB_MAP = {
    "java": {
        "ols": {
            "angular": " -OLS-UAT-ANGULAR-2",
            "war": " _OLS_UAT_WAR",
            "war-angular": "DevOps/job/ols-full"
        },
        "admin": {
            "war": " _ADMIN_UAT_WAR",
            "angular": " _ADMIN_UAT_ANGULAR"
        }
    },
    "reports":{
        "war": " _REPORTS_UAT_WAR",
        "angular": " _REPORTS_UAT_ANGULAR"
        },

    "dotnet": {
        "cms": " _UAT_CMS",
        "fms": " _UAT_FMS",
        "dms": " _UAT_DMS"
    }
}

def check_api():
    return request.headers.get("x-api-key") == API_KEY

# ✅ HEALTH
@app.route('/')
def health():
    return "OK", 200

# 🔐 LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if username in USERS and USERS[username] == password:
            log_access(f"LOGIN: User '{username}' logged in.")
            
            s1_status = get_instance_status(INSTANCE_1_ID)
            s2_status = get_instance_status(INSTANCE_2_ID)

            if s1_status == "UP" and s2_status == "UP":
                return jsonify({"status": "SUCCESS", "username": username})
            else:
                return jsonify({
                    "status": "SERVERS_DOWN",
                    "s1": s1_status,
                    "s2": s2_status,
                    "username": username
                })
        else:
            return jsonify({
                "status": "FAIL",
                "message": "Invalid username or password"
            }), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "ERROR"}), 500

# 🔓 LOGOUT
@app.route('/api/logout', methods=['GET', 'POST'])
def logout():
    print("Logout request received")  # DEBUG PRINT
    try:

        data = request.get_json() or {}
        username = data.get("username") or "Unknown User"
        log_access(f"LOGOUT: User '{username}' logged out.")

        return jsonify({"status": "SUCCESS"})
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"status": "ERROR"}), 500


# ⚡ START SERVERS
@app.route('/api/start-servers', methods=['POST'])
def start_servers():
    if not check_api():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        ec2.start_instances(InstanceIds=[INSTANCE_1_ID, INSTANCE_2_ID])
        return jsonify({"status": "STARTING", "message": "AWS Instances are starting. Please wait 1-2 minutes."})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# 🚀 DEPLOY
@app.route('/api/deploy', methods=['POST'])
def deploy():
    if not check_api():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    if data["tech"] == "java":
        job = JOB_MAP["java"][data["app"]][data["type"]]
    else:
        job = JOB_MAP["dotnet"][data["app"]]

    url = f"{JENKINS_URL}/job/{job}/buildWithParameters"

    res = requests.post(url, params={"SVN_URL": data["svn_url"]}, auth=(USER, TOKEN))

    queue_url = res.headers['Location'] + "api/json"

    while True:
        q = requests.get(queue_url, auth=(USER, TOKEN)).json()
        if 'executable' in q:
            build = q['executable']['number']
            break
        time.sleep(2)

    return jsonify({"status": "STARTED", "job": job, "number": build})

# 📊 STATUS
@app.route('/api/status')
def status():
    if not check_api():
        return jsonify({"error": "Unauthorized"}), 401

    job = request.args.get('job')
    number = request.args.get('number')

    if not job or not number:
        return jsonify({"status": "IDLE"})

    res = requests.get(
        f"{JENKINS_URL}/job/{job}/{number}/api/json",
        auth=(USER, TOKEN)
    ).json()

    return jsonify({"status": "RUNNING" if res["building"] else res["result"]})

# 📜 LOGS
@app.route('/api/logs')
def logs():
    if not check_api():
        return jsonify({"error": "Unauthorized"}), 401

    job = request.args.get('job')
    number = request.args.get('number')

    if not job or not number:
        return jsonify({"logs": ""})

    logs = requests.get(
        f"{JENKINS_URL}/job/{job}/{number}/consoleText",
        auth=(USER, TOKEN)
    ).text

    return jsonify({"logs": logs})

# 📜 HISTORY
@app.route('/api/history')
def history():
    if not check_api():
        return jsonify({"error": "Unauthorized"}), 401

    history_data = {}
    today_counts = {"java": 0, "dotnet": 0}

    # Get start of today in ms
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000

    def fetch_job_history(job_name, tech):
        url = f"{JENKINS_URL}/job/{job_name}/api/json?tree=builds[number,result,timestamp]{{0,15}}"
        try:
            res = requests.get(url, auth=(USER, TOKEN), timeout=10).json()
            builds = res.get("builds", [])
            last_5 = []
            for b in builds:
                if len(last_5) < 5:
                    last_5.append({
                        "number": b.get("number"),
                        "result": b.get("result") or "RUNNING",
                        "timestamp": b.get("timestamp")
                    })
                if b.get("timestamp", 0) >= today_start:
                    today_counts[tech] += 1
            return last_5
        except Exception as e:
            return []

    for tech, apps in JOB_MAP.items():
        if tech not in history_data:
            history_data[tech] = {}
        if tech == "java":
            for app_name, types in apps.items():
                history_data[tech][app_name] = {}
                for type_name, job_name in types.items():
                    history_data[tech][app_name][type_name] = fetch_job_history(job_name, tech)
        else:
            for app_name, job_name in apps.items():
                history_data[tech][app_name] = fetch_job_history(job_name, tech)

    return jsonify({
        "history": history_data,
        "today_counts": today_counts
    })
