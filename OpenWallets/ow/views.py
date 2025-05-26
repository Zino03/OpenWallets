from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ow.models import Legislator, Asset
from django.db.models import Sum
from collections import defaultdict

def main_page(request): # 대시보드 (메인 페이지)
    return render(request, 'main_page.html')

def member_list(request):  # 의원 목록 페이지
    order_by = request.GET.get('order_by', 'name')  # 기본 정렬: 이름

    # 필터링 조건
    party = request.GET.get('party')
    region = request.GET.get('region')

    # 기본 쿼리셋
    members = Legislator.objects.all()

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