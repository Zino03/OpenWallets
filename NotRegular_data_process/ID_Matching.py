import pandas as pd
import os

def match_member_ids(reference_csv_path, target_csv_path):
    """
    참조 CSV의 이름과 의원 ID를 매칭하여 대상 CSV의 member_id 컬럼을 채우고 새 파일로 저장합니다.
    """
    
    try:
        # CSV 파일 읽기
        reference_df = pd.read_csv(reference_csv_path, encoding='utf-8')
        target_df = pd.read_csv(target_csv_path, encoding='utf-8')
        
        # 필요한 컬럼 확인
        if 'name' not in reference_df.columns or 'member_id' not in reference_df.columns:
            raise ValueError("참조 CSV에 'name' 또는 'member_id' 컬럼이 없습니다.")
        
        if 'name' not in target_df.columns:
            raise ValueError("대상 CSV에 'name' 컬럼이 없습니다.")
        
        # member_id 컬럼이 없으면 생성
        if 'member_id' not in target_df.columns:
            target_df['member_id'] = ''
        
        # 참조 데이터에서 이름과 ID 매핑 딕셔너리 생성
        name_to_id = dict(zip(reference_df['name'], reference_df['member_id']))
        
        # 매칭 통계
        matched_count = 0
        unmatched_names = []
        
        # 각 행에 대해 이름 매칭 수행
        for idx, row in target_df.iterrows():
            name = row['name']
            if name in name_to_id:
                target_df.at[idx, 'member_id'] = name_to_id[name]
                matched_count += 1
            else:
                unmatched_names.append(name)
        
        # 새 파일명 생성 (원본 파일명 + "_matched")
        base_name = os.path.splitext(target_csv_path)[0]
        extension = os.path.splitext(target_csv_path)[1]
        output_csv_path = f"{base_name}_matched{extension}"
        
        # 결과 저장
        target_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        
        # 결과 출력
        print(f"\n매칭 완료!")
        print(f"전체 레코드 수: {len(target_df)}")
        print(f"매칭 성공: {matched_count}개")
        print(f"매칭 실패: {len(unmatched_names)}개")
        
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None

def main():
    # 파일 경로 설정
    reference_csv = input("참조 CSV 파일 경로를 입력하세요 (name, member_id 포함): ").strip()
    target_csv = input("대상 CSV 파일 경로를 입력하세요 (name 포함): ").strip()
    
    # 파일 존재 확인
    if not os.path.exists(reference_csv):
        print(f"참조 파일이 존재하지 않습니다: {reference_csv}")
        return
    
    if not os.path.exists(target_csv):
        print(f"대상 파일이 존재하지 않습니다: {target_csv}")
        return
    
    # ID 매칭 실행
    result = match_member_ids(reference_csv, target_csv)
    
    if result is not None:
        print("\n처리가 완료되었습니다!")
