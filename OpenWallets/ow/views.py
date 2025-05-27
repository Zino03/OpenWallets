from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ow.models import Legislator, Asset
from django.db.models import Sum
from collections import defaultdict
from django.db.models.functions import Left

def main_page(request):
    # 기존 top_members 쿼리 유지
    top_members = Legislator.objects.annotate(
        total_assets=Sum('assets__current_valuation')
    ).order_by('-total_assets')[:20]
    
        # 순번을 붙여서 리스트로 변환 (index 0부터 시작하므로 +1)
    numbered_members = [
        {'rank': idx + 1, 'member': member}
        for idx, member in enumerate(top_members)
    ]

    # 4개씩 나누기
    chunked_members = [numbered_members[i:i+4] for i in range(0, len(numbered_members), 4)]

    # 지역별 총 자산 (앞 두 글자만 추출해서 그룹화)
    assets_by_region_qs = Legislator.objects.annotate(
        short_region=Left('electoral_district', 2)  # region 필드 앞 2글자 추출
    ).values('short_region').annotate(
        total_assets=Sum('assets__current_valuation')
    )

    region_assets = {item['short_region']: item['total_assets'] for item in assets_by_region_qs}

    # 정당별 총 자산 예시
    assets_by_party_qs = Legislator.objects.values('party').annotate(
        total_assets=Sum('assets__current_valuation')
    )
    party_assets = {item['party']: item['total_assets'] for item in assets_by_party_qs}

    regions = list(region_assets.keys())
    parties = list(party_assets.keys())
    
    region_top4_data = {}
    for region in regions:
        top4 = Legislator.objects.filter(
            electoral_district__startswith=region
        ).annotate(
            total_assets=Sum('assets__current_valuation')
        ).order_by('-total_assets')[:4]
        region_top4_data[region] = [
            {'name': m.name, 'total_assets': m.total_assets or 0}
            for m in top4
        ]

    # 정당별 top4 의원
    party_top4_data = {}
    for party in parties:
        top4 = Legislator.objects.filter(
            party=party
        ).annotate(
            total_assets=Sum('assets__current_valuation')
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

    # 자산 합계 어노테이션
    members = members.annotate(
        total_assets=Sum('assets__current_valuation')
    )

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

    total_assets = asset.aggregate(sum=Sum('current_valuation'))['sum'] or 0 # 재산 합계
    
    # 연월별 자산 합계 계산
    assets_by_month = defaultdict(int)
    for asset in asset:
        if asset.report_year and asset.report_month:
            key = f"{asset.report_year}-{asset.report_month:02d}"
            assets_by_month[key] += asset.current_valuation or 0

    # 날짜 오름차순 정렬
    assets_by_month = dict(sorted(assets_by_month.items()))
    sorted_assets = dict(sorted(assets_by_month.items(), key=lambda x: x[0]))
    
    # 정렬된 딕셔너리를 리스트 2개로 분리
    labels = sorted(assets_by_month.keys())
    values = [assets_by_month[key] for key in labels]

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'member_info.html', {
        'member': member, 
        'page_obj': page_obj,
        'total_assets': total_assets,
        'graph_labels': labels,
        'graph_data': values,
        'sorted_assets': sorted_assets,
    })

def api_page(request): # api 정보 페이지
    return render(request, 'api_page.html')

def guide_page(request): # 이용안내
    return render(request, 'guide_page.html')