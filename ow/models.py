from django.db import models

class Legislator(models.Model):
    """국회의원 정보를 저장하는 모델 (/members API 기반)"""
    # API 응답의 'id' 필드를 기본 키로 사용
    member_id = models.CharField(
        max_length=20,
        unique=True,
        primary_key=True, # 이 필드를 기본 키로 사용
        help_text="OpenWatch API member ID (고유 식별자)"
    )
    name = models.CharField(max_length=50, db_index=True, help_text="이름 (API 'name')")
    chi_name = models.CharField(max_length=100, db_index=True) # 한자 이름
    birth_cd = models.CharField(max_length=10, blank=True, null=True) # 양력, 음력
    birth = models.DateField(blank=True, null=True) # 생년월일
    position = models.CharField(max_length=100, blank=True, null=True) # 직책
    party = models.CharField(max_length=100, blank=True, null=True) # 정당
    electoral_district = models.CharField(max_length=100, blank=True, null=True) # 선거구
    committee = models.CharField(max_length=100, blank=True, null=True) # 위원회
    latest_age = models.CharField(null=True, blank=True, help_text="활동 회기 (API 'latestAge')") # 예시: 21 또는 22
    gender = models.CharField(max_length=10, blank=True, null=True, help_text="성별 (API 'gender')") # 성별
    reelected = models.CharField(max_length=50, blank=True, null=True, help_text="재선여부 (API 'reelected')") # 재선 여부
    tel = models.CharField(max_length=20, blank=True, null=True) # 전화번호
    email = models.CharField(max_length=100, blank=True, null=True) # 이메일
    history =  models.JSONField(default = list, blank=True, null=True) # 약력
    office =  models.JSONField(default = list, blank=True, null=True) # 사무실 호실
    total_assets = models.BigIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.party or '정보 없음'})"

class Asset(models.Model):
    """국회의원 자산 상세 항목 정보를 저장하는 모델 (/assets API 기반)"""
    # 연결 정보
    legislator = models.ForeignKey(
        Legislator,
        on_delete=models.CASCADE, # 의원 정보 삭제 시 관련 자산 정보도 삭제
        related_name='assets',    # legislator.assets.all() 형태로 접근 가능
        help_text="해당 자산이 속한 국회의원 (nationalAssemblyMemberId를 통해 연결)"
    )

    # OpenWatch API 데이터 기반 필드
    # API 응답의 'id' 필드 (자산 항목 자체의 고유 ID)
    member_id = models.CharField(
        max_length=20,
        help_text="OpenWatch API member ID (고유 식별자)"
    )
    name = models.CharField(max_length=50, db_index=True, help_text="이름 (API 'name')")
    # API 응답의 'date' 필드 - 연도만 저장하거나 날짜로 저장
    report_year = models.IntegerField(db_index=True, help_text="재산 신고 기준 연도")
    report_month = models.IntegerField(null = True, help_text="재산 신고 기준 월")
    asset_type = models.CharField(max_length=100, db_index=True, help_text="재산 종류 (API 'type')")
    kind = models.CharField(max_length=100, blank=True, null=True, help_text="상세 종류 (API 'kind')")
    relation = models.CharField(max_length=50, help_text="소유자와의 관계 (API 'relation')")
    detail = models.TextField(help_text="재산 상세 내역 (API 'detail')")
    current_valuation = models.BigIntegerField(null=True, blank=True, help_text="현재 가액 (API 'currentValuation')")
    reason_for_change = models.TextField(blank=True, null=True, help_text="변동 사유 (API 'reason')")
    
    origin_valuation = models.BigIntegerField(null=True, blank=True, help_text="종전가액 (API 'originValuation')")
    increased_amount = models.BigIntegerField(null=True, blank=True, help_text="증가액 (API 'increasedAmount')")
    decreased_amount = models.BigIntegerField(null=True, blank=True, help_text="감소액 (API 'decreasedAmount')")

    # 부가 정보
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-report_year', '-report_month', 'legislator__name', 'asset_type'] # 최신순, 의원 이름 순 정렬

    def __str__(self):
        formatted_value = "{:,}".format(self.current_valuation) if self.current_valuation is not None else "N/A"
        return f"{self.legislator.name} ({self.report_year}.{self.report_month:02d}) - {self.asset_type} ({self.relation}): {formatted_value} 원"

    # 'date' 문자열에서 연, 월 분리
    @staticmethod
    def parse_date_string(date_str):    # 'YYYYMM' 형식의 문자열에서 연도와 월을 분리하여 반환
        if date_str and len(date_str) == 6:
            try:
                year = int(date_str[:4])
                month = int(date_str[4:])
                return year, month
            except ValueError:
                return None, None
        return None, None