import pandas as pd
import re

# 채무, 정치자금법에 따른~~ 데이터 항목 및 금액 분리

# --- 설정 ---
INPUT_CSV_FILE = 'converted_asset_data2_20250606_161738.csv'
OUTPUT_CSV_FILE = 'converted_asset_data3_20250606_161738.csv' # 출력 파일 이름 변경

ASSET_TYPE_COLUMN_NAME = '자산구분'
DETAIL_COLUMN_NAME_ORIGINAL = '소재지 면적 등 권리의 명세'

COL_PREVIOUS_VALUE = '종전가액'
COL_INCREASE_VALUE = '증가액'
COL_DECREASE_VALUE = '감소액'
COL_CURRENT_VALUE = '현재가액'

# 새로운 자산구분 값 정의
ASSET_TYPE_POLITICAL_FUND = '정치자금법에 따른 정치자금의 수입 및 지출을 위한 예금계좌의 예금'
ASSET_TYPE_DEBT = '채무'

def clean_value(value_str):
    if pd.isna(value_str) or str(value_str).strip() == "": return 0
    try: return int(str(value_str).replace(',', '').strip())
    except ValueError: return 0

def extract_name_for_political_fund(detail_string_original):
    """정치자금예금 명세에서 이름만 추출합니다."""
    if pd.isna(detail_string_original) or str(detail_string_original).strip() == "":
        return None
    detail_string = str(detail_string_original).strip()
    match = re.match(r"(.+?)(?=\s*[\d(])|(.*)", detail_string)
    if match:
        name = match.group(1) if match.group(1) else match.group(2)
        return name.strip(' ,') if name else None
    return detail_string.strip(' ,')

# "채무" 처리를 위한 파싱 함수
def parse_financial_items_for_debt(detail_string_original): # 함수 이름 변경
    parsed_items = []
    if pd.isna(detail_string_original) or str(detail_string_original).strip() == "":
        parsed_items.append({DETAIL_COLUMN_NAME_ORIGINAL: None, COL_PREVIOUS_VALUE: 0, COL_INCREASE_VALUE: 0, COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0})
        return parsed_items

    detail_string = str(detail_string_original)
    item_pattern = re.compile(
        r"(.+?)\s*([\d,]+)(?:\s*\(\s*([\d,]+)\s*(증\s*가|감\s*소)\s*\))?"
    )
    current_pos = 0
    processed_something_in_loop = False
    while current_pos < len(detail_string):
        match = item_pattern.match(detail_string, current_pos)
        if match:
            processed_something_in_loop = True
            item_name_raw = match.group(1)
            item_name = item_name_raw.strip(' ,')
            current_value_str = match.group(2)
            change_amount_str = match.group(3)
            change_type_raw = match.group(4)
            current_value = clean_value(current_value_str)
            increase_value = 0; decrease_value = 0; previous_value = 0
            change_type = None
            if change_type_raw: change_type = "".join(change_type_raw.split())
            if change_amount_str and change_type:
                change_amount = clean_value(change_amount_str)
                if change_type == '증가':
                    increase_value = change_amount
                    previous_value = current_value - increase_value
                elif change_type == '감소':
                    decrease_value = change_amount
                    previous_value = current_value + decrease_value
            else: previous_value = current_value
            parsed_items.append({
                DETAIL_COLUMN_NAME_ORIGINAL: item_name,
                COL_PREVIOUS_VALUE: previous_value, COL_INCREASE_VALUE: increase_value,
                COL_DECREASE_VALUE: decrease_value, COL_CURRENT_VALUE: current_value
            })
            current_pos = match.end()
            if current_pos < len(detail_string) and detail_string[current_pos] == ',': current_pos += 1
            while current_pos < len(detail_string) and detail_string[current_pos].isspace(): current_pos +=1
        else: 
            remaining_text = detail_string[current_pos:].strip(' ,')
            if remaining_text:
                if not (re.fullmatch(r"\(?\s*(?:증\s*가|감\s*소)\s*\)?", remaining_text, re.IGNORECASE) or \
                        re.fullmatch(r"(?:증\s*가|감\s*소)\s*\)?", remaining_text, re.IGNORECASE) or \
                        re.fullmatch(r"\(?\s*(?:증\s*가|감\s*소)", remaining_text, re.IGNORECASE)):
                    # print(f"정보 (채무): 패턴에 맞지 않는 남은 텍스트를 '이름만 있는 항목'으로 처리: '{remaining_text}'. 원본: '{detail_string_original}'")
                    parsed_items.append({
                        DETAIL_COLUMN_NAME_ORIGINAL: remaining_text,
                        COL_PREVIOUS_VALUE: 0, COL_INCREASE_VALUE: 0, COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0
                    })
                    processed_something_in_loop = True
            break 
    if not processed_something_in_loop and str(detail_string_original).strip():
        cleaned_original = str(detail_string_original).strip(' ,')
        if cleaned_original:
            # print(f"경고 (채무): 전체 명세 문자열을 파싱하지 못했습니다: '{detail_string_original}'. 전체를 단일 항목으로 처리합니다.")
            parsed_items.append({
                DETAIL_COLUMN_NAME_ORIGINAL: cleaned_original,
                COL_PREVIOUS_VALUE: 0, COL_INCREASE_VALUE: 0, COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0
            })
    if not parsed_items:
        parsed_items.append({DETAIL_COLUMN_NAME_ORIGINAL: str(detail_string_original).strip(' ,') if pd.notna(detail_string_original) and str(detail_string_original).strip() else None, 
                             COL_PREVIOUS_VALUE: 0, COL_INCREASE_VALUE: 0, 
                             COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0})
    return parsed_items

# --- 메인 실행 로직 ---
current_df_index = -1
current_row_content_for_log = None

try:
    df = pd.read_csv(INPUT_CSV_FILE, encoding='utf-8-sig')
    print(f"'{INPUT_CSV_FILE}' 파일을 'utf-8-sig' 인코딩으로 성공적으로 읽었습니다.")
    original_row_count = len(df)
    print(f"원본 데이터 행 수: {original_row_count}")

    required_columns = [ASSET_TYPE_COLUMN_NAME, DETAIL_COLUMN_NAME_ORIGINAL,
                        COL_PREVIOUS_VALUE, COL_INCREASE_VALUE,
                        COL_DECREASE_VALUE, COL_CURRENT_VALUE]
    for col in required_columns:
        if col not in df.columns:
            print(f"오류: 필수 열 '{col}'을(를) 찾을 수 없습니다. CSV 파일의 헤더를 확인하고 코드의 변수 설정을 수정해주세요.")
            print(f"현재 CSV 파일의 열: {df.columns.tolist()}")
            exit()

    all_new_rows = []
    for index, row in df.iterrows():
        current_df_index = index
        current_row_content_for_log = row[DETAIL_COLUMN_NAME_ORIGINAL]
        asset_type = row[ASSET_TYPE_COLUMN_NAME]

        if asset_type == ASSET_TYPE_DEBT: # "채무" 처리
            detail_text_to_parse = row[DETAIL_COLUMN_NAME_ORIGINAL]
            detail_items_list = parse_financial_items_for_debt(detail_text_to_parse) # 채무용 파싱 함수 사용
            
            for item_data_dict in detail_items_list:
                new_row_data = row.to_dict()
                new_row_data[DETAIL_COLUMN_NAME_ORIGINAL] = item_data_dict.get(DETAIL_COLUMN_NAME_ORIGINAL)
                new_row_data[COL_PREVIOUS_VALUE] = item_data_dict.get(COL_PREVIOUS_VALUE)
                new_row_data[COL_INCREASE_VALUE] = item_data_dict.get(COL_INCREASE_VALUE)
                new_row_data[COL_DECREASE_VALUE] = item_data_dict.get(COL_DECREASE_VALUE)
                new_row_data[COL_CURRENT_VALUE] = item_data_dict.get(COL_CURRENT_VALUE)
                all_new_rows.append(new_row_data)

        elif asset_type == ASSET_TYPE_POLITICAL_FUND: # "정치자금예금" 처리
            row_dict = row.to_dict()
            original_detail_text = row_dict[DETAIL_COLUMN_NAME_ORIGINAL]
            extracted_name = extract_name_for_political_fund(original_detail_text)
            row_dict[DETAIL_COLUMN_NAME_ORIGINAL] = extracted_name
            
            row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
            row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
            row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
            row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))
            all_new_rows.append(row_dict)
            
        else: # "예금" 포함 그 외 모든 자산구분은 특별한 명세 파싱 없이 그대로 유지
            row_dict = row.to_dict()
            # 금액 관련 열들만 숫자형으로 정리
            row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
            row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
            row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
            row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))
            all_new_rows.append(row_dict)
            
    expanded_df = pd.DataFrame(all_new_rows)
    print(f"처리 후 데이터 행 수: {len(expanded_df)}")
    
    if 'df' in locals() and hasattr(df, 'columns'):
        original_cols = df.columns.tolist()
        current_cols = expanded_df.columns.tolist()
        final_cols = [col for col in original_cols if col in current_cols]
        for col in current_cols:
            if col not in final_cols:
                final_cols.append(col)
        expanded_df = expanded_df[final_cols]

    expanded_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8-sig')
    print(f"처리된 데이터가 '{OUTPUT_CSV_FILE}' 파일로 저장되었습니다.")

except FileNotFoundError:
    print(f"오류: '{INPUT_CSV_FILE}' 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해주세요.")
except KeyError as e:
    print(f"★★★★★ KeyError 발생 ★★★★★")
    print(f"오류 메시지: 열 '{e}'을(를) 찾을 수 없습니다.")
    if current_df_index != -1:
        print(f"오류 발생 추정 위치: 원본 CSV 파일의 {current_df_index + 2}번째 행 (헤더 포함).")
        print(f"오류 발생 시 DataFrame 인덱스: {current_df_index}")
        if current_row_content_for_log is not None:
             print(f"오류 발생 시 행의 '{DETAIL_COLUMN_NAME_ORIGINAL}' 내용: {current_row_content_for_log}")
    if 'df' in locals() and hasattr(df, 'columns'): print(f"현재 CSV 파일의 열 목록: {df.columns.tolist()}")
    if 'expanded_df' in locals() and hasattr(expanded_df, 'columns'): print(f"처리된 DataFrame의 열 목록: {expanded_df.columns.tolist()}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"★★★★★ 처리 중 일반 오류가 발생했습니다 ★★★★★")
    print(f"오류 유형: {type(e).__name__}")
    print(f"오류 메시지: {e}")
    if current_df_index != -1:
        print(f"오류 발생 추정 위치: 원본 CSV 파일의 {current_df_index + 2}번째 행 (헤더 포함).")
        print(f"오류 발생 시 DataFrame 인덱스: {current_df_index}")
        if current_row_content_for_log is not None:
             print(f"오류 발생 시 행의 '{DETAIL_COLUMN_NAME_ORIGINAL}' 내용: {current_row_content_for_log}")
    import traceback
    traceback.print_exc()