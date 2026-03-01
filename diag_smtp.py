import socket
import ssl

def check_port(host, port, timeout=5):
    print(f"Checking {host}:{port}...")
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        print(f"  Connection to {host}:{port} SUCCESSFUL")
        sock.close()
        return True
    except socket.timeout:
        print(f"  Connection to {host}:{port} TIMED OUT")
    except Exception as e:
        print(f"  Connection to {host}:{port} FAILED: {e}")
    return False

def test_gmail():
    host = "smtp.gmail.com"
    check_port(host, 465)
    check_port(host, 587)
    check_port(host, 25)

if __name__ == "__main__":
    test_gmail()
