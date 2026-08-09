# CamPose

> **2026 오픈소스 개발자 대회 출품작**  
> 정면 웹캠과 MediaPipe를 이용한 개인 맞춤형 실시간 자세 모니터링 애플리케이션

CamPose는 PC를 사용하는 동안 웹캠 영상에서 사용자의 신체 랜드마크를 추출하고, 개인 기준 자세와 현재 자세의 차이를 분석하는 Windows 데스크톱 애플리케이션입니다. 나쁜 자세가 설정한 시간 이상 지속되면 화면 효과와 경고음으로 알려주며, 측정 결과는 로컬 JSON 파일에 기록합니다.

영상과 이미지는 저장하지 않으며 자세 추론, 설정 저장, 기록 조회는 사용자의 PC에서 처리됩니다.

<a id="table-of-contents"></a>
## 목차

- [프로젝트 개요](#overview)
- [핵심 기능](#features)
- [감지 자세](#postures)
- [동작 흐름](#workflow)
- [파일 구조](#structure)
- [데이터 저장 형식](#data-storage)
- [사용 모델](#model)
- [기술 스택](#tech-stack)
- [실행 환경](#requirements)
- [설치 방법](#installation)
- [실행 및 사용 방법](#usage)
- [테스트 방법](#testing)
- [개인정보 보호](#privacy)
- [현재 범위와 후속 과제](#roadmap)
- [문제 해결](#troubleshooting)
- [오픈소스 및 출처](#open-source)

<a id="overview"></a>
## 프로젝트 개요

장시간 PC 작업 중에는 사용자가 자신의 자세 변화를 즉시 알아차리기 어렵습니다. CamPose는 별도의 웨어러블 센서 없이 일반 웹캠만으로 자세 변화를 감지하고, 다음과 같은 흐름으로 자세 개선을 돕는 것을 목표로 합니다.

1. 사용자의 평소 바른 자세를 개인 기준으로 측정합니다.
2. 현재 자세와 개인 기준 자세의 랜드마크·각도·비율 차이를 비교합니다.
3. 변화 정도를 1~3단계로 구분하고 지속시간을 측정합니다.
4. 설정한 허용 시간을 넘으면 화면 알림 또는 경고음을 제공합니다.
5. 세션별 자세 시간과 경고 횟수를 기록하고 리포트로 보여줍니다.

본 프로젝트는 **생활 습관 개선을 위한 자세 알림 서비스**입니다.

<a id="features"></a>
## 핵심 기능

### 개인 기준 자세 설정

- 시작 버튼을 누른 뒤 3초의 준비시간 제공
- 바른 자세를 10초 동안 다중 프레임으로 측정
- 각 특징값의 중앙값과 흔들림 범위를 개인 기준으로 저장
- 카메라 장치 또는 사용 위치가 바뀌면 다시 설정 가능

### 실시간 자세 분석

- MediaPipe Pose Landmarker로 최대 33개 신체 랜드마크 추출
- 개인 기준 자세 대비 각도·거리·비율 변화 계산
- 카메라 추정값의 순간적인 흔들림을 중앙값 필터로 완화
- 자세별 심각도를 1단계, 2단계, 3단계로 구분
- `강한 교정`, `기본`, `여유` 민감도 제공

### 자세 분석 화면

- 사용자가 보기 편한 거울 모드 카메라 영상
- 영상 위에 관절점과 스켈레톤 표시
- 현재 감지 자세, 심각도, 지속시간 표시
- FPS, 추론시간, 사람·하체 감지 상태 표시
- 현재 특징값, 기준값, 변화량 확인
- 영상 위 스켈레톤 표시 여부를 설정에서 제어

### 알림 및 회복 판정

- 단계별 허용 시간을 각각 설정
- 우측 하단 팝업, 모니터 테두리 강조 또는 두 효과 동시 사용
- 화면 알림과 경고음을 독립적으로 설정
- 좋은 자세를 설정 시간 이상 유지했을 때 회복으로 판정
- 회복 후 같은 나쁜 자세가 다시 발생하면 알림 시간을 새로 측정

### 기록 및 리포트

- 세션별 전체 측정시간, 좋은 자세 비율, 경고 횟수 저장
- 자세 종류별 누적시간과 최고 단계 저장
- 동일한 앱 창 안에서 세션 상세 통계와 막대그래프 표시
- 개별 기록 삭제 및 전체 기록 삭제
- 최근 최대 200개 세션 보관

### 데스크톱 사용성

- Windows에서 확인되는 카메라 장치 목록 제공
- 설정 저장 시 선택한 카메라를 즉시 다시 연결
- 창을 닫아도 시스템 트레이에서 백그라운드 동작 가능
- 트레이 메뉴, 앱 버튼 또는 `Ctrl+C`를 이용한 안전 종료

<a id="postures"></a>
## 감지 자세

| 구분 | 감지 자세 | 주요 분석값 |
|---|---|---|
| 머리·목 | 거북목 | 머리 깊이 변화, 얼굴/어깨 비율 |
| 머리·목 | 고개 숙임 | 귀와 어깨 사이의 세로 간격 |
| 머리·목 | 고개 기울임 | 양쪽 눈을 연결한 선의 기울기 |
| 어깨 | 어깨 비대칭 | 양쪽 어깨를 연결한 선의 기울기 |
| 어깨 | 어깨 으쓱 | 한쪽 귀와 어깨 사이의 간격 감소 |
| 몸통 | 몸통 전방 기울임 | 몸통 깊이 및 화면상 몸통 길이 변화 |
| 몸통 | 몸통 측면 기울임 | 어깨 중심과 골반 중심의 좌우 기울기 |
| 몸통 | 몸통 비틀림 | 양쪽 어깨의 깊이 차이 |
| 거리 | 화면에 가까움 | 기준 대비 화면상 어깨 너비 증가율 |
| 하체 | 한쪽 다리 올림 | 무릎 높이와 골반·무릎 간격 |
| 하체 | 양쪽 다리 올림 | 양쪽 무릎의 기준 대비 상승 비율 |
| 하체 | 다리 꼬기 | 발목이 몸의 중심선을 넘은 정도 |

하체 자세는 무릎 또는 발목이 카메라에 충분히 보이는 경우에만 판정합니다.

<a id="workflow"></a>
## 동작 흐름

```text
웹캠 프레임
   ↓
OpenCV 영상 입력
   ↓
MediaPipe Pose Landmarker - 신체 랜드마크 추출
   ↓
각도·거리·비율 특징값 계산 및 프레임 안정화
   ↓
개인 기준 자세와 비교
   ↓
자세 종류 및 1~3단계 판정
   ↓
지속시간·회복시간 계산
   ↓
화면/소리 알림 + 세션 기록
```

<a id="structure"></a>
## 파일 구조

```text
CamPose-main/
├─ main.py                       # 애플리케이션 진입점
├─ README.md                     # 프로젝트 설명 및 실행 가이드
├─ requirements.txt             # Python 라이브러리 목록
├─ pose_landmarker_lite.task    # MediaPipe Pose Landmarker 모델
│
├─ core/
│  ├─ cameras.py                # Windows 카메라 검색 및 장치 선택
│  ├─ classifier.py             # 자세 종류·단계 판정
│  ├─ config.py                 # 기본 설정과 JSON 저장 경로
│  ├─ features.py               # 랜드마크 특징값 계산
│  ├─ notifications.py          # 경고음 처리
│  ├─ service.py                # 카메라·MediaPipe 분석 작업자
│  ├─ storage.py                # 세션 기록 저장·삭제
│  ├─ timers.py                 # 자세 지속시간과 회복 판정
│  └─ tray.py                   # Windows 시스템 트레이
│
├─ gui/
│  ├─ alerts.py                 # 팝업과 화면 테두리 알림
│  ├─ constants.py              # UI 색상·글꼴·레이아웃 상수
│  ├─ history_page.py           # 기록 목록 및 세션 상세 화면
│  ├─ main_window.py            # 메인 창, 페이지 이동, 종료 처리
│  ├─ monitoring_page.py        # 모니터링·기준 자세·분석 화면
│  └─ settings_page.py          # 설정 화면
│
└─ tests/
   ├─ test_cameras.py
   ├─ test_classifier.py
   ├─ test_service_settings.py
   ├─ test_storage.py
   └─ test_timers.py
```

다음 항목은 실행 중 자동 생성되는 사용자별 데이터이므로 GitHub에 업로드하지 않습니다.

```text
data/
Python/
tmp/
__pycache__/
```

<a id="data-storage"></a>
## 데이터 저장 형식

현재 대회 출품 버전은 별도의 DB 서버나 SQLite를 사용하지 않고 로컬 JSON 파일을 사용합니다.

| 파일 | 저장 내용 | 생성 시점 |
|---|---|---|
| `data/settings.json` | 카메라, 민감도, 알림, 허용시간 등 사용자 설정 | 설정 저장 시 |
| `data/baseline.json` | 10초간 측정한 개인 기준 특징값과 흔들림 범위 | 기준 자세 측정 완료 시 |
| `data/history.json` | 세션 시간, 좋은 자세 비율, 자세별 지속시간, 경고 횟수 | 측정 종료 및 기록 저장 시 |

JSON 파일이 없어도 앱은 정상 실행됩니다. `data/` 폴더는 자동으로 생성되고, 설정 파일이 없으면 코드에 정의된 기본값으로 시작합니다. 이후 사용자가 설정을 저장하거나 측정을 완료하면 필요한 JSON 파일이 자동 생성됩니다.

<a id="model"></a>
## 사용 모델

### MediaPipe Pose Landmarker Lite

- 모델 파일: `pose_landmarker_lite.task`
- 입력: 웹캠 RGB 프레임
- 출력: 신체 랜드마크 최대 33개와 정규화 좌표·월드 좌표
- 실행 방식: 사용자 PC에서 온디바이스 추론
- 활용 항목: 얼굴, 눈, 귀, 어깨, 골반, 무릎, 발목 등의 위치와 가시성

모델 파일은 `main.py`와 같은 프로젝트 최상위 폴더에 위치해야 합니다.

```text
CamPose-main/pose_landmarker_lite.task
```

모델 파일이 저장소에 포함되지 않은 경우 다음 명령으로 내려받을 수 있습니다.

```powershell
Invoke-WebRequest `
  -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task" `
  -OutFile "pose_landmarker_lite.task"
```

<a id="tech-stack"></a>
## 기술 스택

| 분류 | 기술 | 용도 |
|---|---|---|
| Language | Python 3.11 | 애플리케이션 전체 구현 |
| GUI | CustomTkinter, Tkinter | Windows 데스크톱 대시보드 |
| Pose Estimation | MediaPipe Tasks | 33개 신체 랜드마크 추출 |
| Computer Vision | OpenCV | 카메라 입력, 영상 변환, 스켈레톤 렌더링 |
| Image | Pillow | Tkinter 카메라 프레임 표시 |
| Numeric | NumPy | 프레임·수치 데이터 처리 |
| Camera | PyGrabber | Windows 카메라 장치명 검색 |
| Background | pystray | 시스템 트레이 실행 |
| Storage | JSON | 설정, 개인 기준 자세, 세션 기록 저장 |
| Test | unittest | 자세 판정·타이머·저장 로직 회귀 테스트 |

<a id="requirements"></a>
## 실행 환경

- Windows 10 또는 Windows 11
- Python 3.11 권장
- Conda 또는 Miniconda 권장
- 내장 카메라 또는 USB 웹캠
- 최초 설치 시 인터넷 연결
- 실행 시 `pose_landmarker_lite.task` 모델 파일

라이브러리와 모델 설치를 마친 뒤에는 자세 분석과 기록 기능을 오프라인으로 실행할 수 있습니다.

<a id="installation"></a>
## 설치 방법

### 1. 프로젝트 준비

GitHub의 `Code > Download ZIP`으로 내려받아 압축을 풀거나 Git을 사용합니다.

```powershell
git clone <저장소-주소>
cd CamPose-main
```

ZIP으로 받은 경우 VSCode에서 `CamPose-main` 폴더를 연 뒤 터미널을 실행합니다.

### 2. Conda 가상환경 생성

```powershell
conda create -n campose python=3.11 -y
conda activate campose
```

VSCode를 사용하는 경우 `Ctrl+Shift+P`를 누르고 `Python: Select Interpreter`에서 `campose` 환경을 선택합니다.

### 3. 라이브러리 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

설치되는 주요 라이브러리는 다음과 같습니다.

```text
customtkinter
mediapipe
opencv-python
pillow
numpy
pygrabber
pystray
```

### 4. 모델 파일 확인

프로젝트 최상위 폴더에 아래 파일이 있는지 확인합니다.

```text
pose_landmarker_lite.task
```

없다면 [사용 모델](#model)의 다운로드 명령을 실행합니다.

<a id="usage"></a>
## 실행 및 사용 방법

### 앱 실행

```powershell
conda activate campose
cd <CamPose-main이-있는-경로>
python main.py
```

예시:

```powershell
cd D:\05_opensource_contest\CamPose-main
python main.py
```

### 최초 사용 순서

1. `설정 > 감지 설정 > 사용할 카메라`에서 실제 웹캠을 선택하고 설정을 저장합니다.
2. 홈 화면에서 `기준 자세 설정`을 누릅니다.
3. 시작 버튼을 누른 뒤 준비시간 3초 동안 바른 자세로 앉습니다.
4. 이어지는 10초 동안 정면을 보고 자연스러운 바른 자세를 유지합니다.
5. 홈으로 돌아오면 `측정 시작`을 누릅니다.
6. 필요하면 `자세 분석 화면 열기`에서 영상, 스켈레톤, 감지 자세와 특징값을 확인합니다.
7. 측정을 마치면 `측정 종료 및 기록 저장`을 누릅니다.
8. `기록`에서 세션 결과와 상세 통계를 확인합니다.

### 종료 방법

- 창의 `X` 버튼: 백그라운드 숨기기 또는 완전 종료 선택
- 사이드바: `백그라운드로 숨기기` 또는 `앱 완전히 종료`
- 시스템 트레이 아이콘: 앱 열기 또는 종료
- 터미널: `Ctrl+C`

<a id="testing"></a>
## 테스트 방법

프로젝트 최상위 폴더에서 다음 명령을 실행합니다.

```powershell
python -m unittest discover -s tests -v
```

수동 테스트 권장 항목:

1. 바른 자세에서 불필요한 2·3단계 판정이 반복되지 않는지 확인합니다.
2. 고개 기울이기, 한쪽 어깨 내리기, 몸통 좌우 기울이기를 순서대로 확인합니다.
3. 화면 가까이 다가가기와 몸통 앞으로 숙이기가 구분되는지 확인합니다.
4. 하체가 보이는 환경에서는 다리 올림과 다리 꼬기를 확인합니다.
5. 단계별 허용시간을 짧게 설정하고 화면 알림·경고음을 확인합니다.
6. 좋은 자세를 회복 판정 시간 이상 유지한 뒤 같은 자세가 재발할 때 다시 알림되는지 확인합니다.
7. 측정 종료 후 기록과 상세 통계가 저장되는지 확인합니다.

<a id="privacy"></a>
## 개인정보 보호

- 카메라 영상과 이미지를 파일로 저장하지 않습니다.
- 자세 분석을 위한 영상 처리는 사용자 PC에서 수행됩니다.
- 서버 또는 외부 DB로 자세 기록을 전송하는 코드는 포함되어 있지 않습니다.
- 설정, 기준 자세 수치, 세션 요약만 `data/` 폴더에 JSON으로 저장합니다.
- 사용자는 기록 화면에서 개별 기록 또는 전체 기록을 삭제할 수 있습니다.
- GitHub 업로드 시 개인 데이터가 포함된 `data/` 폴더는 제외해야 합니다.

<a id="roadmap"></a>
## 현재 범위와 후속 과제

### 현재 대회 출품 범위

- Windows 로컬 데스크톱 애플리케이션
- 사용자 정면에 위치한 단일 웹캠
- MediaPipe 기반 자세 랜드마크 추출
- 개인 기준 대비 자세 변화 감지
- 화면·소리 알림, JSON 기록, 세션 리포트

### 후속 과제

- 측면 또는 비정면 카메라 각도를 고려한 분석 고도화
- 사용자별 나쁜 자세 범위를 사전에 측정하는 추가 캘리브레이션
- SQLite 기반 기록 저장과 데이터 마이그레이션
- EXE 및 설치 프로그램 형태의 배포
- Windows 로그인 시 자동 시작 옵션
- 같은 자세 유지 및 연속 작업에 대한 휴식 알림 로직 완성
- 다양한 체형·조명·카메라 환경에서의 임계값 검증

<a id="troubleshooting"></a>
## 문제 해결

### 카메라 화면이 보이지 않을 때

1. 다른 카메라 앱, 화상회의 프로그램, 브라우저에서 카메라를 사용 중인지 확인합니다.
2. `설정 > 사용할 카메라`에서 실제 카메라 장치를 선택합니다.
3. `카메라 목록 새로고침`을 누른 뒤 설정을 저장합니다.
4. Windows의 카메라 개인정보 보호 설정에서 데스크톱 앱 접근을 허용합니다.

### `pose_landmarker_lite.task` 오류가 발생할 때

모델 파일이 `main.py`와 같은 폴더에 있는지 확인합니다.

```text
CamPose-main/
├─ main.py
└─ pose_landmarker_lite.task
```

### OpenCV 설치 중 `WinError 5`가 발생할 때

실행 중인 CamPose, Jupyter Notebook, Python 터미널 등 카메라 또는 `cv2`를 사용하는 프로세스를 모두 종료한 뒤 새 터미널에서 다시 설치합니다.

```powershell
conda activate campose
python -m pip install -r requirements.txt
```

### 터미널의 `python` 명령을 찾지 못할 때

Conda 환경을 다시 활성화하고 Python 경로를 확인합니다.

```powershell
conda activate campose
where.exe python
python --version
```

<a id="open-source"></a>
## 오픈소스 및 출처

- [Google AI Edge - MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)
- [MediaPipe GitHub](https://github.com/google-ai-edge/mediapipe)
- [MediaPipe Apache 2.0 License](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)
- [MediaPipe Pose Landmarker Lite 모델](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [OpenCV](https://opencv.org/)

공개 저장소로 배포할 때는 프로젝트 소스 코드에 적용할 `LICENSE` 파일을 별도로 추가하는 것을 권장합니다.

---

**CamPose - 바른 자세를 강요하기보다, 사용자가 자신의 자세 변화를 알아차릴 수 있도록 돕습니다.**
