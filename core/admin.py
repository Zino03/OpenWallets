# core/admin.py
from django.contrib import admin
from .models import Legislator, Asset # 모델 임포트

@admin.register(Legislator) # Legislator 모델 등록
class LegislatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'electoral_district', 'member_id') # 목록에 보여줄 필드 지정
    search_fields = ('name', 'party', 'member_id') # 검색 기능 추가
    list_filter = ('party', 'gender', 'reelected') # 필터 기능 추가

@admin.register(Asset) # Asset 모델 등록
class AssetAdmin(admin.ModelAdmin):
    list_display = ('legislator', 'report_year', 'report_month', 'asset_type', 'kind', 'current_valuation', 'openwatch_asset_id') # 목록에 보여줄 필드
    search_fields = ('legislator__name', 'asset_type', 'kind', 'detail', 'openwatch_asset_id')
    list_filter = ('asset_type', 'kind', 'relation', 'report_year') # 필터 기능 추가

