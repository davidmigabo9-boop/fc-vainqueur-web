import subprocess, time, sys, os, re, threading

os.chdir(r"C:\Users\LENOVO\Documents\New OpenCode Project\fc_vainqueur_web")

print("1. Flask...")
flask = subprocess.Popen(
    [sys.executable, "-c",
     "from app import create_app; app=create_app(); app.run(host='0.0.0.0',port=5000,debug=False)"]
)
time.sleep(5)

r = os.popen("curl -s http://localhost:5000/").read()
print(f"   Flask: {'OK' if r else 'FAIL'}")

print("2. Tunnel serveo...")
ssh = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "serveo.net"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, bufsize=0
)

url = None
for line in iter(ssh.stdout.readline, b""):
    text = line.decode("utf-8", errors="replace").strip()
    print(f"   {text}")
    m = re.search(r'(https://\S+serveousercontent\.com)', text)
    if m:
        url = m.group(1)
        break

if not url:
    print("ERREUR")
    flask.terminate()
    sys.exit(1)

threading.Thread(target=lambda p: [x for x in p.stdout], args=(ssh,), daemon=True).start()

print(f"\n{'='*50}")
print(f"LIEN: {url}")
print(f"Login: admin / admin123")
print(f"{'='*50}")

time.sleep(2)
print("\nTest local...")
r2 = os.popen("curl -s http://localhost:5000/login").read()
print(f"   Local: {'OK' if 'fc' in r2.lower() or 'login' in r2.lower() else 'FAIL'}")

try:
    while True:
        if flask.poll() is not None:
            flask = subprocess.Popen(
                [sys.executable, "-c",
                 "from app import create_app; app=create_app(); app.run(host='0.0.0.0',port=5000,debug=False)"]
            )
        if ssh.poll() is not None:
            print("Tunnel perdu! Relance...")
            ssh = subprocess.Popen(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "serveo.net"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, bufsize=0
            )
        time.sleep(5)
except KeyboardInterrupt:
    flask.terminate()
    ssh.terminate()
