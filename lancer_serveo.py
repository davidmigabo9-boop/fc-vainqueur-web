import subprocess, time, sys, os, re, webbrowser, threading

os.chdir(r"C:\Users\LENOVO\Documents\New OpenCode Project\fc_vainqueur_web")

print("=" * 50)
print("  FC VAINQUEUR - Serveur + Tunnel Serveo")
print("=" * 50)

print("\n1. Demarrage Flask...")
flask = subprocess.Popen(
    [sys.executable, "-c",
     "from app import create_app; app=create_app(); app.run(host='0.0.0.0',port=5000,debug=False)"]
)
time.sleep(4)
print("   Flask OK")

print("2. Demarrage tunnel Serveo...")
ssh = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "serveo.net"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL
)

url = None
for line in iter(ssh.stdout.readline, b""):
    text = line.decode("utf-8", errors="replace").strip()
    if text:
        print(f"   {text}")
    m = re.search(r'(https://\S+serveousercontent\.com)', text)
    if m:
        url = m.group(1)
        break

if not url:
    print("ERREUR: pas de lien recu!")
    flask.terminate()
    sys.exit(1)

with open("lien.txt", "w") as f:
    f.write(url)

def drain(proc):
    for _ in proc.stdout:
        pass

threading.Thread(target=drain, args=(ssh,), daemon=True).start()

print(f"\n{'=' * 50}")
print(f"  LIEN: {url}")
print(f"  Login: admin / admin123")
print(f"{'=' * 50}")

try:
    webbrowser.open(url + "/login")
    print("\nNavigateur ouvert.")
except:
    print(f"\nOuvre: {url}/login")

print("Ctrl+C pour arreter.\n")

try:
    while True:
        if flask.poll() is not None:
            print("Flask arrete, relance...")
            flask = subprocess.Popen(
                [sys.executable, "-c",
                 "from app import create_app; app=create_app(); app.run(host='0.0.0.0',port=5000,debug=False)"]
            )
        time.sleep(3)
except KeyboardInterrupt:
    flask.terminate()
    ssh.terminate()
    print("\nArrete.")
