from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def main_page(request):
    return render(request, 'main_page.html')

def member_list(request):
    return render(request, 'member_list.html')

def member_info(request, member_id):
    # 여기선 일단 임시 데이터로 구성
    return render(request, 'member_info.html', {'member_id': member_id})

def api_page(request):
    return render(request, 'api_page.html')

def guide_page(request):
    return render(request, 'guide_page.html')