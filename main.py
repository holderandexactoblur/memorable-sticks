import requests
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

write_lock = threading.Lock()

def load_proxies():
    proxies = []
    try:
        with open("proxies.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, username, password = parts
                        proxy_str = f"http://{username}:{password}@{ip}:{port}"
                        proxies.append(proxy_str)
                    else:
                        proxies.append("http://" + line)
    except FileNotFoundError:
        print("proxies.txt not found. Using direct connection.")
    return proxies

def get_random_proxy(proxies):
    if proxies:
        proxy_str = random.choice(proxies)
        return {"http": proxy_str, "https": proxy_str}
    return None

def fetch_xsrf_token(proxies):
    """Fetch the XSRF token from the kick.com homepage."""
    url = "https://kick.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
    }
    try:
        proxy = get_random_proxy(proxies)
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        if response.status_code == 200:
            # Extract the XSRF-TOKEN from cookies
            xsrf_token = response.cookies.get("XSRF-TOKEN")
            if xsrf_token:
                return xsrf_token
            else:
                print("XSRF-TOKEN not found in cookies.")
        else:
            print(f"Failed to fetch XSRF token: Status code {response.status_code}")
    except Exception as e:
        print(f"Error fetching XSRF token: {e}")
    return None

def check_username(username, proxies, xsrf_token, max_retries=3):
    url = "https://kick.com/api/v1/signup/verify/username"
    payload = {"username": username}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
        "Origin": "https://kick.com",
        "Referer": "https://kick.com/",
        "X-XSRF-TOKEN": xsrf_token,
        "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    
    for _ in range(max_retries):
        try:
            proxy = get_random_proxy(proxies)
            response = requests.post(url, json=payload, headers=headers, proxies=proxy, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("taken", False)
            elif response.status_code == 422:
                print(f"[422] Unprocessable Content for username '{username}': {response.text}")
                return None
            else:
                print(f"Username '{username}' returned unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"Error checking username '{username}': {e}")
            time.sleep(1)
    return None

def main():
    proxies = load_proxies()
    
    try:
        with open("usernames.txt", "r") as f:
            usernames = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("usernames.txt not found.")
        return

    # Fetch the XSRF token dynamically
    xsrf_token = fetch_xsrf_token(proxies)
    if not xsrf_token:
        print("Failed to fetch XSRF token. Exiting.")
        return

    with ThreadPoolExecutor(max_workers=90) as executor:
        futures = {executor.submit(check_username, username, proxies, xsrf_token): username for username in usernames}
        for future in as_completed(futures):
            username = futures[future]
            result = future.result()
            if result is None:
                print(f"Failed to check username: {username}")
            elif result:
                print(f"Username '{username}' is taken.")
            else:
                print(f"Username '{username}' is available.")
                with write_lock:
                    with open("available.txt", "a") as out_file:
                        out_file.write(username + "\n")

if __name__ == "__main__":
    main()
