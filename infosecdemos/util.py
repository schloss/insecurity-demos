import subprocess

def get_wireless_devices():
    cmd = "fakeroot airmon-ng | awk '{ print $1 }' | tail -n +5 | head -n -1"
    lines = subprocess.check_output(cmd, shell=True)
    return lines.split()
