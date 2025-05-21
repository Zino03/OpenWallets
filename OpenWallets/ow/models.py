from django.db import models
    
class AssemblyMember(models.Model):
    code = models.CharField(max_length=100, unique=True) # 식별 코드
    name = models.CharField(max_length=100) # 이름
    chinese_name = models.CharField(max_length=100) # 한자 이름
    birth_cd = models.BooleanField() # 양력 / 음력
    birth_date = models.DateField() # 생년월일
    position = models.CharField(max_length=100) # 직책
    party = models.CharField(max_length=100) # 정당
    ward = models.CharField(max_length=100) # 선거구
    committee = models.CharField(max_length=100) # 위원회
    session = models.CharField(max_length=10)  # 대수
    gender = models.BooleanField() # 성별
    tel = models.CharField(max_length=20) # 전화번호
    email = models.CharField(max_length=100) # 이메일
    history =  models.JSONField(default = list) # 약력
    office =  models.JSONField(default = list) # 사무실 호실
    year_month = models.CharField(max_length=10) # 재산 신고 연월
    pro_classify = models.CharField(max_length=100) # 재산 구분 
    pro_relationship = models.CharField(max_length=10) # 본인과의 관계
    pro_kind = models.CharField(max_length=100) # 재산 종류
    pro_details = models.CharField(max_length=100) # 소재지 aus적 등 권리의 명세 (분할 예정)
    pre_price = models.IntegerField() # 종전가액
    inc_price = models.IntegerField() # 증가액
    inc_autual_price = models.IntegerField() # 증가액실거래가
    dec_price = models.IntegerField() # 감소액
    dec_actual_price = models.IntegerField() # 감소액실거래가
    cur_price = models.IntegerField() # 현재액
    change = models.CharField(max_length = 100) # 변동사유
    sum_price = models.IntegerField() # 신고된 재산의 현재액 합
    year_price = models.JSONField(default = list) # 연도별 재산

    
class Property(models.Model):
    region_price = models.JSONField(default = dict)
    poly_price = models.JSONField(default = dict)