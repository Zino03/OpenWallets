import pandas as pd
import re
import datetime

def split_detail_rows(csv_filename):
    """
    CSV 파일의 detail 컬럼에서 콤마로 구분된 항목들을 별도 행으로 분리하는 함수
    """
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_filename, encoding='utf-8-sig')
        
        print(f"원본 파일 읽기 완료: {len(df)}개 행")
        print("detail 컬럼 분리 작업 시작...")
        
        # 분리된 데이터를 저장할 리스트
        separated_data = []
        
        for idx, row in df.iterrows():
            detail = str(row['detail']).strip()
            
            # detail이 비어있거나 nan인 경우 원본 행 그대로 추가
            if not detail or detail == 'nan' or detail == '':
                separated_data.append(row.to_dict())
                continue
            
            # 콤마로 분리 (콤마 뒤에 공백이나 글자가 있는 경우)
            # 정규식으로 콤마 뒤에 공백 또는 문자가 오는 패턴을 찾아 분리
            detail_parts = re.split(r',\s*(?=[가-힣A-Za-z(])', detail)
            
            # 분리된 각 부분에 대해 별도 행 생성
            for i, part in enumerate(detail_parts):
                part = part.strip()
                if part:  # 빈 문자열이 아닌 경우만
                    new_row = row.to_dict().copy()
                    
                    # 패턴 3: 금액(증가/감소 금액) 패턴 - "수협은행 216,375(120,297 증가)" 같은 형식
                    pattern3 = re.search(r'(.*?)\s+([\d,]+)\(([\d,]+)\s*(증가|감소)\)', part)
                    
                    if pattern3:
                        detail_text = pattern3.group(1).strip()
                        current_val = int(pattern3.group(2).replace(',', ''))
                        change_amount = int(pattern3.group(3).replace(',', ''))
                        change_type = pattern3.group(4)
                        
                        new_row['detail'] = detail_text
                        new_row['current_valuation'] = current_val
                        
                        if change_type == '증가':
                            new_row['origin_valuation'] = current_val - change_amount
                            new_row['increased_amount'] = change_amount
                            new_row['decreased_amount'] = 0
                        else:  # 감소
                            new_row['origin_valuation'] = current_val + change_amount
                            new_row['increased_amount'] = 0
                            new_row['decreased_amount'] = change_amount
                    else:
                        # 패턴 1: 이름 금액 패턴 - "주식회사 카카오뱅크 34,000" 같은 형식
                        pattern1 = re.search(r'(.*?)\s+([\d,]+)$', part)
                        
                        if pattern1 and not re.search(r'(감소|증가)$', part):
                            detail_text = pattern1.group(1).strip()
                            amount = int(pattern1.group(2).replace(',', ''))
                            
                            new_row['detail'] = detail_text
                            new_row['current_valuation'] = amount
                            new_row['origin_valuation'] = amount
                            new_row['increased_amount'] = 0
                            new_row['decreased_amount'] = 0
                        else:
                            # 패턴 2: 이름만 있는 경우 (또는 '감소'/'증가' 키워드가 포함된 설명)
                            new_row['detail'] = part
                    
                    # 필수 필드가 없는 경우 기본값 설정
                    if 'origin_valuation' not in new_row:
                        new_row['origin_valuation'] = new_row.get('current_valuation', 0)
                    if 'increased_amount' not in new_row:
                        new_row['increased_amount'] = 0
                    if 'decreased_amount' not in new_row:
                        new_row['decreased_amount'] = 0
                    
                    separated_data.append(new_row)
                    
                    print(f"분리됨: {row['name']} - {new_row['detail'][:50]}...")
        
        # 새로운 DataFrame 생성
        df_separated = pd.DataFrame(separated_data)
        
        # 타임스탬프가 포함된 파일명 생성
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'debt_separated_{timestamp}.csv'
        
        # CSV 파일로 저장
        df_separated.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"\ndetail 분리 완료!")
        print(f"원본: {len(df)}개 행 → 분리 후: {len(df_separated)}개 행")
        print(f"결과 파일: {output_filename}")
        
        # 분리 결과 샘플 출력
        print("\n분리된 데이터 샘플:")
        sample_cols = ['name', 'relation', 'kind', 'detail', 'current_valuation', 
                      'origin_valuation', 'increased_amount', 'decreased_amount']
        sample_df = df_separated[sample_cols].head(15)
        for idx, row in sample_df.iterrows():
            print(f"{row['name']} - {row['detail'][:40]} - 현재:{row['current_valuation']} - 원래:{row['origin_valuation']} - 증가:{row['increased_amount']} - 감소:{row['decreased_amount']}")
        
        return df_separated
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return None
def find_latest_debt_file():
    """
    가장 최근에 생성된 debt_only_ 파일을 찾는 함수
    """
    import glob
    import os
    
    debt_files = glob.glob('debt_only_*.csv')
    if not debt_files:
        print("debt_only_로 시작하는 CSV 파일을 찾을 수 없습니다.")
        return None
    
    # 파일 생성 시간으로 정렬하여 가장 최근 파일 반환
    latest_file = max(debt_files, key=os.path.getctime)
    print(f"처리할 파일: {latest_file}")
    return latest_file

if __name__ == "__main__":
    print("채무 데이터 detail 분리 프로그램")
    print("=" * 50)
    
    # 가장 최근 debt_only 파일 찾기
    input_file = find_latest_debt_file()
    
    if input_file:
        # detail 분리 작업 수행
        result = split_detail_rows(input_file)
        
        if result is not None:
            print("\ndetail 분리 작업이 완료되었습니다!")
        else:
            print("\n분리 작업 중 오류가 발생했습니다.")
    else:
        print("\n처리할 파일을 찾을 수 없습니다.")
        print("먼저 su_data5.py를 실행하여 debt_only_ 파일을 생성해주세요.")