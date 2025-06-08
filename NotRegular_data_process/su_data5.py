import pandas as pd
import numpy as np
import re
import datetime

def extract_debt_only():
    """
    채무 데이터만 추출하는 함수
    """
    try:
        # Excel 파일 읽기 (헤더 없이)
        df = pd.read_excel('data1.xlsx', header=None)
        
        print("채무 데이터만 추출 시작...")
        
        # 변환된 데이터를 저장할 리스트
        debt_data = []
        
        current_name = None
        current_date = None
        in_debt_section = False  # 채무 섹션에 있는지 확인
        
        for idx, row in df.iterrows():
            # 행을 문자열로 변환하여 확인
            row_values = [str(x) for x in row if pd.notna(x)]
            
            # 성명과 공개일자 추출
            if len(row) > 1 and '성명' in str(row.iloc[0]) and pd.notna(row.iloc[1]):
                current_name = str(row.iloc[1])
                in_debt_section = False  # 새 사람이면 채무 섹션 초기화
                
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
            
            # ▶로 시작하는 카테고리 행 처리
            if len(row_values) > 0 and '▶' in row_values[0]:
                category_text = row_values[0].replace('▶', '').replace('(소계)', '').strip()
                
                # 채무 관련 섹션인지 확인
                if '채무' in category_text:
                    in_debt_section = True
                    print(f"채무 섹션 시작: {category_text}")
                else:
                    in_debt_section = False
                    print(f"다른 섹션: {category_text} (건너뜀)")
                continue
            
            # 메타정보 건너뛰기
            if (len(row_values) > 0 and any(keyword in row_values[0] for keyword in 
                ['소속', '직위', '공개목록', '본인과의관계', '재산의종류', '소재지', '현재가액', '비고'])):
                continue
            
            # 총계 행 건너뛰기
            if len(row_values) > 0 and '총계' in row_values[0]:
                continue
            
            # 채무 섹션에서만 데이터 처리
            if in_debt_section and current_name and len(row) >= 4 and pd.notna(row.iloc[0]):
                relation = str(row.iloc[0]).strip()
                
                # 관계가 비어있거나 공백인 경우 처리
                if not relation or relation == 'nan':
                    if debt_data and current_name == debt_data[-1]['name']:
                        relation = debt_data[-1]['relation']
                    else:
                        relation = '본인'
                
                # 채무 종류 추출
                debt_type = ''
                if pd.notna(row.iloc[1]):
                    debt_type = str(row.iloc[1]).strip()
                    if debt_type == 'nan':
                        debt_type = ''
                
                # 세부사항 추출
                detail = ''
                for i in range(2, min(len(row), 5)):
                    if pd.notna(row.iloc[i]):
                        val = str(row.iloc[i]).strip()
                        if val != 'nan' and val != '' and not val.replace(',', '').replace('.', '').isdigit():
                            detail = val
                            break
                
                # 현재 가액 추출
                current_val = 0
                for i in range(3, min(len(row), 8)):
                    if pd.notna(row.iloc[i]):
                        val_str = str(row.iloc[i])
                        # 숫자만 추출
                        if val_str.replace(',', '').replace('.', '').isdigit():
                            try:
                                current_val = int(val_str.replace(',', '').split('.')[0])
                                break
                            except:
                                continue
                
                # 연도, 월 추출
                year, month = 2024, 8
                if current_date:
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', current_date)
                    if date_match:
                        year, month = int(date_match.group(1)), int(date_match.group(2))
                
                # 채무 데이터만 추가
                debt_row = {
                    'name': current_name,
                    'report_year': year,
                    'report_month': month,
                    'asset_type': '채무',
                    'relation': relation,
                    'kind': debt_type,
                    'detail': detail,
                    'origin_valuation': 0,
                    'increased_amount': 0,
                    'decreased_amount': 0,
                    'current_valuation': current_val,
                    'reason_for_change': ''
                }
                
                debt_data.append(debt_row)
                print(f"채무 데이터 추가: {current_name} - {relation} - {debt_type} - {current_val}")
        
        # DataFrame으로 변환
        if debt_data:
            df_debt = pd.DataFrame(debt_data)
            
            # 타임스탬프가 포함된 고유한 파일명 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f'debt_only_{timestamp}.csv'
            
            # CSV 파일로 저장
            df_debt.to_csv(output_filename, index=False, encoding='utf-8-sig')
            
            print(f"\n채무 데이터 추출 완료! {output_filename} 파일이 생성되었습니다.")
            print(f"총 {len(df_debt)}개의 채무 데이터가 추출되었습니다.")
            
            # 변환된 데이터 샘플 출력
            print("\n추출된 채무 데이터 샘플:")
            print(df_debt[['name', 'relation', 'kind', 'detail', 'current_valuation']].head(10))
            
            return df_debt
        else:
            print("추출된 채무 데이터가 없습니다.")
            return None
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("채무 데이터 전용 추출 프로그램")
    print("=" * 50)
    
    # 채무 데이터만 추출
    result = extract_debt_only()
    
    if result is not None:
        print("\n채무 데이터 추출이 완료되었습니다!")
    else:
        print("\n추출 중 오류가 발생했습니다.")