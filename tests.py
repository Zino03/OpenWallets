import requests
asset_url = "https://openwatch.kr/api/national-assembly/assets"
test_member_id = "T2T8225E"
params = {'member_id': test_member_id}
response = requests.get(asset_url, params=params)
print(response.status_code)
print(response.json())