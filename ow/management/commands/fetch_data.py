# api 데이터 가져오기
from django.core.management.base import BaseCommand
from ow.services import save_legislators, save_assets, delete_status, DEFAULT_STATUS_FILE

class Command(BaseCommand):
    help = 'OpenWatch API 데이터 가져오기 및 저장'

    def add_arguments(self, parser):
        parser.add_argument(
            '--legislators-only',
            action='store_true',
            help='Legislator 정보만 저장.',
        )
        parser.add_argument(
            '--assets-only',
            action='store_true',
            help='Asset 정보만 저장.',
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=0, # 0이면 제한 없음
            help='Asset 데이터를 가져올 MAX page 수',
        )
        # 상태 초기화 옵션 추가
        parser.add_argument(
            '--reset-status',
            action='store_true',
            help='저장된 데이터 무시, 상태 파일 초기화하고 처음부터 데이터 가져오기 시작',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Data import 시작"))

        legislators_only = options['legislators_only']
        assets_only = options['assets_only']
        max_pages = options['max_pages']
        output_file = options['output_file']
        reset_status = options['reset_status'] # 옵션 값 읽기
        status_file = DEFAULT_STATUS_FILE # 기본값 사용

        # --reset-status 옵션 처리
        if reset_status:
            delete_status(status_file) # 상태 파일 삭제

        # --output-file 이 지정되면 자동으로 --assets-only 처럼 동작
        if output_file:
            assets_only = True
            legislators_only = False # 명시적으로 의원 임포트는 끔
            self.stdout.write(self.style.WARNING(f"Output 모드 Asset DB대신 파일에 저장 '{output_file}'"))

        # 어떤 작업을 실행할지 결정
        run_legislators = not assets_only
        run_assets = not legislators_only

        if run_legislators:
             self.stdout.write("Legislator 가져오기 시작")
             # status_file 인자 전달
             saved_l, updated_l, skipped_l = save_legislators(status_file=status_file)
             self.stdout.write(self.style.SUCCESS(f"Legislator 가져오기 끝 Saved: {saved_l}, Updated: {updated_l}"))

        if run_assets:
            self.stdout.write(f"Asset 가져오기 시작 (max pages: {'unlimited' if max_pages == 0 else max_pages})...")
            # max_pages, output_file, status_file 인자 전달
            saved_a, updated_a, skipped_a = save_assets(max_pages=max_pages, output_file_path=output_file, status_file=status_file)
            if output_file:
                 # 파일 출력 모드에서는 saved/updated는 0, skipped만 의미 있음
                 self.stdout.write(self.style.SUCCESS(f"Asset 파일 추축 끝 "))
            else:
                 # DB 저장 모드 결과 출력
                 self.stdout.write(self.style.SUCCESS(f"Asset 가져오기 끝 Saved: {saved_a}, Updated: {updated_a}"))

        self.stdout.write(self.style.SUCCESS("\데이터 가져오기 문제없이 완료"))