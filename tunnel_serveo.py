import subprocess, time, sys, os, re, threading, signal

os.chdir(r"C:\Users\LENOVO\Documents\New OpenCode Project\fc_vainqueur_web")

print("Demarrage tunnel Serveo...")
ssh = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "serveo.net"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
    bufsize=0
)

url = None
for line in iter(ssh.stdout.readline, b""):
    text = line.decode("utf-8", errors="replace").strip()
    print(f"  {text}")
    m = re.search(r'(https://\S+serveousercontent\.com)', text)
    if m:
        url = m.group(1)
        break

if not url:
    print("ERREUR: pas de lien!")
    ssh.terminate()
    sys.exit(1)

with open("lien.txt", "w") as f:
    f.write(url)
print(f"\nLIEN: {url}")

def drain(proc):
    for _ in proc.stdout:
        pass

threading.Thread(target=drain, args=(ssh,), daemon=True).start()

print("Tunnel actif. Ctrl+C pour arreter.")
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    ssh.terminate()
    print("Arrete.")
