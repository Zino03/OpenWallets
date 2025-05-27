from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ow.models import Legislator, Asset
from django.db.models import OuterRef, Subquery, Sum, F, Max
from collections import defaultdict
from django.db.models.functions import Left

def main_page(request):
    # 상위 20명 정렬
    top_members = Legislator.objects.order_by('-total_assets')[:20]

    # 순위 붙이기
    numbered_members = [
        {'rank': idx + 1, 'member': member}
        for idx, member in enumerate(top_members)
    ]

    # 4개씩 나누기
    chunked_members = [numbered_members[i:i+4] for i in range(0, len(numbered_members), 4)]

    # 지역별 자산 합계 (지역 앞 2글자 기준)
    assets_by_region_qs = Legislator.objects.exclude(electoral_district__isnull=True).annotate(
        short_region=Left('electoral_district', 2)
    ).values('short_region').annotate(
        total_assets=Sum('total_assets')
    )
    region_assets = {item['short_region']: item['total_assets'] for item in assets_by_region_qs}
    regions = list(region_assets.keys())

    # 정당별 자산 합계
    assets_by_party_qs = Legislator.objects.exclude(party__isnull=True).values('party').annotate(
        total_assets=Sum('total_assets')
    )
    party_assets = {item['party']: item['total_assets'] for item in assets_by_party_qs}
    parties = list(party_assets.keys())

    # 지역별 상위 4명
    region_top4_data = {}
    for region in regions:
        top4 = Legislator.objects.filter(
            electoral_district__startswith=region
        ).order_by('-total_assets')[:4]
        region_top4_data[region] = [
            {'name': m.name, 'total_assets': m.total_assets or 0}
            for m in top4
        ]

    # 정당별 상위 4명
    party_top4_data = {}
    for party in parties:
        top4 = Legislator.objects.filter(
            party=party
        ).order_by('-total_assets')[:4]
        party_top4_data[party] = [
            {'name': m.name, 'total_assets': m.total_assets or 0}
            for m in top4
        ]

    return render(request, 'main_page.html', {
        'chunked_members': chunked_members,
        'region_assets': region_assets,
        'party_assets': party_assets,
        'region_top4': region_top4_data,
        'party_top4': party_top4_data,
        'regions': regions,
        'parties': parties,
    })



def member_list(request):  # 의원 목록 페이지
    order_by = request.GET.get('order_by', 'name')  # 기본 정렬: 이름
    query = request.GET.get('q', '')  # 검색어 파라미터

    # 필터링 조건
    party = request.GET.get('party')
    region = request.GET.get('region')

    # 기본 쿼리셋
    members = Legislator.objects.all()

    if query:
        members = members.filter(name__icontains=query)  # 이름 기준 검색
    if party:
        members = members.filter(party=party)
    if region:
        members = members.filter(electoral_district__startswith=region)

    # 정렬 기준 처리
    if order_by in ['name', '-total_assets']:
        members = members.order_by(order_by)
    else:
        members = members.order_by('name')  # 기본값

    # 필터용 데이터
    parties = Legislator.objects.exclude(party__isnull=True).exclude(party='').values_list('party', flat=True).distinct()
    districts = Legislator.objects.exclude(electoral_district__isnull=True).exclude(electoral_district='')\
        .values_list('electoral_district', flat=True)
    regions = sorted({d.split()[0] for d in districts if ' ' in d})  # 첫 단어 기준

    # 페이지네이션
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'member_list.html', {
        'order_by': order_by,
        'parties': parties,
        'regions': regions,
        'page_obj': page_obj,
        'query': query,
    })


def member_info(request, member_id): # 의원 상세 정보 페이지
    # 여기선 일단 임시 데이터로 구성
    member = get_object_or_404(Legislator, member_id=member_id)
    asset = Asset.objects.filter(legislator=member).order_by('-report_year', '-report_month')
    paginator = Paginator(asset, 10)  # 한 페이지에 10개

    # 연월별 자산 합계 계산
    assets_by_month = defaultdict(int)
    for asset in asset:
        if asset.report_year and asset.report_month:
            key = f"{asset.report_year}-{asset.report_month:02d}"
            assets_by_month[key] += asset.current_valuation or 0

    # 날짜 오름차순 정렬
    assets_by_month = dict(sorted(assets_by_month.items()))
    
    # 정렬된 딕셔너리를 리스트 2개로 분리
    labels = sorted(assets_by_month.keys())
    values = [assets_by_month[key] for key in labels]

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'member_info.html', {
        'member': member, 
        'page_obj': page_obj,
        'graph_labels': labels,
        'graph_data': values,
    })

def api_page(request): # api 정보 페이지
    return render(request, 'api_page.html')

def guide_page(request): # 이용안내
    return render(request, 'guide_page.html')