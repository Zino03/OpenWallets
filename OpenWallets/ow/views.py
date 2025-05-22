from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from datetime import date
from ow.models import Legislator, Asset

def main_page(request): # 대시보드 (메인 페이지)
    return render(request, 'main_page.html')

def member_list(request): # 의원 목록 페이지
    order_by = request.GET.get('order_by', 'name')  # 기본값: name
    members = Legislator.objects.all().order_by(order_by)
    party = request.GET.get('party')
    region = request.GET.get('region')

    # 조건 필터링
    if party:
        members = members.filter(party=party)
    if region:
        members = members.filter(electoral_district__startswith=region)
    
    parties = Legislator.objects.exclude(party__isnull=True).exclude(party='').values_list('party', flat=True).distinct()
    districts = Legislator.objects.exclude(electoral_district__isnull=True).exclude(electoral_district='')\
        .values_list('electoral_district', flat=True)

    regions = sorted({d.split()[0] for d in districts if ' ' in d})  # 첫 단어 기준 중복 제거 후 정렬
        
    paginator = Paginator(members, 10)  # 한 페이지에 10명
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'member_list.html', {
        'order_by' : order_by,
        'parties': parties,
        'regions': regions,
        'page_obj': page_obj,
    })

def member_info(request, member_id): # 의원 상세 정보 페이지
    # 여기선 일단 임시 데이터로 구성
    member = get_object_or_404(Legislator, member_id=member_id)
    asset = Asset.objects.filter(legislator=member).order_by('-updated_at')
    paginator = Paginator(asset, 10)  # 한 페이지에 10개

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'member_info.html', {
        'member': member, 
        'page_obj': page_obj,
    })

def api_page(request): # api 정보 페이지
    return render(request, 'api_page.html')

def guide_page(request): # 이용안내
    return render(request, 'guide_page.html')