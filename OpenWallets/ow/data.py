from ow.models import AssemblyMember, AssemblyProperty, Property

# AssemblyMember 저장
member = AssemblyMember.objects.create(
    code="1234",
    name="홍길동",
    chinese_name="洪吉東",
    birth_cd=True,  # 양력
    birth_date="1970-01-01",
    position="위원",
    party="더불어민주당",
    ward="서울 종로구",
    committee="국토교통위원회",
    number="21",
    gender=True,  # 남자
    tel="010-1234-5678",
    email="hong@example.com",
    history=["서울시의원", "교육부 장관"],
    office=["의원회관 123호"]
)
member.save()

# AssemblyProperty 저장
prop = AssemblyProperty.objects.create(
    code="1234",
    year_month="2024-03",
    pro_classify="본인",
    pro_relationship="본인",
    pro_kind="부동산",
    pro_details="서울 종로구 OOO",
    pre_price=10000,
    inc_price=2000,
    inc_autual_price=1900,
    dec_price=0,
    dec_actual_price=0,
    cur_price=12000,
    change="신규 취득",
    sum_price=30000,
    year_price=[10000, 11000, 12000]
)

# Property 저장
prop_stats = Property.objects.create(
    region_price={"서울 종로구": 12000, "강남구": 15000},
    poly_price={"더불어민주당": 100000, "국민의힘": 90000}
)