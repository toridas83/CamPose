# CamPose

> **2026 오픈소스 개발자 대회 출품작**  
> 정면 웹캠과 MediaPipe를 활용한 개인 맞춤형 실시간 자세 모니터링 서비스

CamPose는 PC 작업 중 사용자의 자세 변화를 웹캠으로 분석하고, 나쁜 자세가 일정 시간 이상 지속되면 화면 효과와 경고음으로 알려주는 Windows 데스크톱 애플리케이션입니다. 사용자가 직접 측정한 기준 자세와 현재 자세를 비교하여 개인별 신체 구조와 카메라 환경의 차이를 반영합니다.

<a id="table-of-contents"></a>
## 목차

1. [프로젝트 개요](#overview)
2. [주요 기능](#features)
3. [파일 구조 및 데이터 저장 형식](#structure-data)
4. [기술 스택](#tech-stack)
5. [설치 및 실행](#install-run)
6. [기대효과 및 향후 과제](#impact-roadmap)
7. [오픈소스 및 출처](#sources)

<a id="overview"></a>
## 1. 프로젝트 개요

장시간 PC를 사용하면 고개가 앞으로 나오거나 어깨와 몸통이 기울어지는 등의 자세가 반복될 수 있습니다. 그러나 사용자가 작업에 집중하는 동안 이러한 변화를 스스로 인지하기는 어렵습니다.

CamPose는 별도의 웨어러블 센서 없이 일반 웹캠과 자세 추정 모델을 이용해 사용자의 자세 변화를 실시간으로 분석합니다. 일시적인 움직임에는 즉시 경고하지 않고, 나쁜 자세가 설정된 허용 시간 이상 유지될 때 알림을 제공하여 과도한 알림을 줄였습니다.

### 서비스 흐름

```text
웹캠 영상 입력
   ↓
MediaPipe 신체 랜드마크 추출
   ↓
각도·거리·비율 특징값 계산
   ↓
개인 기준 자세와 현재 자세 비교
   ↓
자세 종류 및 1~3단계 판정
   ↓
지속시간·회복시간 계산
   ↓
화면/소리 알림 및 세션 기록
```

본 프로젝트는 의료 진단이 아닌 생활 습관 개선을 위한 자세 알림 서비스를 목적으로 합니다.

<a id="features"></a>
## 2. 주요 기능

### 개인 기준 자세 측정

- 측정 시작 전 3초의 자세 준비시간 제공
- 바른 자세를 10초 동안 다중 프레임으로 측정
- 각 특징값의 중앙값과 흔들림 범위를 개인 기준으로 저장
- 개인 기준에서 벗어난 변화량을 바탕으로 현재 자세 분석

### 실시간 자세 분석

- MediaPipe Pose Landmarker를 이용해 최대 33개 신체 랜드마크 추출
- 각도·거리·신체 비율을 계산해 자세 종류 판정
- 카메라 추정값의 순간적인 흔들림을 중앙값 필터로 완화
- 변화 정도를 1단계, 2단계, 3단계로 구분
- `강한 교정`, `기본`, `여유` 감지 민감도 제공

### 자세 분석 화면

- 거울 모드 카메라 영상과 스켈레톤 표시
- 현재 자세 종류, 단계, 지속시간 표시
- 사람·하체 감지 상태, FPS, 추론시간 표시
- 현재 특징값, 기준값, 변화량 확인

### 알림과 회복 판정

- 자세 단계별 허용시간 설정
- 우측 하단 팝업, 모니터 테두리 강조, 경고음 제공
- 화면 알림과 경고음을 독립적으로 설정
- 좋은 자세를 설정 시간 이상 유지했을 때 회복으로 판정
- 회복 후 같은 나쁜 자세가 재발하면 알림 시간을 새로 측정

### 기록과 대시보드

- 전체 측정시간, 좋은 자세 비율, 경고 횟수 기록
- 자세 종류별 누적시간과 최고 단계 저장
- 세션별 상세 통계와 막대그래프 제공
- 개별 기록 및 전체 기록 삭제
- 최근 최대 200개 세션 보관
- 시스템 트레이를 이용한 백그라운드 동작

### 감지 자세 목록

| 구분 | 감지 자세 | 주요 분석값 |
|---|---|---|
| 머리·목 | 거북목 | 머리 깊이 변화, 얼굴/어깨 비율 |
| 머리·목 | 고개 숙임 | 귀와 어깨 사이의 세로 간격 |
| 머리·목 | 고개 기울임 | 양쪽 눈을 연결한 선의 기울기 |
| 어깨 | 어깨 비대칭 | 양쪽 어깨를 연결한 선의 기울기 |
| 어깨 | 어깨 으쓱 | 한쪽 귀와 어깨 사이의 간격 감소 |
| 몸통 | 몸통 전방 기울임 | 몸통 깊이와 화면상 몸통 길이 변화 |
| 몸통 | 몸통 측면 기울임 | 어깨 중심과 골반 중심의 좌우 기울기 |
| 몸통 | 몸통 비틀림 | 양쪽 어깨의 깊이 차이 |
| 거리 | 화면에 가까움 | 기준 대비 화면상 어깨 너비 증가율 |
| 하체 | 한쪽 다리 올림 | 무릎 높이와 골반·무릎 간격 |
| 하체 | 양쪽 다리 올림 | 양쪽 무릎의 기준 대비 상승 비율 |
| 하체 | 다리 꼬기 | 발목이 몸의 중심선을 넘은 정도 |

하체 자세는 무릎 또는 발목이 카메라에 충분히 보이는 경우에만 판정합니다.

<a id="structure-data"></a>
## 3. 파일 구조 및 데이터 저장 형식

### 파일 구조

```text
CamPose-main/
├─ main.py                       # 애플리케이션 실행 파일
├─ README.md                     # 프로젝트 소개 및 실행 안내
├─ requirements.txt             # Python 라이브러리 목록
├─ pose_landmarker_lite.task    # MediaPipe 자세 추정 모델
│
├─ core/
│  ├─ cameras.py                # 카메라 검색 및 선택
│  ├─ classifier.py             # 자세 종류·단계 판정
│  ├─ config.py                 # 기본 설정과 저장 경로
│  ├─ features.py               # 랜드마크 특징값 계산
│  ├─ notifications.py          # 경고음 처리
│  ├─ service.py                # 카메라·MediaPipe 분석 처리
│  ├─ storage.py                # 세션 기록 저장·삭제
│  ├─ timers.py                 # 자세 지속시간과 회복 판정
│  └─ tray.py                   # 시스템 트레이 처리
│
├─ gui/
│  ├─ alerts.py                 # 팝업과 화면 테두리 알림
│  ├─ constants.py              # UI 공통 설정
│  ├─ history_page.py           # 기록과 세션 상세 화면
│  ├─ main_window.py            # 메인 창과 페이지 이동
│  ├─ monitoring_page.py        # 모니터링·기준 자세·분석 화면
│  └─ settings_page.py          # 설정 화면
│
├─ tests/                       # 핵심 로직 자동 검증 코드
│
└─ data/                        # 실행 중 자동 생성되는 사용자 데이터
```

`tests/`는 자세 판정, 카메라 선택, 알림 타이머, 저장 기능을 자동으로 검증하는 코드입니다. 앱 실행에는 필요하지 않지만 기능 변경 시 기존 동작이 깨지지 않았는지 확인하는 용도로 사용됩니다.

### 데이터 저장 형식

대회 출품 버전은 별도의 DB 없이 로컬 JSON 파일을 사용합니다.

| 파일 | 저장 내용 | 생성 시점 |
|---|---|---|
| `data/settings.json` | 카메라, 민감도, 알림, 허용시간 등 사용자 설정 | 설정 저장 시 |
| `data/baseline.json` | 개인 기준 자세의 특징값과 흔들림 범위 | 기준 자세 측정 완료 시 |
| `data/history.json` | 측정시간, 좋은 자세 비율, 자세별 지속시간, 경고 횟수 | 측정 종료 및 기록 저장 시 |

JSON 파일이 없어도 앱은 기본 설정으로 실행됩니다. `data/` 폴더와 각 JSON 파일은 필요한 시점에 자동 생성됩니다. 카메라 영상과 이미지는 저장하지 않습니다.

<a id="tech-stack"></a>
## 4. 기술 스택

| 분류 | 기술 | 용도 |
|---|---|---|
| Language | Python 3.11 | 애플리케이션 전체 구현 |
| GUI | CustomTkinter, Tkinter | Windows 데스크톱 대시보드 |
| Pose Estimation | MediaPipe Tasks | 신체 랜드마크 추출 |
| Computer Vision | OpenCV | 카메라 입력과 영상 처리 |
| Image | Pillow | 카메라 프레임 UI 표시 |
| Numeric | NumPy | 프레임과 특징값 처리 |
| Camera | PyGrabber | Windows 카메라 장치 검색 |
| Background | pystray | 시스템 트레이 실행 |
| Storage | JSON | 설정, 기준 자세, 세션 기록 저장 |

<a id="install-run"></a>
## 5. 설치 및 실행

실행 환경은 Windows 10/11과 Python 3.11을 기준으로 합니다.

### 가상환경 생성

```powershell
conda create -n campose python=3.11 -y
conda activate campose
```

### 라이브러리 설치

```powershell
python -m pip install -r requirements.txt
```

### 모델 파일 확인

`pose_landmarker_lite.task`가 `main.py`와 같은 최상위 폴더에 있어야 합니다.

```text
CamPose-main/
├─ main.py
└─ pose_landmarker_lite.task
```

모델 파일: [MediaPipe Pose Landmarker Lite](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task)

### 실행

프로젝트 최상위 폴더에서 `main.py`를 실행합니다.

```powershell
python main.py
```

<a id="impact-roadmap"></a>
## 6. 기대효과 및 향후 과제

### 기대효과

- 별도 센서 없이 일반 웹캠만으로 자세 변화를 확인할 수 있습니다.
- 개인 기준 자세를 활용하여 체형과 촬영 환경의 차이를 일부 반영할 수 있습니다.
- 나쁜 자세를 즉시 단정하지 않고 지속시간을 함께 판단하여 불필요한 알림을 줄입니다.
- 백그라운드에서 자세를 분석하므로 작업 흐름을 크게 방해하지 않습니다.
- 세션 기록과 상세 통계를 통해 자주 발생하는 자세와 취약 시간대를 확인할 수 있습니다.
- 영상은 저장하지 않고 자세 수치와 요약 기록만 로컬에 보관합니다.
- 라이브러리와 모델 설치 후에는 핵심 분석 기능을 오프라인으로 실행할 수 있습니다.

### 현재 범위

- Windows 로컬 데스크톱 애플리케이션
- 사용자 정면에 위치한 단일 웹캠
- 개인 기준 대비 자세 변화 감지
- 화면·소리 알림과 로컬 JSON 기록

### 향후 과제

- 측면 또는 비정면 카메라 각도를 고려한 분석 고도화
- 사용자별 나쁜 자세 범위를 사전 측정하는 추가 캘리브레이션
- SQLite 기반 기록 저장과 데이터 마이그레이션
- EXE 및 설치 프로그램 형태의 배포
- Windows 로그인 시 자동 시작 옵션
- 같은 자세 유지 및 연속 작업에 대한 휴식 알림 로직 완성
- 다양한 체형·조명·카메라 환경에서의 임계값 검증

<a id="sources"></a>
## 7. 오픈소스 및 출처

- [Google AI Edge - MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)
- [MediaPipe GitHub](https://github.com/google-ai-edge/mediapipe)
- [MediaPipe Apache 2.0 License](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)
- [MediaPipe Pose Landmarker Lite 모델](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [OpenCV](https://opencv.org/)
