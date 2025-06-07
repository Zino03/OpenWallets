from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ow.models import Legislator, Asset
from django.db.models import Sum
from collections import defaultdict
from django.db.models.functions import Left

def main_page(request): # 모든 데이터는 22대로 제한
    # 재산 총에 기준으로 내림차순 정렬하여 상위 의원 20명 슬라이싱
    top_members = Legislator.objects.filter(latest_age__contains='22대').order_by('-total_assets')[:20]

    # 순위 붙이기 (각 항목은 순위, Legislator 객체로 구성된 딕셔너리)
    numbered_members = [ 
        {'rank': idx + 1, 'member': member}
        for idx, member in enumerate(top_members)
    ]

    # 4개씩 나누기 -> 4개씩 한 화면에 출력하기 위함
    chunked_members = [numbered_members[i:i+4] for i in range(0, len(numbered_members), 4)]

    # 지역별 자산 합계 (지역 앞 2글자 기준)
    assets_by_region_qs = Legislator.objects.filter(
        latest_age__contains='22대'
    ).exclude(
        electoral_district__isnull=True
    ).exclude(
        electoral_district__startswith='비례' # 비례대표는 제외
    ).annotate(
        short_region=Left('electoral_district', 2)
    ).values('short_region').annotate( # 지역에 해당하는 의원들의 재산 총액을 모두 더함
        total_assets=Sum('total_assets')
    )
    
    # 지역 : 총액으로 이루어진 딕셔너리
    region_assets = {item['short_region']: item['total_assets'] for item in assets_by_region_qs}
    # 키, 값을 각각 리스트로 나눠서 전달(차트용)
    regions = list(region_assets.keys())
    region_asset_values = list(region_assets.values())

    # 정당별 자산 합계
    assets_by_party_qs = Legislator.objects.filter(
        latest_age__contains='22대'
    ).exclude(party__isnull=True).values('party').annotate(
        total_assets=Sum('total_assets')
    )
    # 정당 : 총액으로 이루어진 딕셔너리
    party_assets = {item['party']: item['total_assets'] for item in assets_by_party_qs}
    # 키, 값을 각각 리스트로 나눠서 전달(차트용)
    parties = list(party_assets.keys())
    party_asset_values = list(party_assets.values())

    # 지역별 상위 5명
    region_top5_data = {}
    for region in regions:
        top5 = Legislator.objects.filter(
            latest_age__contains='22대',
            electoral_district__startswith=region # 지역에 해당하는 의원 필터
        ).order_by('-total_assets')[:5] # 상위 5명까지만 저장
        region_top5_data[region] = [
            # 이름, 재산총액, 의원 id(id는 카드 클릭 시 페이지 이동을 위해 필요)를 담은 딕셔너리를 각 지역에(키) 해당하는 값으로 저장 
            {'name': m.name, 'total_assets': m.total_assets or 0, 'member_id': m.member_id}
            for m in top5
        ]

    # 정당별 상위 5명
    party_top5_data = {}
    for party in parties:
        top5 = Legislator.objects.filter(
            latest_age__contains='22대',
            party=party # 정당에 해당하는 의원 필터
        ).order_by('-total_assets')[:5] # 상위 5명까지만 저장
        party_top5_data[party] = [
            # 이름, 재산총액, 의원 id(id는 카드 클릭 시 페이지 이동을 위해 필요)를 담은 딕셔너리를 각 정당에(키) 해당하는 값으로 저장 
            {'name': m.name, 'total_assets': m.total_assets or 0, 'member_id': m.member_id}
            for m in top5
        ]

    return render(request, 'main_page.html', {
        'chunked_members': chunked_members, # 상위 20위 슬라이더를 위해 4명씩 자른 리스트
        'region_assets': region_assets, # 지역별 총 재산을 담은 딕셔너리
        'party_assets': party_assets, # 정당별 총 재산을 담은 딕셔너리
        'region_top5': region_top5_data, # 지역별 재산 상위 5위 의원 딕셔너리
        'party_top5': party_top5_data, # 정당별 재산 상위 5위 의원 딕셔너리
        
        # 아래 리스트들은 차트를 만들기 위해 따로 제공하는 것
        'regions': regions, # 선택 가능한 지역을 담은 리스트
        'parties': parties, # 선택 가능한 정당을 담은 리스트
        'party_asset_values': party_asset_values, # 지역의 재산 총액을 담은 리스트
        'region_asset_values': region_asset_values, # 정당의 재산 총액을 담은 리스트
    })



def member_list(request):  # 의원 목록 페이지
    order_by = request.GET.get('order_by', 'name')  # 기본 정렬: 이름
    query = request.GET.get('q', '')  # 검색어 파라미터

    # 필터링용 값 가져오기
    party = request.GET.get('party')
    region = request.GET.get('region')

    # 전체 의원 가져오기
    members = Legislator.objects.all()

    if query:
        members = members.filter(name__icontains=query)  # 이름 기준 검색
    if party:
        members = members.filter(party=party) # 정당 필터
    if region:
        members = members.filter(electoral_district__startswith=region) # 지역 필터

    # 정렬 기준 처리
    if order_by in ['name', '-total_assets']: # 이름순, 재산순
        members = members.order_by(order_by)
    else:
        members = members.order_by('name')  # 기본값

    # 필터용 데이터 (드롭박스)
    parties = Legislator.objects.exclude(party__isnull=True).exclude(party='').values_list('party', flat=True).distinct()
    districts = Legislator.objects.exclude(electoral_district__isnull=True).exclude(electoral_district='')\
        .values_list('electoral_district', flat=True)
    regions = sorted({d.split()[0] for d in districts if ' ' in d})  # 첫 단어 기준

    # 페이지네이션
    paginator = Paginator(members, 20) # 한 페이지에 20명
    page_number = request.GET.get('page') # 현재 페이지 번호
    # 10 페이지 범위 단위 구성
    page_obj = paginator.get_page(page_number)
    current_page = page_obj.number
    page_start = ((current_page - 1) // 10) * 10 + 1 
    page_end = min(page_start + 9, page_obj.paginator.num_pages)
    page_range = range(page_start, page_end + 1)

    return render(request, 'member_list.html', {
        'order_by': order_by, # 정렬 기준 선택
        'parties': parties, # 드롭박스용 정당 목록
        'regions': regions, # 드롭박스용 지역 목록
        'page_obj': page_obj, # 현재 페이지의 데이터 목록
        'page_range': page_range, # 페이지 개수 체크를 위함
        'query': query, # 검색용
    })


def member_info(request, member_id): # 의원 상세 정보 페이지
    # 해당 의원 id를 가진 의원 데이터를 가져옴 (존재하지 않는 경우 404 페이지)
    member = get_object_or_404(Legislator, member_id=member_id) 
    # 그 의원의 재산 내역을 가져옴
    asset = Asset.objects.filter(legislator=member).order_by('-report_year', '-report_month')
    # 한 페이지에 10명씩 담음
    paginator = Paginator(asset, 10)

    # 연월별 자산 합계 계산 (재산 변화 그래프용)
    assets_by_month = defaultdict(int) # 연월 : 총액 형태의 딕셔너리
    for asset in asset:
        # 해당 연월의 재산 내역을 모두 합산
        if asset.report_year and asset.report_month:
            key = f"{asset.report_year}-{asset.report_month:02d}"
            assets_by_month[key] += asset.current_valuation or 0

    # 날짜 오름차순 정렬 (그래프 테이블을 위함)
    assets_by_month = dict(sorted(assets_by_month.items()))
    
    # 정렬된 딕셔너리를 리스트 2개로 분리 (그래프용)
    labels = sorted(assets_by_month.keys())
    values = [assets_by_month[key] for key in labels]
    
    # 페이지네이션
    page_number = request.GET.get('page') # 현재 페이지 번호
    page_obj = paginator.get_page(page_number)
    # 10 페이지 범위 단위 구성
    current_page = page_obj.number 
    page_start = ((current_page - 1) // 10) * 10 + 1
    page_end = min(page_start + 9, page_obj.paginator.num_pages)
    page_range = range(page_start, page_end + 1)
    
    return render(request, 'member_info.html', {
        'member': member, # 의원 기본 정보
        'page_obj': page_obj, # 현재 페이지의 데이터 목록
        'page_range': page_range, # 페이지 개수 체크를 위함
        'graph_labels': labels, # 그래프 x축 (연월)
        'graph_data': values, # 그래프 y축 (금액)
    })

def api_page(request): # api 정보 페이지
    return render(request, 'api_page.html')

def guide_page(request): # 이용안내
    return render(request, 'guide_page.html')