"""
웹 앱 공통 CSS
다크 모드 + 초록 포인트 색상 테마
"""

WEB_CSS = """
<style>
  body { background: #1a1a2e !important; font-family: 'Malgun Gothic', '맑은 고딕', sans-serif; }
  .sidebar { background: #16213e !important; min-width: 200px; max-width: 200px; }
  .card { background: #0f3460 !important; border-radius: 12px; padding: 16px; }
  .preview-box {
    background: #0d0d0d; border-radius: 12px;
    aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center;
    color: #a0a0a0; min-height: 200px;
  }
  .stat-card { background: #0f3460; border-radius: 12px; padding: 16px; text-align: center; }
  .text-accent { color: #00b894 !important; }
  .text-dim { color: #a0a0a0 !important; }
  .text-danger { color: #e74c3c !important; }
  .text-warning { color: #f39c12 !important; }
  .text-success { color: #00b894 !important; }
  .page-title { font-size: 1.25rem; font-weight: bold; color: #eaeaea; }
  .posture-label { font-size: 2rem; font-weight: bold; }
  .timer-label { font-size: 1.5rem; font-weight: bold; }
  .menu-btn-active { background: #00b894 !important; color: white !important; }
  .menu-btn { color: #eaeaea !important; justify-content: flex-start !important; }
  .history-card { background: #0f3460; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; }
  .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
</style>
"""
