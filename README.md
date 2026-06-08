# OpenWallets

**22대 국회의원 재산 공개 웹 서비스**

대한민국 국회의원의 재산 신고 데이터를 수집·정리하여 누구나 쉽게 조회할 수 있도록 제공하는 오픈소스 웹 애플리케이션입니다.

---

## 주요 기능

- **메인 페이지**: 전체 의원 중 재산 상위 20명 표시, 지역·정당별 재산 집계 및 상위 5명 비교
- **의원 목록**: 정당·지역 필터링, 이름 검색, 정렬, 페이지네이션 지원
- **의원 상세 페이지**: 개별 의원의 재산 내역 및 연도별 자산 변화 그래프
- **API 안내 페이지**: REST API 사용법 제공
- **이용 가이드**: 서비스 이용 방법 안내

---

## 기술 스택

- **Backend** — Python 3, Django 5.2, Django REST Framework
- **Database** — SQLite
- **서버** — Gunicorn, WhiteNoise
- **배포** — Render
---

## 데이터 모델

### Legislator (의원)
- 이름, 한자명, 생년월일, 성별
- 정당, 선거구, 소속 위원회, 당선 횟수
- 연락처(전화, 이메일)
- 총 재산 합계

### Asset (재산)
- 신고 연월, 재산 종류 및 세부 종목
- 명의자 관계
- 현재가액, 종전가액, 증감액, 변동 사유

---

## URL 구조

| URL | 설명 |
|-----|------|
| `/` | 메인 페이지 |
| `/members/` | 의원 목록 |
| `/members/<member_id>/` | 의원 상세 정보 |
| `/api/` | API 안내 |
| `/guide/` | 이용 가이드 |

---

## 로컬 실행 방법

```bash
# 1. 저장소 클론
git clone https://github.com/Zino03/OpenWallets.git
cd OpenWallets

# 2. 의존성 설치
pip install -r requirements.txt

# 3. DB 마이그레이션
python manage.py migrate

# 4. 개발 서버 실행
python manage.py runserver
브라우저에서 http://127.0.0.1:8000 접속

배포 (Render)
render.yaml을 통해 Render 플랫폼 자동 배포가 구성되어 있습니다.

이 프로젝트는 오픈소스입니다. 자세한 내용은 저장소를 참고하세요.


---

이 README를 파일로 저장하거나 수정이 필요한 부분이 있으면 말씀해 주세요.
