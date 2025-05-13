# core/models.py
from django.db import models
import datetime # 날짜 처리를 위해 추가

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
    party = models.CharField(max_length=100, blank=True, null=True, help_text="정당명 (API 'partyName')")
    gender = models.CharField(max_length=10, blank=True, null=True, help_text="성별 (API 'gender')")
    reelected = models.CharField(max_length=50, blank=True, null=True, help_text="재선여부 (API 'reelected')")
    electoral_district = models.CharField(max_length=100, blank=True, null=True, help_text="선거구 (API 'electoralDistrict')")
    latest_age = models.IntegerField(null=True, blank=True, help_text="활동 회기 (API 'latestAge')") # 예시: 21 또는 22

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
    openwatch_asset_id = models.BigIntegerField(unique=True, null = True, blank = True, help_text="OpenWatch API 상의 자산 고유 ID")
    # API 응답의 'date' 필드 - 연도만 저장하거나 날짜로 저장
    report_year = models.IntegerField(db_index=True, help_text="재산 신고 기준 연도")
    report_month = models.IntegerField(null = True, help_text="재산 신고 기준 월") # 월 정보도 저장

    asset_type = models.CharField(max_length=100, db_index=True, help_text="재산 종류 (API 'type')")
    kind = models.CharField(max_length=100, blank=True, null=True, help_text="상세 종류 (API 'kind')")
    relation = models.CharField(max_length=50, help_text="소유자와의 관계 (API 'relation')")
    detail = models.TextField(help_text="재산 상세 내역 (API 'detail')")
    current_valuation = models.BigIntegerField(null=True, blank=True, help_text="현재 가액 (API 'currentValuation')")
    reason_for_change = models.TextField(blank=True, null=True, help_text="변동 사유 (API 'reason')")

    origin_valuation = models.BigIntegerField(null=True, blank=True, help_text="최초 가액 (API 'originValuation')")
    increased_amount = models.BigIntegerField(null=True, blank=True, help_text="증가액 (API 'increasedAmount')")
    decreased_amount = models.BigIntegerField(null=True, blank=True, help_text="감소액 (API 'decreasedAmount')")
    # increased_amount_real = models.BigIntegerField(null=True, blank=True, help_text="실거래 증가액 (API 'increasedAmountForRealTransaction')")
    # decreased_amount_real = models.BigIntegerField(null=True, blank=True, help_text="실거래 감소액 (API 'decreasedAmountForRealTransaction')")
    # current_valuation_real = models.BigIntegerField(null=True, blank=True, help_text="실거래 현재가액 (API 'currentValuationForRealTransation')")

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