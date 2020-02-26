# requires request library, download at: pip install requests
import requests
import json


def get_nav_data(token):
    api_endpoint = 'https://arbeidsplassen.nav.no/public-feed/api/v1/ads?size=4999'
    api_headers = {'accept': 'application/json',
                   'Authorization': token}
    download = requests.get(url=api_endpoint, headers=api_headers)
    if download.status_code == 200:
        data = download.json()
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("Download complete")
        return True
    elif download.status_code == 401:
        print("Error 401 not authorized, public token likely expired. Get a new one at: https://github.com/navikt/pam-public-feed")
        return False
    else:
        print("Error: " + str(download.status_code))
        return False


if __name__ == "__main__":
    api_public_token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    get_nav_data(api_public_token)

