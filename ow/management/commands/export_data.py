# core/management/commands/export_data.py
import pandas as pd
from django.core.management.base import BaseCommand
from ow.models import Legislator, Asset
import datetime

class Command(BaseCommand):
    help = 'Legislator, Asset Excel 파일로 추출출'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Excel로 추출 시작작'))

        try:
            # 1. 데이터베이스에서 데이터 조회
            self.stdout.write('DB에서 Legislator 정보 가져오기 시작')
            legislators_qs = Legislator.objects.all().values(
                'member_id', 'name', 'party', 'gender', 'reelected', 'electoral_district', 'latest_age'
                # 필요한 다른 필드 이름 추가
            )
            legislators_df = pd.DataFrame(list(legislators_qs))
            self.stdout.write(f'Fetched {len(legislators_df)} legislator 레코드')

            self.stdout.write('DB에서 Asset 정보 가져오기 시작')
            assets_qs = Asset.objects.select_related('legislator').all().values(
                'openwatch_asset_id',
                'legislator__name',
                'legislator__member_id',
                'report_year',
                'report_month',
                'asset_type',
                'kind',
                'relation',
                'detail',
                'current_valuation',
                'reason_for_change',
                'origin_valuation',
                'increased_amount',
                'decreased_amount'
                # 필요한 다른 필드 이름 추가
            )
            assets_df = pd.DataFrame(list(assets_qs))
            # 필요시 컬럼 이름 변경
            assets_df.rename(columns={
                'legislator__name': '의원명',
                'legislator__member_id': '의원ID',
                'openwatch_asset_id': '자산ID(OpenWatch)',
                'report_year': '신고연도',
                'report_month': '신고월',
                'asset_type': '자산구분',
                'kind': '종류',
                'relation': '관계',
                'detail': '상세내역',
                'current_valuation': '현재가액',
                'reason_for_change': '변동사유',
                'origin_valuation': '종전가액',
                'increased_amount': '증가액',
                'decreased_amount': '감소액'
            }, inplace=True)
            self.stdout.write(f'Fetched {len(assets_df)} asset 레코드드') # DB에 있는 Asset 수 출력

            # 2. 파일로 저장
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f'db_export_data_{timestamp}.xlsx' # 파일 이름 변경 (선택)
            csv_legislators_filename = f'db_export_legislators_{timestamp}.csv' # 파일 이름 변경 (선택)
            csv_assets_filename = f'db_export_assets_{timestamp}.csv' # 파일 이름 변경 (선택)

            self.stdout.write(f'파일로 저장')

            # Excel 저장
            self.stdout.write(f'Excel로 저장 : {excel_filename}')
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                legislators_df.to_excel(writer, sheet_name='의원정보', index=False)
                assets_df.to_excel(writer, sheet_name='자산정보', index=False)

            # CSV 저장
            self.stdout.write(f'CSV로 Legislator 정보 저장: {csv_legislators_filename}')
            legislators_df.to_csv(csv_legislators_filename, index=False, encoding='utf-8-sig')

            self.stdout.write(f'CSV로 Asset 정보 저장: {csv_assets_filename}')
            assets_df.to_csv(csv_assets_filename, index=False, encoding='utf-8-sig')

            self.stdout.write(self.style.SUCCESS(f'\n문제 없이 마무리'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error : {e}'))