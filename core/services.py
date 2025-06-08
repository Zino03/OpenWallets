# core/services.py (수정본)
import requests
import time
import math
from .models import Legislator, Asset
from django.db import IntegrityError

OPENWATCH_BASE_URL = "https://openwatch.kr/api/national-assembly"
MEMBERS_ENDPOINT = f"{OPENWATCH_BASE_URL}/members" # 의원 정보 엔드포인트
ASSETS_ENDPOINT = f"{OPENWATCH_BASE_URL}/assets" # 자산 정보 엔드포인트

def fetch_api_data(url, params=None): # API 데이터 가져오는 함수
    print(f"API url: {url}, params: {params or {}}")
    try:
        response = requests.get(url, params=params, timeout=60) # 타임아웃 늘림
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        print(f"API Response Status Code: {response.status_code}")
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Error: 타임아웃 {url}")
        return None
    
def save_legislators(): # 의원 정보 저장
    print("\n의원 정보 저장 시작")
    all_legislator_items = [] # 페이지 체크
    page_num = 1
    items_per_page = 100
    PARAM_NAME_PAGE = 'page'
    PARAM_NAME_LIMIT = 'pageSize'
    total_count = 0

    while True:
        params = {
            PARAM_NAME_PAGE: page_num,
            PARAM_NAME_LIMIT: items_per_page
        }
        print(f"/member page {page_num} (pageSize {items_per_page}) from: {MEMBERS_ENDPOINT}")
        page_data = fetch_api_data(MEMBERS_ENDPOINT, params=params)

        if not page_data: # API 요청 실패 시 중단
            print(f"요청 실패 > 중단")
            break

        if page_num == 1: # 첫 페이지 응답에서 전체 개수 확인
            if 'totalCount' in page_data:
                total_count = page_data['totalCount']
                print(f"저장된 의원 정보 데이터의 양: {total_count}")
                if total_count == 0:
                    print("데이터 없음")
                    break
        # 현재 페이지의 데이터(rows) 가져오기
        items_on_page = page_data.get('rows', [])
        if not items_on_page:
            print(f"종료 / 페이지에 데이터 없음 {page_num}")
            break

        # 가져온 데이터를 전체 리스트에 추가
        all_legislator_items.extend(items_on_page)
        print(f"{page_num} 페이지에서 legislator 정보를 {len(items_on_page)}만큼 가져옴. 총 받은 양: {len(all_legislator_items)}")

        # 만약 total_count를 얻었고, 누적된 아이템 수가 total_count 이상이면 종료
        if total_count > 0 and len(all_legislator_items) >= total_count:
            print("데이터 다 받았으므로 종료")
            break

        page_num += 1
        time.sleep(0.5) # 서버 부하 방지 0.5초 대기

    print(f"\n의원 정보 가져오기 끝")

    saved_count = 0
    updated_count = 0
    skipped_count = 0
    total_rows_to_process = len(all_legislator_items)

    if total_rows_to_process > 0:
        print(f"DB에 legislator 정보 저장 시작. 총량: {total_rows_to_process}")
    else:
        print("DB에 저장할 legislator 정보가 없음")
        return 0, 0, 0

    # 가져온 모든 의원 정보(all_legislator_items)를 순회하며 DB에 저장
    for i, member_info in enumerate(all_legislator_items):
        # 진행 상황 로그
        if (i + 1) % 100 == 0:
             print(f"DB에 legislator 정보 저장 중 {i+1} / {total_rows_to_process}...")

        member_id = member_info.get('id')
        if not member_id:
            skipped_count += 1
            continue

        defaults = {
            'name': member_info.get('name'),
            'party': member_info.get('partyName'),
            'gender': member_info.get('gender'),
            'reelected': member_info.get('reelected'),
            'electoral_district': member_info.get('electoralDistrict'),
            'latest_age': member_info.get('latestAge'),
            # 필요한 다른 필드들도 여기에 추가
        }
        defaults = {k: v for k, v in defaults.items() if v is not None}

        try:
            legislator, created = Legislator.objects.update_or_create(
                member_id=member_id, # 고유 ID 기준으로 찾거나 생성
                defaults=defaults
            )
            if created:
                saved_count += 1
            else:
                updated_count += 1
        except IntegrityError as e:
            print(f"Error : DB 무결성 오류 legislator {member_id} ({member_info.get('name')}): {e}")
            skipped_count += 1
        except Exception as e:
            print(f"Error : 의원 정보 저장 {member_id}: {e}")
            skipped_count += 1

    print(f"\nLegislator 정보 저장 완료")
    print(f"총 받은 양: {total_rows_to_process}, Saved: {saved_count}, Skipped: {skipped_count}")
    return saved_count, updated_count, skipped_count

def save_assets():  #assets API에서 자산 정보를 가져와 DB에 저장 (파라미터 기반)
    print("\nAsset 정보 저장 시작")

    # 1. 페이지네이션으로 모든 자산 데이터 가져오기
    all_asset_items = []
    page_num = 1
    items_per_page = 100
    PARAM_NAME_PAGE = 'page'
    PARAM_NAME_LIMIT = 'limit'
    total_count = 0

    while True:
        # 페이지네이션 API 호출 로직
        params = { PARAM_NAME_PAGE: page_num, PARAM_NAME_LIMIT: items_per_page }
        page_data = fetch_api_data(ASSETS_ENDPOINT, params=params)
        if not page_data: break
        if page_num == 1:
            if 'totalCount' in page_data: total_count = page_data['totalCount']
        items_on_page = page_data.get('rows', [])
        if not items_on_page: break
        all_asset_items.extend(items_on_page)
        if total_count > 0 and len(all_asset_items) >= total_count: break
        page_num += 1
        time.sleep(0.5) # 대기 시간 유지

    print(f"\n모든 페이지 가져오기 끝 / 총 asset 양 : {len(all_asset_items)}")

    # 2. DB 저장을 위한 준비
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    total_rows_to_process = len(all_asset_items)

    if total_rows_to_process == 0:
        print("DB에 저장할 asset 정보가 없음")
        return 0, 0, 0

    # member_id를 키로, Legislator 객체를 값으로 하는 딕셔너리 생성
    try:
        # Legislator 모델에 접근해서 모든 객체를 가져옴
        legislators_dict = {leg.member_id: leg for leg in Legislator.objects.all()}
        print(f"Loaded {len(legislators_dict)} legislators.")
        if not legislators_dict:
             print("DB에 legislator 정보 없음")

    except Exception as e:
        print(f"Error: legislators 로딩: {e}.")
        return 0, 0, total_rows_to_process # 오류 발생 시 중단 및 스킵 처리

    print(f"asset 정보 프로세스 시작: {total_rows_to_process}")

    # 3. 모든 자산 데이터를 순회하며 DB에 저장
    for i, item in enumerate(all_asset_items):
        if (i + 1) % 500 == 0: # 500개마다 로그 출력
             print(f"DB에 저장 중 {i+1} / {total_rows_to_process}...")

        # 기존 자산 정보 추출
        openwatch_asset_id = item.get('id')
        national_assembly_member_id = item.get('nationalAssemblyMemberId')
        date_str = item.get('date')

        if not openwatch_asset_id or not national_assembly_member_id or not date_str:
            skipped_count += 1
            continue
        legislator = legislators_dict.get(national_assembly_member_id) # 딕셔너리에서 조회
        if legislator is None:
            # 미리 로드한 딕셔너리에 해당 의원이 없으면 건너뛰기
            skipped_count += 1
            continue

        try:
            # Asset 모델에 parse_date_string 메소드가 있다고 가정
            report_year, report_month = Asset.parse_date_string(date_str)
            if report_year is None or report_month is None:
                skipped_count += 1
                continue
        except AttributeError:
             print(f"Error: Asset have not 'parse_date_string")
             skipped_count += 1
             continue
        except Exception as e:
             print(f"Error: 날짜 오류 '{date_str}': {e}")
             skipped_count += 1
             continue

        defaults = {
            'legislator': legislator,
            'report_year': report_year,
            'report_month': report_month,
            'current_valuation': item.get('currentValutaion') or item.get('currentValuation'),
        }
        defaults = {k: v for k, v in defaults.items() if v is not None}

        try:
            asset, created = Asset.objects.update_or_create(
                openwatch_asset_id=openwatch_asset_id,
                defaults=defaults
            )
            if created:
                saved_count += 1
            else:
                updated_count += 1
        except Exception as e:
            # 오류 처리
            skipped_count += 1

    print(f"\n문제 없이 끝")
    print(f"총 받은 양: {total_rows_to_process}, Saved: {saved_count}, Skipped: {skipped_count}")
    return saved_count, updated_count, skipped_count

def run_import_process():
    print("프로그램 실행")
    save_legislators() # 의원 신상 정보 저장
    save_assets() # 자산 정보 저장
    print("\문제 없이 끝")