# 피부 안전성 평가 대시보드

Streamlit으로 만든 피부 안전성 평가 대시보드입니다. 선택된 성분별로 MoS, 시간 거동, 규제 정보, 상세 데이터, 기준치 출처를 시각화합니다.

## 파일 구성

- `dashboard.py` - 메인 Streamlit 앱
- `requirements.txt` - Python 패키지 목록
- `data/` - 데이터 파일 폴더
  - `성분_CAS_요약_정제.csv` - 요약 데이터
  - `상세_MoS_정제.csv` - 상세 MoS 데이터
  - `전체_레퍼런스.csv` - 기준치 출처 데이터
  - `pbpk_concentration_timeseries_surface_model.csv` - 시계열 PBPk 데이터

## 실행 환경

- Python 3.9 이상 권장
- `requirements.txt`에 정의된 패키지 사용

## 설치 및 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

## 사용 방법

1. 브라우저에서 Streamlit이 시작되면 사이드바의 `분석할 성분 선택`에서 성분을 선택합니다.
2. 각 탭에서 안정성 요약, 안정성 분석, 시간 거동 분석, 규제 정보, 상세 데이터, 기준치 출처를 확인할 수 있습니다.

## 주의 사항

- `dashboard.py`는 프로젝트 루트 폴더 내의 `data/` 폴더에서 데이터를 로드합니다.
- `data/` 폴더와 그 안의 4개 CSV 파일이 모두 존재해야 합니다.

