# core/services.py (상태 저장/로드 추가)
import requests
import time
import csv
import math
import logging
from .models import Legislator, Asset
from django.db import IntegrityError
import os
import json # json 모듈 임포트

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

OPENWATCH_BASE_URL = "https://openwatch.kr/api/national-assembly"
MEMBERS_ENDPOINT = f"{OPENWATCH_BASE_URL}/members"
ASSETS_ENDPOINT = f"{OPENWATCH_BASE_URL}/assets"

# --- 상태 파일 관련 Helper 함수 ---
DEFAULT_STATUS_FILE = '.fetch_status.json'

def load_status(status_file=DEFAULT_STATUS_FILE):
    """상태 파일을 읽어 마지막 페이지 정보를 반환합니다."""
    if not os.path.exists(status_file):
        return {} # 파일 없으면 빈 딕셔너리 반환
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
            # 간단한 유효성 검사 (필요에 따라 추가)
            if not isinstance(status_data, dict):
                logger.warning(f"Invalid status file format in {status_file}. Starting fresh.")
                return {}
            return status_data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read status file {status_file}: {e}. Starting fresh.")
        return {}

def save_status(data, status_file=DEFAULT_STATUS_FILE):
    """현재 상태를 상태 파일에 저장합니다."""
    try:
        # 기존 상태를 읽어와서 업데이트 (다른 작업의 상태 유지)
        current_status = load_status(status_file)
        current_status.update(data)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(current_status, f, indent=2)
        logger.debug(f"Saved status to {status_file}: {data}")
    except IOError as e:
        logger.error(f"Could not write status file {status_file}: {e}")

def delete_status(status_file=DEFAULT_STATUS_FILE):
    """상태 파일을 삭제합니다."""
    if os.path.exists(status_file):
        try:
            os.remove(status_file)
            logger.info(f"Removed status file: {status_file}")
            print(f"Status file {status_file} removed for a fresh start.")
        except OSError as e:
            logger.error(f"Error removing status file {status_file}: {e}")
            print(f"Error: Could not remove status file {status_file}: {e}")

def fetch_api_data(url, params=None):
    logger.info(f"Requesting API: {url} with params: {params or {}}")
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        logger.info(f"API Response Status Code: {response.status_code}")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while requesting {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching {url}: {e}", exc_info=True)
        return None

def save_legislators(status_file=DEFAULT_STATUS_FILE): # status_file 인자 추가
    """/members API에서 의원 정보를 가져와 DB에 저장 (상태 관리 기능 추가)"""
    print("\n--- Fetching Legislator Data (Paginated with Params) ---")

    # 상태 로드하여 시작 페이지 결정
    status_data = load_status(status_file)
    start_page = status_data.get('legislators_last_page', 0) + 1
    if start_page > 1:
        print(f"Resuming legislator fetch from page {start_page} (based on status file).")
        logger.info(f"Resuming legislator fetch from page {start_page}")

    all_legislator_items = []
    page_num = start_page # 시작 페이지 설정
    items_per_page = 100
    PARAM_NAME_PAGE = 'page'
    PARAM_NAME_LIMIT = 'pageSize'
    total_count = 0 # 루프 내에서 첫 페이지 응답으로 설정됨

    while True:
        params = { PARAM_NAME_PAGE: page_num, PARAM_NAME_LIMIT: items_per_page }
        logger.info(f"Fetching legislator page {page_num} (pageSize {items_per_page}) from: {MEMBERS_ENDPOINT}")
        print(f"Fetching legislator page {page_num}...")
        page_data = fetch_api_data(MEMBERS_ENDPOINT, params=params)

        if not page_data:
            logger.error(f"Failed to fetch legislator page {page_num}, stopping pagination.")
            print(f"Error: Failed to fetch legislator page {page_num}. Stopping.")
            # 실패 시에는 상태 업데이트를 하지 않음 (다음 실행 시 같은 페이지 재시도)
            break

        # 첫 페이지(또는 재개 후 첫 페이지)에서 totalCount 가져오기 시도
        if page_num == start_page and total_count == 0: # total_count가 아직 설정 안됐을 때만
             pagination_data = page_data.get('pagination', page_data)
             temp_total_count = pagination_data.get('totalCount') # 임시 변수 사용
             if temp_total_count is not None:
                 total_count = temp_total_count
                 logger.info(f"Total legislator records reported by API: {total_count}")
                 print(f"API reported total legislators: {total_count}")
                 if total_count == 0:
                     logger.info("No legislator records to fetch.")
                     print("No legislator records to fetch.")
                     # 데이터가 0개이면 완료 상태 저장하고 종료
                     save_status({'legislators_last_page': 0}, status_file) # 0으로 저장하여 다음엔 1부터 시작
                     break
             else:
                 logger.warning("Could not find 'totalCount' in API response for /members. Pagination might not stop correctly.")
                 print("Warning: Could not determine total legislator count from API.")

        items_on_page = page_data.get('rows', [])
        print(f"Fetched {len(items_on_page)} items from page {page_num}.")

        if not items_on_page:
             # 재개 후 첫 페이지가 비어있을 수도 있으므로 page_num > 1 조건 제거
             # total_count가 0이 아니고, items_on_page가 비었다면 종료
             if total_count != 0:
                logger.info(f"No more legislator items found on page {page_num}. Assuming finished fetching.")
                print("No more items found on subsequent pages. Fetching finished.")
                # 완료 상태 저장: 마지막 성공 페이지 기록
                save_status({'legislators_last_page': page_num -1 if page_num > 1 else 0}, status_file)
                break
             # total_count가 0이면 위에서 이미 처리됨
             # total_count를 얻지 못했다면(None), 첫 페이지부터 비어있지 않는 한 계속 진행

        all_legislator_items.extend(items_on_page)
        logger.info(f"Total items fetched in this run (starting from page {start_page}): {len(all_legislator_items)}")
        # 전체 누적 개수 대신 이번 실행에서 가져온 개수를 보여주는 것이 덜 혼란스러울 수 있음

        # ===== 상태 저장: 현재 페이지 처리 성공 직후 =====
        # (DB 저장 전에 상태를 저장하면, DB 저장 중 실패 시 다음 실행때 이 페이지는 건너뛰게 됨)
        # (DB 저장 *후에* 상태를 저장하면, DB 저장 중 실패 시 다음 실행때 이 페이지를 *다시* 가져오고 처리하게 됨 - update_or_create가 중복 방지)
        # 여기서는 DB 저장 *후에* 상태를 저장하는 것이 더 안전해 보임 (아래 DB 처리 로직 후로 이동 고려)
        # --> 일단 페이지 fetch 성공 시 저장 (간단한 방식)
        save_status({'legislators_last_page': page_num}, status_file)
        # =============================================

        if total_count is not None and total_count > 0:
            # total_count 기반 종료 조건은 실제 API 응답 구조에 맞춰 조정 필요
            # 예시: total_count와 현재까지 가져온 총 아이템 수가 일치하면 종료 (단, 이건 전체 아이템 수를 알아야 함)
            # 여기서는 페이지네이션으로 더 이상 아이템이 안 나올 때까지 도는 것으로 가정
            estimated_total_pages = math.ceil(total_count / items_per_page)
            if page_num >= estimated_total_pages:
                logger.info(f"Reached estimated last page ({estimated_total_pages}). Assuming finished fetching.")
                print("Reached estimated last page. Fetching finished.")
                # 완료 상태 저장
                save_status({'legislators_last_page': page_num}, status_file)
                break

        page_num += 1
        time.sleep(0.5)

    # --- DB 저장 로직 ---
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    total_rows_to_process = len(all_legislator_items) # 이번 실행에서 가져온 데이터만 처리

    if total_rows_to_process == 0:
        print("No new legislator records fetched in this run to save to the database.")
        return 0, 0, 0

    print(f"\nStarting database process for {total_rows_to_process} legislator records (fetched in this run).")
    PROGRESS_INTERVAL = 50

    for i, member_info in enumerate(all_legislator_items):
        if (i + 1) % PROGRESS_INTERVAL == 0 or (i + 1) == total_rows_to_process:
             print(f"  Processing DB record {i+1} / {total_rows_to_process}...")

        member_id = member_info.get('id')
        # ... (기존 DB 저장 로직과 동일) ...
        if not member_id:
            logger.warning(f"Skipping member due to missing ID: {member_info.get('name', 'N/A')}")
            print(f"  [SKIP] Missing ID for member: {member_info.get('name', 'N/A')}")
            skipped_count += 1
            continue

        defaults = {
            'name': member_info.get('name'),
            'party': member_info.get('partyName'),
            'gender': member_info.get('gender'),
            'reelected': member_info.get('reelected'),
            'electoral_district': member_info.get('electoralDistrict'),
            'latest_age': member_info.get('latestAge'),
        }
        defaults = {k: v for k, v in defaults.items() if v is not None}

        try:
            legislator, created = Legislator.objects.update_or_create(
                member_id=member_id,
                defaults=defaults
            )
            if created:
                saved_count += 1
            else:
                updated_count += 1
        except IntegrityError as e:
            logger.error(f"DB IntegrityError saving legislator {member_id} ({member_info.get('name')}): {e}")
            print(f"  [DB SKIP] IntegrityError for legislator {member_id} ({member_info.get('name')}): {e}")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Unexpected error saving legislator {member_id}: {e}", exc_info=True)
            print(f"  [DB SKIP] Unexpected error for legislator {member_id}: {e}")
            skipped_count += 1


    print(f"\nLegislator database process finished for this run.")
    print(f"Processed: {total_rows_to_process}, Saved: {saved_count}, Updated: {updated_count}, Skipped: {skipped_count}")
    return saved_count, updated_count, skipped_count


# --- save_assets 함수 (상태 관리 및 파일 이어쓰기 추가) ---
def save_assets(max_pages=0, output_file_path=None, status_file=DEFAULT_STATUS_FILE): # 인자 추가
    """/assets API 데이터를 처리 (상태 관리, 파일 이어쓰기 기능 추가)"""
    print("\n--- Fetching Asset Data (Paginated with Params) ---")
    logger.info(f"--- Starting save_assets ---")
    logger.info(f"Received max_pages: {max_pages}")
    logger.info(f"Received output_file_path: {output_file_path}")

    # 상태 로드하여 시작 페이지 결정
    status_data = load_status(status_file)
    start_page = status_data.get('assets_last_page', 0) + 1
    if start_page > 1:
        print(f"Resuming asset fetch from page {start_page} (based on status file).")
        logger.info(f"Resuming asset fetch from page {start_page}")

    # max_pages 제한이 있고, 시작 페이지가 이미 제한을 넘었으면 실행 안 함
    if max_pages > 0 and start_page > max_pages:
        print(f"Start page ({start_page}) exceeds max_pages ({max_pages}). Nothing to fetch.")
        logger.info(f"Start page ({start_page}) exceeds max_pages ({max_pages}). Skipping asset fetch.")
        return 0, 0, 0

    all_asset_items = []
    page_num = start_page # 시작 페이지 설정
    items_per_page = 100
    PARAM_NAME_PAGE = 'page'
    PARAM_NAME_LIMIT = 'limit'
    total_count = None # 루프 내에서 첫 페이지 응답으로 설정됨

    # --- 파일 출력 모드 설정 (이어쓰기 지원) ---
    csv_writer = None
    csv_file = None
    fieldnames = [
        'api_asset_id', 'api_member_id',
        'api_date', 'api_type', 'api_kind',
        'api_relation', 'api_detail', 'api_current_valuation', 'api_origin_valuation',
        'api_increased_amount', 'api_decreased_amount', 'api_reason_change',
    ]
    file_exists = False
    if output_file_path:
        file_exists = os.path.exists(output_file_path)
        # 이어쓰기 모드 결정: 상태 파일 기준 start_page > 1 이고 파일이 존재하면 'a', 아니면 'w'
        open_mode = 'a' if start_page > 1 and file_exists else 'w'
        try:
            csv_file = open(output_file_path, open_mode, newline='', encoding='utf-8')
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            # 헤더는 새로 파일을 만들거나 이어쓰기인데 파일이 없던 경우에만 작성
            if open_mode == 'w' or not file_exists:
                csv_writer.writeheader()
                print(f"Output file mode: Writing header and results to {output_file_path}")
            else:
                print(f"Output file mode: Appending results to existing file {output_file_path}")
            logger.info(f"Opened {output_file_path} in '{open_mode}' mode.")
        except IOError as e:
            logger.error(f"Error opening output file {output_file_path}: {e}. Aborting asset processing.", exc_info=True)
            print(f"Error: Could not open output file {output_file_path}. Aborting.")
            if csv_file: csv_file.close()
            # 실패 시에는 상태 업데이트를 하지 않음
            return 0, 0, 0 # 에러 발생 시 processed 0, skipped 0 반환

    # --- API 데이터 가져오기 루프 ---
    processed_in_this_run = 0 # 이번 실행에서 처리한 총 아이템 수 (DB/파일 무관)
    items_fetched_in_this_run = 0 # 이번 실행에서 가져온 아이템 수

    while True:
        # max_pages 제한 확인
        if max_pages > 0 and page_num > max_pages:
            logger.info(f"Reached max_pages limit ({max_pages}) at page {page_num}. Stopping fetch.")
            print(f"Reached max_pages limit ({max_pages}). Stopping fetch.")
            # 완료된 마지막 페이지 저장
            save_status({'assets_last_page': page_num - 1}, status_file)
            break

        params = {PARAM_NAME_PAGE: page_num, PARAM_NAME_LIMIT: items_per_page}
        logger.info(f"\n>>> Fetching asset page {page_num}")
        print(f"Fetching asset page {page_num}...")
        page_data = fetch_api_data(ASSETS_ENDPOINT, params=params)

        if not page_data:
            logger.error(f"!!! Breaking loop: fetch_api_data returned None for page {page_num}")
            print(f"Error: Failed to fetch asset page {page_num}. Stopping.")
            # 실패 시 상태 업데이트 안 함
            break

        # 첫 페이지(또는 재개 후 첫 페이지)에서 totalCount 가져오기
        if page_num == start_page and total_count is None:
            logger.info("--- First page data received (in this run) ---")
            if 'pagination' in page_data and 'totalCount' in page_data['pagination']:
                total_count = page_data['pagination']['totalCount']
                logger.info(f"Extracted total_count: {total_count}")
                print(f"API reported total assets: {total_count}")
                if total_count == 0:
                     logger.info("No asset records reported by API.")
                     print("No asset records to fetch.")
                     save_status({'assets_last_page': 0}, status_file) # 완료 상태 저장
                     break # 가져올 데이터 없음
            else:
                logger.warning("!!! Could not extract 'pagination.totalCount' from first page response. Total count based loop break disabled.")
                print("Warning: Could not determine total asset count from API.")

        items_on_page = page_data.get('rows', [])
        logger.info(f"Items found on page {page_num}: {len(items_on_page)}")
        print(f"Fetched {len(items_on_page)} items from asset page {page_num}.")

        if not items_on_page:
            if total_count != 0: # total_count 가 0이 아닐 때만 빈 페이지를 종료로 간주
                logger.info(f"!!! Breaking loop: No items found on page {page_num}. Assuming finished.")
                print("No more items found on subsequent pages. Fetching finished.")
                # 완료 상태 저장
                save_status({'assets_last_page': page_num - 1 if page_num > 1 else 0}, status_file)
                break
            # total_count가 0이거나 None이면 빈 페이지라도 계속 시도할 수 있음 (혹은 API 오류일 수도)
            # 여기서는 total_count가 0이 아니면 종료하는 것으로 가정

        items_fetched_in_this_run += len(items_on_page)
        all_asset_items.extend(items_on_page) # 이번 실행에서 가져온 것만 추가
        logger.info(f"Total items fetched in this run so far: {items_fetched_in_this_run}")
        print(f"Total asset items fetched in this run so far: {items_fetched_in_this_run}")

        # ===== 상태 저장: 현재 페이지 fetch 성공 직후 =====
        save_status({'assets_last_page': page_num}, status_file)
        # =============================================

        # total_count 기반 종료 조건 (Optional, 추정치 기반)
        if total_count is not None and total_count > 0:
            estimated_total_pages = math.ceil(total_count / items_per_page)
            if page_num >= estimated_total_pages:
                logger.info(f"Reached estimated last page ({estimated_total_pages}). Assuming finished fetching.")
                print("Reached estimated last page. Fetching finished.")
                # 완료 상태 저장
                save_status({'assets_last_page': page_num}, status_file)
                break

        logger.info(f"Incrementing page_num from {page_num} to {page_num + 1}")
        page_num += 1
        time.sleep(0.5)

    print(f"\nFinished fetching pages for this run. Total asset items retrieved: {items_fetched_in_this_run}")

    # --- DB 저장 또는 파일 출력 처리 ---
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    written_to_file_count = 0 # 파일에 쓰여진 레코드 수 (이번 실행)
    total_rows_to_process = len(all_asset_items) # 이번 실행에서 가져온 데이터 수

    if total_rows_to_process == 0:
        print("No new asset records fetched in this run to process.")
        if csv_file: csv_file.close() # 파일 핸들 닫기
        return 0, 0, 0

    # --- 의원 정보 로드 (DB 모드일 때만, 매번 실행 시 로드) ---
    legislators_dict = {}
    if not output_file_path:
        # ... (기존 의원 로드 로직과 동일) ...
        logger.info("DB mode: Loading all legislators into memory...")
        print("DB mode: Loading legislators...")
        try:
            legislators_dict = {leg.member_id: leg for leg in Legislator.objects.all()}
            logger.info(f"Loaded {len(legislators_dict)} legislators.")
            print(f"Loaded {len(legislators_dict)} legislators.")
            if not legislators_dict:
                 logger.warning("No legislators found in the database. Assets cannot be linked.")
                 print("Warning: No legislators found in DB. Assets cannot be saved.")
        except Exception as e:
            logger.error(f"Error loading legislators: {e}. Asset processing cannot continue.", exc_info=True)
            print(f"Error: Failed loading legislators: {e}. Aborting.")
            if csv_file: csv_file.close()
            return 0, 0, total_rows_to_process # 처리 불가로 스킵 처리

    print(f"\nStarting data processing for {total_rows_to_process} asset records (fetched in this run) {'(Output File Mode)' if output_file_path else '(Database Mode)'}.")
    PROGRESS_INTERVAL = 50

    # --- 데이터 처리 루프 ---
    for i, item in enumerate(all_asset_items):
        processed_in_this_run += 1 # 실제로 처리 시작하는 아이템 수 계산

        if (i + 1) % PROGRESS_INTERVAL == 0 or (i + 1) == total_rows_to_process:
             print(f"  Processing record {i+1} / {total_rows_to_process}...")

        # ... (기존 유효성 검사 로직 시작) ...
        result_data = {fname: None for fname in fieldnames} if csv_writer else {}
        # API 데이터 추출...
        openwatch_asset_id = item.get('id')
        national_assembly_member_id = item.get('nationalAssemblyMemberId')
        # ... (나머지 필드 추출) ...
        date_str = item.get('date')
        asset_type_api = item.get('type')
        kind_api = item.get('kind')
        relation_api = item.get('relation')
        detail_api = item.get('detail')
        reason_api = item.get('reason')
        current_valuation_api = item.get('currentValuation') or item.get('currentValutaion')
        origin_valuation_api = item.get('originValuation')
        increased_amount_api = item.get('increasedAmount')
        decreased_amount_api = item.get('decreasedAmount')

        if csv_writer:
             result_data.update({
                 'api_asset_id': openwatch_asset_id,
                 'api_member_id': national_assembly_member_id,
                 'api_date': date_str,
                 'api_type': asset_type_api,
                 'api_kind': kind_api,
                 'api_relation': relation_api,
                 'api_detail': detail_api,
                 'api_current_valuation': current_valuation_api,
                 'api_origin_valuation': origin_valuation_api,
                 'api_increased_amount': increased_amount_api,
                 'api_decreased_amount': decreased_amount_api,
                 'api_reason_change': reason_api,
             })

        # 유효성 검사...
        _status = "Valid"
        _reason = ""
        should_skip = False

        # 1. 필수 정보 누락...
        missing_fields = []
        if not openwatch_asset_id: missing_fields.append("id")
        if not national_assembly_member_id: missing_fields.append("nationalAssemblyMemberId")
        if not date_str: missing_fields.append("date")
        if not asset_type_api: missing_fields.append("type")
        if not relation_api: missing_fields.append("relation")
        if not detail_api: missing_fields.append("detail")
        if missing_fields:
            _status = "Skipped"
            _reason = f"Missing fields: {', '.join(missing_fields)}"
            should_skip = True
            logger.warning(f"Skipping asset ({_reason}) - API ID: {openwatch_asset_id}")
            print(f"  [SKIP] Asset ID {openwatch_asset_id}: {_reason}")

        # 2. 의원 정보 확인...
        legislator_obj = None
        if not should_skip:
            if not output_file_path: # DB 모드
                legislator_obj = legislators_dict.get(national_assembly_member_id)
                if legislator_obj is None:
                    _reason = f"Legislator '{national_assembly_member_id}' not found in preloaded dict."
                    should_skip = True
                    # (로그 및 print 출력...)
                    print(f"  [SKIP] Asset ID {openwatch_asset_id}: {_reason}")
            else: # 파일 모드
                 try:
                     if not Legislator.objects.filter(member_id=national_assembly_member_id).exists():
                         _reason = f"Legislator '{national_assembly_member_id}' not found in DB."
                         should_skip = True
                         # (로그 및 print 출력...)
                         print(f"  [SKIP] Asset ID {openwatch_asset_id}: {_reason}")
                 except Exception as db_e:
                     logger.error(f"DB check error for legislator {national_assembly_member_id}: {db_e}")
                     print(f"  [WARN] DB check error for legislator {national_assembly_member_id}: {db_e}")

        # 3. 날짜 파싱...
        report_year, report_month = None, None
        if not should_skip:
            try:
                report_year, report_month = Asset.parse_date_string(date_str)
                if report_year is None or report_month is None: raise ValueError("Parsing returned None")
            except AttributeError:
                 _reason = "Asset model missing 'parse_date_string' method"
                 should_skip = True
                 # (로그 및 print 출력...)
                 print(f"  [SKIP] Asset ID {openwatch_asset_id}: {_reason}")
            except Exception as e:
                 _reason = f"Failed to parse date string '{date_str}': {e}"
                 should_skip = True
                 # (로그 및 print 출력...)
                 print(f"  [SKIP] Asset ID {openwatch_asset_id}: {_reason}")


        # --- 스킵 결정 및 처리 ---
        if should_skip:
            skipped_count += 1
            continue # 다음 레코드로

        # --- 스킵되지 않은 레코드 처리 ---
        if not output_file_path: # DB 저장 모드
            # ... (기존 DB 저장 defaults 설정 및 try-except 블록) ...
            defaults = {
                'legislator': legislator_obj, 'report_year': report_year, 'report_month': report_month,
                'asset_type': asset_type_api, 'kind': kind_api, 'relation': relation_api, 'detail': detail_api,
                'current_valuation': current_valuation_api, 'reason_for_change': reason_api,
                'origin_valuation': origin_valuation_api, 'increased_amount': increased_amount_api,
                'decreased_amount': decreased_amount_api,
            }
            defaults = {k: v for k, v in defaults.items() if v is not None}
            try:
                asset, created = Asset.objects.update_or_create(
                    openwatch_asset_id=openwatch_asset_id, defaults=defaults
                )
                if created: saved_count += 1
                else: updated_count += 1
            except IntegrityError as e:
                 logger.error(f"Skipping asset (ID: {openwatch_asset_id}): DB IntegrityError: {e}")
                 print(f"  [DB SKIP] IntegrityError for asset {openwatch_asset_id}: {e}")
                 skipped_count += 1
            except Exception as e:
                logger.error(f"Skipping asset (ID: {openwatch_asset_id}): DB Error during save/update: {e}", exc_info=True)
                print(f"  [DB SKIP] Unexpected error for asset {openwatch_asset_id}: {e}")
                skipped_count += 1
        else: # 파일 출력 모드 (유효성 검사 통과 시)
            try:
                 csv_writer.writerow(result_data)
                 written_to_file_count += 1
            except Exception as write_e:
                 logger.error(f"CSV write error for asset {openwatch_asset_id}: {write_e}")
                 print(f"  [WARN] CSV write error for asset {openwatch_asset_id}: {write_e}")
                 skipped_count += 1 # 파일 쓰기 실패도 스킵으로 간주

    # --- 루프 종료 후 처리 ---
    if csv_file:
        try:
             csv_file.close()
        except Exception as close_e:
             logger.error(f"Error closing output file {output_file_path}: {close_e}")
             print(f"Warning: Error closing output file {output_file_path}: {close_e}")
        print(f"\nProcessing finished for this run. Results appended to {output_file_path}")
        print(f"Items processed in this run: {processed_in_this_run}, Validation Skipped: {skipped_count}, Written to file: {written_to_file_count}")
        logger.info(f"Asset processing finished (File Output Mode - Run). Processed: {processed_in_this_run}, Skipped: {skipped_count}, Written: {written_to_file_count}.")
        return 0, 0, skipped_count # DB 기준 반환값

    else: # DB 모드
        print(f"\nAsset database process finished for this run.")
        print(f"Items processed in this run: {processed_in_this_run}, Saved: {saved_count}, Updated: {updated_count}, Skipped: {skipped_count}")
        logger.info(f"Asset database process finished (Run). Processed: {processed_in_this_run}, Saved: {saved_count}, Updated: {updated_count}, Skipped: {skipped_count}")
        return saved_count, updated_count, skipped_count
