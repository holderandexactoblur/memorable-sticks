import random
import tls_client
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load proxies from proxies.txt
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

# Load usernames from usernames.txt
def load_usernames():
    try:
        with open("usernames.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("usernames.txt not found. Exiting.")
        exit()

# Get a random proxy
def get_random_proxy(proxies):
    if proxies:
        return random.choice(proxies)
    return None

# Check username availability
def check_username(username, proxies):
    proxy = get_random_proxy(proxies)
    session = tls_client.Session(
        client_identifier="chrome112",
        random_tls_extension_order=True
    )

    # Set proxy if available
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    url = "https://kick.com/api/v1/signup/verify/username"
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip",
        "accept-language": "de_DE",
        "connection": "Keep-Alive",
        "content-type": "application/json",
        "host": "kick.com",
        "user-agent": "okhttp/4.9.2",
        "x-kick-app-p-os": "android",
        "x-kick-app-p-v": "28",
        "x-kick-app-v": "1.0.43",
    }

    try:
        response = session.post(
            url,
            headers=headers,
            json={
                "username": username,
            },
        )

        # If the response is empty, the username is available
        if not response.text:
            print(f"Available username: {username}")
            with threading.Lock():
                with open("available.txt", "a") as file:
                    file.write(username + "\n")
        else:
            print(f"Unavailable username: {username}")
    except Exception as e:
        print(f"Error checking username '{username}': {e}")

# Main function
def main():
    proxies = load_proxies()
    usernames = load_usernames()

    # Use ThreadPoolExecutor for multi-threading
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_username, username, proxies): username for username in usernames}
        for future in as_completed(futures):
            username = futures[future]
            try:
                future.result()  # Ensure any exceptions are raised
            except Exception as e:
                print(f"Error processing username '{username}': {e}")

if __name__ == "__main__":
    main()