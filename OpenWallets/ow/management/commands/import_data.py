import csv
from django.core.management.base import BaseCommand
from ow.models import Legislator, Asset


class Command(BaseCommand):
    help = 'CSV 파일로부터 Legislator와 Asset 데이터를 로드합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--members', type=str, help='members.csv 경로')
        parser.add_argument('--assets', type=str, help='assets.csv 경로')

    def handle(self, *args, **options):
        if options['members']:
            self.load_members(options['members'])
        if options['assets']:
            self.load_assets(options['assets'])

    def load_members(self, filepath):
        self.stdout.write(f"▶ members.csv 로드 중: {filepath}")
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                legislator, created = Legislator.objects.update_or_create(
                    member_id=row['member_id'],
                    defaults={
                        'name': row['name'],
                        'chi_name': row['chi_name'],
                        'birth_cd': row.get('birth_cd', ''),
                        'birth': row.get('birth', ''),
                        'position': row.get('position', ''),
                        'party': row.get('party', ''),
                        'electoral_district': row.get('electoral_district', ''),
                        'committee': row.get('committee', ''),
                        'gender': row.get('gender', ''),
                        'reelected': row.get('reelected', ''),
                        'electoral_district': row.get('electoral_district', ''),
                        'latest_age': row.get('latest_age') or None,
                        'tel': row.get('tel', ''),
                        'email': row.get('email', ''),
                        'history': row.get('history', ''),
                        'office': row.get('office', ''),   
                    }
                )
                self.stdout.write(f" - {'생성' if created else '업데이트'}됨: {legislator.name}")

    def load_assets(self, filepath):
        self.stdout.write(f"▶ assets.csv 로드 중: {filepath}")
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    legislator = Legislator.objects.get(member_id=row['member_id'])
                except Legislator.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f" ⚠ 의원 {row['member_id']} 없음"))
                    continue

                asset, created = Asset.objects.update_or_create(
                    legislator=legislator,
                    member_id=row['member_id'],
                    name=row['name'],
                    report_year=int(row['report_year']),
                    report_month=int(row['report_month']),
                    asset_type=row['asset_type'],
                    relation=row['relation'],
                    detail=row['detail'],
                    kind=row.get('kind'),
                    current_valuation=int(row['current_valuation'] or 0),
                    reason_for_change=row.get('reason_for_change', ''),
                    origin_valuation=int(row['origin_valuation'] or 0),
                    increased_amount=int(row['increased_amount'] or 0),
                    decreased_amount=int(row['decreased_amount'] or 0),
            )
                self.stdout.write(f" - 자산 추가됨: {asset}")
