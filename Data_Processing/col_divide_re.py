import pandas as pd
import re

# 에금 및 채무 데이터 항목, 금액 조건(종전가액,증가액,감소액,현재가액)에 따른 분리 강화

# --- 설정 ---
INPUT_CSV_FILE = 'new_data14_0526_2053.csv'
OUTPUT_CSV_FILE = 'new_data19.csv' # 테스트용 출력 파일

ASSET_TYPE_COLUMN_NAME = '자산구분'
DETAIL_COLUMN_NAME_ORIGINAL = '소재지 면적 등 권리의 명세'

COL_PREVIOUS_VALUE = '종전가액'
COL_INCREASE_VALUE = '증가액'
COL_DECREASE_VALUE = '감소액'
COL_CURRENT_VALUE = '현재가액'

ASSET_TYPE_DEPOSIT_VAL = '예금'
ASSET_TYPE_DEBT_VAL = '채무'


def clean_value(value_str):
    if pd.isna(value_str) or str(value_str).strip() == "": return 0
    try: return int(str(value_str).replace(',', '').strip())
    except ValueError: return 0

def is_parsable_detail_string(detail_string):
    if pd.isna(detail_string) or not str(detail_string).strip():
        return False # 비어있으면 파싱 대상 아님
    
    s = str(detail_string)
    # 숫자(하나 이상) 또는 여는 괄호 '(' 가 포함되어 있으면 파싱 대상으로 간주
    if re.search(r'\d+ | \(', s): # 숫자 뒤 공백, 또는 여는 괄호 앞 공백을 고려 (더 정확하게는 금액 패턴 확인)
                                 # 더 간단하게는 그냥 숫자나 괄호 존재 유무만 봐도 됨
        # 좀 더 정확한 패턴: 이름 뒤에 공백/숫자 또는 공백/괄호가 오는 경우
        # 아래 패턴은 "이름"만 있는 경우와 "이름 숫자..." 형태를 구분하려는 시도
        # 만약 이름 뒤에 바로 숫자나 (가 오면 파싱 대상
        if re.search(r"\S\s+[\d(]", s) or re.search(r"\S[\d(]", s): # 문자 뒤 공백 후 숫자/( 또는 문자뒤 바로 숫자/(
             # 하지만 이 방법도 완벽하지 않을 수 있음.
             # 가장 확실한 건, 현재 parse 함수의 item_pattern과 유사한 패턴이 존재하는지 보는 것.
             # 아래는 단순화된 체크: 숫자나 괄호가 있으면 일단 파싱 시도
             if re.search(r'\d', s) or re.search(r'\(', s):
                 return True
    return False

def parse_financial_details_for_expansion_core(detail_string_original):
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
            item_name_raw = match.group(1); item_name = item_name_raw.strip(' ,')
            current_value_str = match.group(2)
            change_amount_str = match.group(3); change_type_raw = match.group(4)
            current_value = clean_value(current_value_str)
            increase_value = 0; decrease_value = 0; previous_value = 0
            change_type = None
            if change_type_raw: change_type = "".join(change_type_raw.split())
            if change_amount_str and change_type:
                change_amount = clean_value(change_amount_str)
                if change_type == '증가': increase_value = change_amount; previous_value = current_value - increase_value
                elif change_type == '감소': decrease_value = change_amount; previous_value = current_value + decrease_value
            else: previous_value = current_value
            parsed_items.append({
                DETAIL_COLUMN_NAME_ORIGINAL: item_name, COL_PREVIOUS_VALUE: previous_value, 
                COL_INCREASE_VALUE: increase_value, COL_DECREASE_VALUE: decrease_value, 
                COL_CURRENT_VALUE: current_value
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
                    # print(f"정보 (core_parser): 패턴 미일치, 남은 텍스트를 '이름만' 항목으로 처리: '{remaining_text}' (원본: '{detail_string_original}')")
                    parsed_items.append({
                        DETAIL_COLUMN_NAME_ORIGINAL: remaining_text, COL_PREVIOUS_VALUE: 0, 
                        COL_INCREASE_VALUE: 0, COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0
                    })
                    processed_something_in_loop = True
            break 
    if not processed_something_in_loop and str(detail_string_original).strip():
        cleaned_original = str(detail_string_original).strip(' ,')
        if cleaned_original:
            # print(f"경고 (core_parser): 전체 명세 문자열 파싱 실패: '{detail_string_original}'. 전체를 단일 항목으로 처리.")
            parsed_items.append({
                DETAIL_COLUMN_NAME_ORIGINAL: cleaned_original, COL_PREVIOUS_VALUE: 0, 
                COL_INCREASE_VALUE: 0, COL_DECREASE_VALUE: 0, COL_CURRENT_VALUE: 0
            })
    if not parsed_items:
        final_name_if_empty = str(detail_string_original).strip(' ,') if pd.notna(detail_string_original) and str(detail_string_original).strip() else None
        parsed_items.append({DETAIL_COLUMN_NAME_ORIGINAL: final_name_if_empty, 
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
            print(f"오류: 필수 열 '{col}'을(를) 찾을 수 없습니다.")
            exit()

    all_new_rows = []
    for index, row in df.iterrows():
        current_df_index = index
        current_row_content_for_log = row.get(DETAIL_COLUMN_NAME_ORIGINAL, "N/A")
        asset_type = str(row[ASSET_TYPE_COLUMN_NAME]).strip()
        row_dict_original = row.to_dict()

        if asset_type == ASSET_TYPE_DEPOSIT_VAL or asset_type == ASSET_TYPE_DEBT_VAL:
            detail_text_to_parse = row[DETAIL_COLUMN_NAME_ORIGINAL]
            
            # *** 명세열 형태에 따른 조건부 처리 ***
            if is_parsable_detail_string(detail_text_to_parse):
                # 명세열이 복잡한 형태 -> 파싱 및 행 확장
                # print(f"파싱 대상 명세: {detail_text_to_parse}") # 디버깅용
                detail_items_list = parse_financial_details_for_expansion_core(detail_text_to_parse)
                
                if not detail_items_list:
                    all_new_rows.append(row_dict_original)
                    continue

                for item_data_dict in detail_items_list:
                    expanded_row_data = row_dict_original.copy()
                    expanded_row_data[DETAIL_COLUMN_NAME_ORIGINAL] = item_data_dict.get(DETAIL_COLUMN_NAME_ORIGINAL)
                    expanded_row_data[COL_PREVIOUS_VALUE] = item_data_dict.get(COL_PREVIOUS_VALUE)
                    expanded_row_data[COL_INCREASE_VALUE] = item_data_dict.get(COL_INCREASE_VALUE)
                    expanded_row_data[COL_DECREASE_VALUE] = item_data_dict.get(COL_DECREASE_VALUE)
                    expanded_row_data[COL_CURRENT_VALUE] = item_data_dict.get(COL_CURRENT_VALUE)
                    all_new_rows.append(expanded_row_data)
            else:
                # 명세열이 단순 이름 형태 (이미 처리됨) -> 원본 금액 유지
                # print(f"이미 처리된 명세 (유지): {detail_text_to_parse}") # 디버깅용
                row_dict = row_dict_original.copy()
                row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
                row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
                row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
                row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))
                all_new_rows.append(row_dict)
        else:
            # "예금" 또는 "채무"가 아닌 다른 모든 자산구분
            row_dict = row_dict_original.copy()
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
            if col not in final_cols: final_cols.append(col)
        expanded_df = expanded_df[final_cols]

    expanded_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8-sig')
    print(f"처리된 데이터가 '{OUTPUT_CSV_FILE}' 파일로 저장되었습니다.")

# ... (except 블록들은 이전과 동일) ...
except FileNotFoundError:
    print(f"오류: '{INPUT_CSV_FILE}' 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해주세요.")
except KeyError as e:
    print(f"***** KeyError 발생 *****")
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
    print(f"***** 처리 중 일반 오류가 발생했습니다 ******")
    print(f"오류 유형: {type(e).__name__}")
    print(f"오류 메시지: {e}")
    if current_df_index != -1:
        print(f"오류 발생 추정 위치: 원본 CSV 파일의 {current_df_index + 2}번째 행 (헤더 포함).")
        print(f"오류 발생 시 DataFrame 인덱스: {current_df_index}")
        if current_row_content_for_log is not None:
             print(f"오류 발생 시 행의 '{DETAIL_COLUMN_NAME_ORIGINAL}' 내용: {current_row_content_for_log}")
    import traceback
    traceback.print_exc()