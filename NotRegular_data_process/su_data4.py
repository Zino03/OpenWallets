import pandas as pd
import numpy as np
import re
import datetime

def parse_complex_data():
    """
    복잡한 형식의 데이터를 파싱하여 CSV로 변환하는 함수
    """
    try:
        # Excel 파일 읽기 (헤더 없이)
        df = pd.read_excel('data1.xlsx', header=None)
        
        print("원본 데이터 구조 확인:")
        print(f"컬럼 수: {len(df.columns)}")
        
        # 변환된 데이터를 저장할 리스트
        converted_data = []
        
        current_name = None
        current_date = None
        current_category = None  # ▶ 카테고리 정보 저장
        
        for idx, row in df.iterrows():
            # 행을 문자열로 변환하여 확인
            row_values = [str(x) for x in row if pd.notna(x)]
            
            # 성명과 공개일자 추출
            if len(row) > 1 and '성명' in str(row.iloc[0]) and pd.notna(row.iloc[1]):
                current_name = str(row.iloc[1])
                # 공개일자 찾기
                for i in range(2, min(len(row), 6)):
                    if pd.notna(row.iloc[i]):
                        val = str(row.iloc[i])
                        if re.search(r'\d{4}-\d{2}-\d{2}', val) or val.isdigit():
                            if val.isdigit() and len(val) == 5:  # Excel 날짜 형식
                                try:
                                    excel_date = pd.to_datetime('1900-01-01') + pd.Timedelta(days=int(val)-2)
                                    current_date = excel_date.strftime('%Y-%m-%d')
                                except:
                                    current_date = '2024-08-29'
                            else:
                                current_date = val
                            break
                print(f"새로운 의원 발견: {current_name}")
                continue
            
            # 메타정보 건너뛰기 - 더 강화된 조건
            if len(row_values) > 0:
                first_val = row_values[0].lower()
                # 메타정보 키워드들
                meta_keywords = ['소속', '직위', '공개목록', '본인과의관계', '재산의종류', '소재지', 
                               '현재가액', '비고', '본인과의', '관계', '면적', '권리의', '명세', 
                               '가액', '변동액', '천원', '타인부양', '변동사유']
                
                # 첫 번째 값이 메타정보 키워드이거나
                if any(keyword in first_val for keyword in meta_keywords):
                    print(f"DEBUG - 메타정보 건너뛰기: {row_values[0]}")
                    continue
                
                # 전체 행이 메타정보로 구성된 경우
                if any(keyword in ' '.join(row_values).lower() for keyword in 
                      ['본인과의관계', '재산의종류', '소재지면적', '현재가액', '변동액']):
                    print(f"DEBUG - 메타정보 행 건너뛰기: {row_values}")
                    continue
            
            # ▶로 시작하는 카테고리 행 처리 (이것이 asset_type이 됨)
            if len(row_values) > 0 and '▶' in row_values[0]:
                category_text = row_values[0].replace('▶', '').replace('(소계)', '').strip()
                current_category = category_text
                print(f"카테고리 변경: {current_category}")
                continue
            
            # 총계 행 건너뛰기
            if len(row_values) > 0 and ('총계' in row_values[0] or '소계' in row_values[0]):
                print(f"DEBUG - 총계/소계 행 건너뛰기: {row_values[0]}")
                continue
            
            # 단순 키워드만 있는 행 건너뛰기
            if (len(row_values) <= 3 and len(row_values) > 0 and 
                any(keyword in row_values[0].lower() for keyword in 
                   ['모', '관계', '천원', '가액', '변동', '타인부양', '변동사유'])):
                print(f"DEBUG - 키워드 행 건너뛰기: {row_values}")
                continue
            
            # 괄호로만 이루어진 행은 건너뛰기 (이미 위에서 처리됨)
            if (current_name and len(row) >= 2 and pd.notna(row.iloc[1]) and 
                str(row.iloc[1]).strip().startswith('(') and str(row.iloc[1]).strip().endswith(')') and
                (not pd.notna(row.iloc[0]) or str(row.iloc[0]).strip() == '')):
                print(f"DEBUG - 괄호 행 건너뛰기: {str(row.iloc[1]).strip()}")
                continue
            
            # 실제 데이터 행 처리
            if (current_name and len(row) >= 4 and pd.notna(row.iloc[0]) and 
                current_category and  # 카테고리가 설정되어 있어야 함
                str(row.iloc[0]).strip() not in ['모', '관계', '본인과의', '천원', '가액', '변동액', '타인부양', '변동사유']):
                relation = str(row.iloc[0]).strip()
                
                # 관계가 비어있거나 공백인 경우 처리
                if not relation or relation == 'nan':
                    if converted_data and current_name == converted_data[-1]['name']:
                        relation = converted_data[-1]['relation']
                    else:
                        relation = '본인'
                
                # asset_type은 현재 카테고리를 그대로 사용 (길어도 원본 유지)
                asset_type = current_category if current_category else ''
                kind = ''
                detail = ''
                
                # 고지거부 및 등록제외사항인 경우 우선 처리
                if '고지거부' in asset_type or '등록제외' in asset_type:
                    kind = '고지거부'
                    print(f"DEBUG - 고지거부 카테고리로 처리됨")
                else:
                    # 컬럼 1에서 kind 추출 (재산의 종류 칼럼)
                    if pd.notna(row.iloc[1]):
                        raw_kind = str(row.iloc[1]).strip()
                        
                        # 다음 행에 추가 정보가 있는지 확인 (괄호로 시작하는 경우)
                        if idx + 1 < len(df):
                            next_row = df.iloc[idx + 1]
                            if pd.notna(next_row.iloc[1]):
                                next_kind = str(next_row.iloc[1]).strip()
                                # 괄호로 시작하는 경우 연결
                                if next_kind.startswith('(') and next_kind.endswith(')'):
                                    raw_kind = raw_kind + next_kind
                                    print(f"DEBUG - 다음 행과 결합: '{raw_kind}'")
                        
                        print(f"DEBUG - raw_kind: '{raw_kind}', asset_type: '{asset_type}'")
                        if raw_kind != 'nan' and raw_kind != '':
                            # 원본 데이터를 그대로 사용 (괄호 포함)
                            kind = raw_kind
                            print(f"DEBUG - 원본 kind 사용: '{kind}'")
                    else:
                        # kind가 없는 경우 빈 문자열
                        kind = ''
                        print(f"DEBUG - kind 없음")
                
                # detail이 없으면 컬럼 2 또는 3에서 추출
                for i in range(2, min(len(row), 5)):
                    if pd.notna(row.iloc[i]):
                        val = str(row.iloc[i]).strip()
                        if val != 'nan' and val != '' and not val.replace(',', '').replace('.', '').isdigit():
                            detail = val
                            break
                
                # 현재 가액 추출 - 두 가지 형식 처리
                current_val = 0
                origin_val = 0
                increased_amount = 0
                decreased_amount = 0
                val_column_idx = None
                reason_for_change = ''
                
                # 먼저 숫자가 있는 컬럼들을 찾아서 형식 판단
                numeric_columns = []
                for i in range(3, min(len(row), len(df.columns))):
                    if pd.notna(row.iloc[i]):
                        val_str = str(row.iloc[i]).strip()
                        # 괄호 안의 숫자나 일반 숫자 모두 처리
                        clean_val = val_str.replace('(', '').replace(')', '').replace(',', '')
                        if clean_val.replace('.', '').isdigit() or (clean_val.startswith('-') and clean_val[1:].replace('.', '').isdigit()):
                            try:
                                # 괄호가 있으면 음수로 처리
                                if '(' in val_str and ')' in val_str:
                                    numeric_val = -int(clean_val.replace('.', '').split('.')[0])
                                else:
                                    numeric_val = int(clean_val.replace('.', '').split('.')[0])
                                numeric_columns.append((i, numeric_val, val_str))
                            except:
                                continue
                
                print(f"DEBUG - 숫자 컬럼들: {numeric_columns}")
                
                # 형식 판단 및 처리
                if len(numeric_columns) >= 4:
                    # 형식 1: 분리형 (종전가액, 증가액, 감소액, 현재가액)
                    origin_val = numeric_columns[0][1]
                    increased_amount = numeric_columns[1][1] 
                    decreased_amount = abs(numeric_columns[2][1])  # 감소액은 양수로 저장
                    current_val = numeric_columns[3][1]
                    val_column_idx = numeric_columns[3][0]  # 마지막 가액 컬럼
                    print(f"DEBUG - 분리형 처리: 종전={origin_val}, 증가={increased_amount}, 감소={decreased_amount}, 현재={current_val}")
                    
                elif len(numeric_columns) >= 1:
                    # 형식 2: 단일형 (현재가액만)
                    current_val = numeric_columns[0][1]
                    val_column_idx = numeric_columns[0][0]
                    print(f"DEBUG - 단일형 처리: 현재={current_val}")
                
                # 비고(reason_for_change) 추출 - 가액 뒤 컬럼들에서 찾기
                if val_column_idx is not None:
                    # 가액 다음 컬럼부터 끝까지 확인
                    for i in range(val_column_idx + 1, min(len(row), len(df.columns))):
                        if pd.notna(row.iloc[i]):
                            reason_text = str(row.iloc[i]).strip()
                            if reason_text != 'nan' and reason_text != '':
                                # 숫자가 아닌 텍스트인 경우 비고로 간주
                                clean_reason = reason_text.replace(',', '').replace('.', '').replace('(', '').replace(')', '')
                                if not clean_reason.isdigit():
                                    reason_for_change = reason_text
                                    print(f"DEBUG - 비고 발견: '{reason_for_change}' (컬럼 {i})")
                                    break
                else:
                    # 가액이 없는 경우 뒤쪽 컬럼들에서 비고 찾기
                    for i in range(4, min(len(row), len(df.columns))):
                        if pd.notna(row.iloc[i]):
                            reason_text = str(row.iloc[i]).strip()
                            if reason_text != 'nan' and reason_text != '':
                                # 숫자가 아닌 텍스트인 경우 비고로 간주
                                if not reason_text.replace(',', '').replace('.', '').isdigit():
                                    reason_for_change = reason_text
                                    print(f"DEBUG - 비고 발견 (가액없음): '{reason_for_change}' (컬럼 {i})")
                                    break
                # 연도, 월 추출
                year, month = 2024, 8
                if current_date:
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', current_date)
                    if date_match:
                        year, month = int(date_match.group(1)), int(date_match.group(2))
                
                # 의미있는 데이터만 추가
                if asset_type and asset_type not in ['국회', 'nan', '', '소속']:
                    converted_row = {
                        'name': current_name,
                        'report_year': year,
                        'report_month': month,
                        'asset_type': asset_type,
                        'relation': relation,
                        'kind': kind,
                        'detail': detail,
                        'origin_valuation': origin_val,  # 종전가액
                        'increased_amount': increased_amount,  # 증가액
                        'decreased_amount': decreased_amount,  # 감소액
                        'current_valuation': current_val,  # 현재가액
                        'reason_for_change': reason_for_change
                    }
                    
                    converted_data.append(converted_row)
        
        # DataFrame으로 변환
        df_converted = pd.DataFrame(converted_data)
        
        # 타임스탬프가 포함된 고유한 파일명 생성
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'converted_asset_data_{timestamp}.csv'
        
        # CSV 파일로 저장
        df_converted.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n변환 완료! {output_filename} 파일이 생성되었습니다.")
        print(f"총 {len(df_converted)}개의 행이 변환되었습니다.")
        
        # 변환된 데이터 샘플 출력
        print("\n변환된 데이터 샘플:")
        print(df_converted.head(10))
        
        # 자산 종류별 통계
        if len(df_converted) > 0:
            print("\n자산 종류별 데이터 개수:")
            print(df_converted['asset_type'].value_counts().head(15))
            
            print("\nkind 필드 값들:")
            kind_counts = df_converted[df_converted['kind'] != '']['kind'].value_counts()
            if len(kind_counts) > 0:
                print(kind_counts.head(15))
            else:
                print("kind 필드에 데이터가 없습니다.")
        
        return df_converted
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("국회의원 재산 신고 데이터 변환 프로그램")
    print("=" * 50)
    
    print("\n" + "=" * 50)
    
    print("데이터 파싱 및 변환...")
    result = parse_complex_data()
    
    if result is not None:
        print("\n변환이 완료되었습니다!")
    else:
        print("\n변환 중 오류가 발생했습니다.")