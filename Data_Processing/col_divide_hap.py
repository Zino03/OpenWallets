import pandas as pd
import re

# 정치자금법에 따른 ~~ 데이터(강화), 합명·합자·유한회사 출자지분 데이터 금액 분리 및 추출

# --- 설정 ---
INPUT_CSV_FILE = 'converted_asset_data3_20250606_161738.csv'
OUTPUT_CSV_FILE = 'converted_asset_data5_20250606_161738.csv' # 출력 파일 이름 변경

ASSET_TYPE_COLUMN_NAME = '자산구분'
DETAIL_COLUMN_NAME_ORIGINAL = '소재지 면적 등 권리의 명세'

COL_PREVIOUS_VALUE = '종전가액'
COL_INCREASE_VALUE = '증가액'
COL_DECREASE_VALUE = '감소액'
COL_CURRENT_VALUE = '현재가액'

# 자산구분 값 정의
ASSET_TYPE_POLITICAL_FUND = '정치자금법에 따른 정치자금의 수입 및 지출을 위한 예금계좌의 예금'
ASSET_TYPE_PARTNERSHIP_SHARE = '합명·합자·유한회사 출자지분'

def clean_value(value_str):
    if pd.isna(value_str) or str(value_str).strip() == "": return 0
    try: return int(str(value_str).replace(',', '').strip())
    except ValueError: return 0

def extract_name_for_political_fund(detail_string_original):
    if pd.isna(detail_string_original) or str(detail_string_original).strip() == "": return None
    detail_string = str(detail_string_original).strip()
    match = re.match(r"(.+?)(?=\s*[\d(])|(.*)", detail_string)
    if match:
        name = match.group(1) if match.group(1) else match.group(2)
        return name.strip(' ,') if name else None
    return detail_string.strip(' ,')

def extract_name_before_first_comma(detail_string_original):
    """명세 문자열에서 첫 번째 쉼표 이전의 내용(이름)만 추출합니다."""
    if pd.isna(detail_string_original) or str(detail_string_original).strip() == "":
        return None
    detail_string = str(detail_string_original) # 이미 문자열이라고 가정하지만, 안전하게 str()
    
    # 첫 번째 쉼표를 찾음
    comma_index = detail_string.find(',')
    
    if comma_index != -1: # 쉼표가 있다면
        name_part = detail_string[:comma_index]
        return name_part.strip() # 쉼표 앞부분의 양쪽 공백 제거
    else: # 쉼표가 없다면 전체 문자열을 이름으로 간주하고 반환 (양쪽 공백 제거)
        return detail_string.strip()

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
        
        row_dict = row.to_dict() # 먼저 현재 행을 복사

        if asset_type == ASSET_TYPE_POLITICAL_FUND: # "정치자금예금" 처리
            original_detail_text = row_dict[DETAIL_COLUMN_NAME_ORIGINAL]
            extracted_name = extract_name_for_political_fund(original_detail_text)
            row_dict[DETAIL_COLUMN_NAME_ORIGINAL] = extracted_name
            # 금액은 원본 값 유지 (숫자형 정리)
            row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
            row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
            row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
            row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))

        elif asset_type == ASSET_TYPE_PARTNERSHIP_SHARE: # "출자지분" 처리
            original_detail_text = row_dict[DETAIL_COLUMN_NAME_ORIGINAL]
            extracted_name = extract_name_before_first_comma(original_detail_text)
            row_dict[DETAIL_COLUMN_NAME_ORIGINAL] = extracted_name
            # 금액은 원본 값 유지 (숫자형 정리)
            row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
            row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
            row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
            row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))
            
        else: # "예금" 포함 그 외 모든 자산구분
            # 금액 관련 열들만 숫자형으로 정리, 명세는 그대로
            row_dict[COL_PREVIOUS_VALUE] = clean_value(row.get(COL_PREVIOUS_VALUE))
            row_dict[COL_INCREASE_VALUE] = clean_value(row.get(COL_INCREASE_VALUE))
            row_dict[COL_DECREASE_VALUE] = clean_value(row.get(COL_DECREASE_VALUE))
            row_dict[COL_CURRENT_VALUE] = clean_value(row.get(COL_CURRENT_VALUE))
        
        # 모든 경우에 대해, 수정된 row_dict를 all_new_rows에 추가
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
    print(f"***** 처리 중 일반 오류가 발생했습니다 *****")
    print(f"오류 유형: {type(e).__name__}")
    print(f"오류 메시지: {e}")
    if current_df_index != -1:
        print(f"오류 발생 추정 위치: 원본 CSV 파일의 {current_df_index + 2}번째 행 (헤더 포함).")
        print(f"오류 발생 시 DataFrame 인덱스: {current_df_index}")
        if current_row_content_for_log is not None:
             print(f"오류 발생 시 행의 '{DETAIL_COLUMN_NAME_ORIGINAL}' 내용: {current_row_content_for_log}")
    import traceback
    traceback.print_exc()