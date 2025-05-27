from django.core.management.base import BaseCommand
from ow.models import Legislator, Asset 
from django.db.models import Max, Sum

class Command(BaseCommand):
    help = '의원별 최신 연월 자산 합계를 계산하여 Legislator 모델에 저장합니다.'

    def handle(self, *args, **options):
        count = 0
        for legislator in Legislator.objects.all():
            # 해당 의원의 자산 중 최신 연월 구하기
            latest = (
                Asset.objects
                .filter(legislator=legislator)
                .aggregate(
                    max_year=Max('report_year'),
                    max_month=Max('report_month')
                )
            )
            max_year = latest['max_year']
            max_month = latest['max_month']

            if max_year and max_month:
                total = (
                    Asset.objects
                    .filter(legislator=legislator, report_year=max_year, report_month=max_month)
                    .aggregate(sum=Sum('current_valuation'))['sum'] or 0
                )
                legislator.total_assets = total
                legislator.save()
                count += 1
        self.stdout.write(f"{count}명의 의원 데이터가 갱신되었습니다.")
