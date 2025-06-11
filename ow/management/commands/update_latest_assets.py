from django.core.management.base import BaseCommand
from ow.models import Legislator, Asset 
from django.db.models import Max, Sum

class Command(BaseCommand):
    help = '의원별 최신 연월 자산 합계를 계산하여 Legislator 모델에 저장.'

    def handle(self, *args, **options):
        count = 0
        for legislator in Legislator.objects.all():
            # 최신 연월 조합을 구함
            latest_asset = (
                Asset.objects
                .filter(legislator=legislator)
                .order_by('-report_year', '-report_month')
                .values('report_year', 'report_month')
                .first()
            )
            if latest_asset:
                max_year = latest_asset['report_year']
                max_month = latest_asset['report_month']
                # 최신 연월의 자산 합계를 DB에 저장
                total = (
                    Asset.objects
                    .filter(legislator=legislator, report_year=max_year, report_month=max_month)
                    .exclude(asset_type='채무')
                    .exclude(asset_type='비영리법인에 출연한 재산')
                    .aggregate(sum=Sum('current_valuation'))['sum'] or 0
                )
                legislator.total_assets = total
                legislator.save()