"""
공통 색상, 폰트, 레이아웃 상수
프로그램 전체에서 동일한 디자인을 유지하기 위해 한곳에서 관리합니다.
"""

# ── 창 크기 ──────────────────────────────────────────
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 650
SIDEBAR_WIDTH = 200

# ── 색상 (다크 모드 + 초록 포인트) ───────────────────
COLOR_BG = "#1a1a2e"           # 메인 배경
COLOR_SIDEBAR = "#16213e"      # 사이드바 배경
COLOR_CARD = "#0f3460"         # 카드 배경
COLOR_CARD_HOVER = "#1a4a7a"   # 카드 호버
COLOR_ACCENT = "#00b894"       # 주요 포인트 (초록)
COLOR_ACCENT_HOVER = "#00a383" # 포인트 호버
COLOR_TEXT = "#eaeaea"         # 기본 텍스트
COLOR_TEXT_DIM = "#a0a0a0"     # 보조 텍스트
COLOR_DANGER = "#e74c3c"       # 경고/위험
COLOR_WARNING = "#f39c12"      # 주의
COLOR_SUCCESS = "#00b894"      # 좋은 상태
COLOR_PREVIEW_BG = "#0d0d0d"   # 카메라 미리보기 배경

# ── 자세 상태별 색상 ─────────────────────────────────
POSTURE_COLORS = {
    "좋은 자세": COLOR_SUCCESS,
    "자세 주의": COLOR_WARNING,
    "나쁜 자세": COLOR_DANGER,
    "사람 미감지": COLOR_TEXT_DIM,
}

# ── 폰트 ─────────────────────────────────────────────
FONT_TITLE = ("맑은 고딕", 20, "bold")
FONT_HEADING = ("맑은 고딕", 16, "bold")
FONT_BODY = ("맑은 고딕", 13)
FONT_BODY_BOLD = ("맑은 고딕", 13, "bold")
FONT_SMALL = ("맑은 고딕", 11)
FONT_BUTTON = ("맑은 고딕", 13, "bold")
FONT_SIDEBAR = ("맑은 고딕", 14)
FONT_TIMER = ("맑은 고딕", 28, "bold")

# ── 공통 여백 ────────────────────────────────────────
PAD_X = 16
PAD_Y = 12
CARD_CORNER = 12
