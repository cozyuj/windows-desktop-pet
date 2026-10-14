# -*- coding: utf-8 -*-
"""
Desktop Pet - 바탕화면에 떠 있는 감성/유머 데스크톱 펫

기능
  - 투명 배경 + 항상 위 창에 이미지(PNG/GIF/JPG/WEBP) 표시, 애니메이션 GIF 지원
  - 마우스 왼쪽 드래그로 위치 이동
  - 우클릭 메뉴: 이미지 불러오기 / 크기 조절 / 위치 조정 / 마우스 따라다니기 /
                 좌우 반전 / 둥실둥실 / 항상 위 / 한마디 하기 / 종료
  - 왼쪽 클릭(드래그 없이)하면 랜덤 한마디 말풍선
  - 마지막 설정(이미지 경로, 위치, 크기, 옵션)을 저장해서 다음 실행 때 복원
"""

import json
import math
import os
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageOps, ImageSequence, ImageTk
except ImportError:  # pragma: no cover
    tk.Tk().withdraw()
    messagebox.showerror("Desktop Pet", "Pillow 가 필요합니다.\n\npip install pillow")
    sys.exit(1)

APP_NAME = "DesktopPet"
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# 윈도우 투명 처리용 키 컬러 (이미지에 거의 쓰이지 않는 색)
KEY_COLOR = "#ff00fe"
BOB_MARGIN = 12          # 둥실둥실 효과를 위한 캔버스 여유 공간(px)
FOLLOW_STOP_DIST = 70    # 마우스에서 이 거리 안이면 따라가기 멈춤(px)
FOLLOW_FPS_MS = 16       # 따라다니기 틱 간격

DEFAULT_QUOTES = [
    "오늘도 수고했어요. 진짜로.",
    "커피 한 잔 어때요? 저는 못 마시지만.",
    "버그는 기능이다. (아님)",
    "잠깐 스트레칭 한 번만요.",
    "모니터 너무 가까워요. 조금만 뒤로.",
    "퇴근까지 얼마 안 남았어요. 아마도.",
    "물 마실 시간이에요.",
    "그거 저장했어요? Ctrl+S.",
    "오늘 하늘 봤어요? 한 번 보고 와요.",
    "힘들면 쉬어도 돼요. 제가 지켜볼게요.",
    "회의는 메일로 끝낼 수 있었다.",
    "깃 푸시 전에 한 번만 더 확인!",
    "당신 생각보다 잘하고 있어요.",
    "월요일은 원래 그런 날이에요.",
    "저 좀 옮겨 주세요. 여기 햇빛이 세요.",
]


def resource_path(rel: str) -> str:
    """PyInstaller onefile 환경과 일반 실행 환경 모두에서 리소스 경로를 돌려준다."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def exe_dir() -> str:
    """exe(또는 스크립트)가 놓인 폴더. quotes.txt 같은 사용자 파일을 찾는 기준."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path() -> str:
    if IS_WINDOWS:
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.config")
    folder = os.path.join(base, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")


def load_quotes() -> list:
    """exe 옆에 quotes.txt 가 있으면 그 내용을, 없으면 기본 문구를 쓴다."""
    path = os.path.join(exe_dir(), "quotes.txt")
    try:
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        if lines:
            return lines
    except OSError:
        pass
    return DEFAULT_QUOTES


class DesktopPet(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.overrideredirect(True)   # 타이틀바/테두리 제거
        self.wm_attributes("-topmost", True)
        self._setup_transparency()

        # 상태
        self.frames_src = []          # 원본 PIL 프레임 목록
        self.durations = []           # 프레임별 지연(ms)
        self.frames_tk = []           # 현재 크기/반전 상태의 PhotoImage 목록
        self._scaled_cache = []       # 리사이즈된 PIL 프레임 캐시
        self._scaled_cache_key = None
        self.frame_idx = 0
        self._anim_job = None
        self.image_path = None
        self.scale = 1.0
        self.x = 0.0
        self.y = 0.0
        self.img_w = 0
        self.img_h = 0

        self.follow_var = tk.BooleanVar(value=False)
        self.flip_var = tk.BooleanVar(value=False)
        self.bob_var = tk.BooleanVar(value=True)
        self.topmost_var = tk.BooleanVar(value=True)
        self.talk_var = tk.BooleanVar(value=True)    # 클릭하면 한마디
        self._bob_phase = 0.0
        self._bob_job = None
        self._follow_job = None

        self._drag_start = None
        self._drag_moved = False
        self._bubble = None
        self._bubble_job = None
        self.quotes = load_quotes()

        # 캔버스
        self.canvas = tk.Canvas(self, bg=self._bg_color(), highlightthickness=0, bd=0)
        self.canvas.pack()
        self.canvas_img = None

        self._build_menu()
        self._bind_events()

        # 설정 복원 -> 이미지 로드 -> 배치
        cfg = self._load_config()
        self.scale = float(cfg.get("scale", 1.0))
        self.flip_var.set(bool(cfg.get("flip", False)))
        self.bob_var.set(bool(cfg.get("bob", True)))
        self.follow_var.set(bool(cfg.get("follow", False)))
        self.topmost_var.set(bool(cfg.get("topmost", True)))
        self.talk_var.set(bool(cfg.get("talk", True)))
        self.wm_attributes("-topmost", self.topmost_var.get())

        img = cfg.get("image")
        if not (img and os.path.isfile(img) and self._load_image(img)):
            self._load_image(resource_path(os.path.join("assets", "pet.png")))

        if "x" in cfg and "y" in cfg:
            self.x, self.y = float(cfg["x"]), float(cfg["y"])
            self._clamp_to_screen()
        else:
            self._move_to_corner()
        self._place()

        if self.bob_var.get():
            self._start_bob()
        if self.follow_var.get():
            self._start_follow()

        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    # ------------------------------------------------------------------ 투명 처리
    def _setup_transparency(self):
        if IS_WINDOWS:
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
            self.configure(bg=KEY_COLOR)
            self.wm_attributes("-transparentcolor", KEY_COLOR)
        elif IS_MAC:
            self.wm_attributes("-transparent", True)
            self.configure(bg="systemTransparent")
        else:
            self.configure(bg=KEY_COLOR)

    def _bg_color(self) -> str:
        return "systemTransparent" if IS_MAC else KEY_COLOR

    # ------------------------------------------------------------------ 메뉴
    def _build_menu(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="이미지 불러오기...", command=self.choose_image)

        size_menu = tk.Menu(m, tearoff=0)
        for label, s in (("50%", 0.5), ("75%", 0.75), ("100%", 1.0),
                         ("150%", 1.5), ("200%", 2.0), ("300%", 3.0)):
            size_menu.add_command(label=label, command=lambda s=s: self.set_scale(s))
        size_menu.add_separator()
        size_menu.add_command(label="조금 크게 (+)", command=lambda: self.set_scale(self.scale * 1.15))
        size_menu.add_command(label="조금 작게 (-)", command=lambda: self.set_scale(self.scale / 1.15))
        m.add_cascade(label="크기", menu=size_menu)

        pos_menu = tk.Menu(m, tearoff=0)
        pos_menu.add_command(label="오른쪽 아래", command=lambda: self._move_to_corner("br"))
        pos_menu.add_command(label="왼쪽 아래", command=lambda: self._move_to_corner("bl"))
        pos_menu.add_command(label="오른쪽 위", command=lambda: self._move_to_corner("tr"))
        pos_menu.add_command(label="왼쪽 위", command=lambda: self._move_to_corner("tl"))
        pos_menu.add_command(label="화면 중앙", command=lambda: self._move_to_corner("c"))
        pos_menu.add_separator()
        pos_menu.add_command(label="좌표 직접 입력...", command=self.ask_position)
        m.add_cascade(label="위치 조정", menu=pos_menu)

        m.add_separator()
        m.add_checkbutton(label="마우스 따라다니기", variable=self.follow_var, command=self.toggle_follow)
        m.add_checkbutton(label="좌우 반전", variable=self.flip_var, command=self._rebuild_frames)
        m.add_checkbutton(label="둥실둥실 효과", variable=self.bob_var, command=self.toggle_bob)
        m.add_checkbutton(label="항상 위에 표시", variable=self.topmost_var, command=self.toggle_topmost)
        m.add_checkbutton(label="클릭하면 한마디", variable=self.talk_var, command=self._save_config)
        m.add_separator()
        m.add_command(label="종료", command=self.quit_app)
        self.menu = m

    def _bind_events(self):
        c = self.canvas
        c.bind("<ButtonPress-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)
        right = "<Button-2>" if IS_MAC else "<Button-3>"
        c.bind(right, self._on_right_click)
        if IS_MAC:
            c.bind("<Control-Button-1>", self._on_right_click)
        c.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Escape>", lambda e: self.quit_app())

    # ------------------------------------------------------------------ 이미지
    def _load_image(self, path: str) -> bool:
        try:
            im = Image.open(path)
        except Exception as e:
            messagebox.showerror("Desktop Pet", f"이미지를 열 수 없습니다.\n{path}\n\n{e}")
            return False

        frames, durations = [], []
        try:
            for fr in ImageSequence.Iterator(im):
                frames.append(fr.convert("RGBA"))
                durations.append(int(fr.info.get("duration", 100)) or 100)
        except Exception:
            frames, durations = [im.convert("RGBA")], [100]
        if not frames:
            return False

        self.frames_src = frames
        self.durations = durations
        self.image_path = path
        self._rebuild_frames()
        return True

    def _scaled_frames(self, sw: int, sh: int) -> list:
        """현재 크기로 리사이즈한 PIL 프레임. 크기가 같으면 캐시를 재사용한다 (반전 전환이 가벼워짐)."""
        key = (id(self.frames_src), sw, sh)
        if self._scaled_cache_key != key:
            self._scaled_cache = [fr.resize((sw, sh), Image.Resampling.LANCZOS) for fr in self.frames_src]
            self._scaled_cache_key = key
        return self._scaled_cache

    def _rebuild_frames(self, save: bool = True):
        """현재 scale / flip 상태로 PhotoImage 목록을 다시 만든다."""
        if not self.frames_src:
            return
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None

        sw = max(1, int(self.frames_src[0].width * self.scale))
        sh = max(1, int(self.frames_src[0].height * self.scale))
        # 윈도우 키컬러 투명은 1비트라서, 반투명 픽셀은 키컬러 위에 합성해 테두리 번짐을 줄인다
        bg_rgb = None if IS_MAC else tuple(int(KEY_COLOR[i:i + 2], 16) for i in (1, 3, 5))

        new = []
        for f in self._scaled_frames(sw, sh):
            if self.flip_var.get():
                f = ImageOps.mirror(f)
            if bg_rgb is not None:
                base = Image.new("RGBA", f.size, bg_rgb + (255,))
                base.alpha_composite(f)
                f = base
            new.append(ImageTk.PhotoImage(f))
        self.frames_tk = new
        self.img_w, self.img_h = sw, sh
        self.frame_idx = 0

        self.canvas.config(width=sw, height=sh + BOB_MARGIN)
        if self.canvas_img is None:
            self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.frames_tk[0])
        else:
            self.canvas.itemconfig(self.canvas_img, image=self.frames_tk[0])
        self._clamp_to_screen()
        self._place()
        if len(self.frames_tk) > 1:
            self._anim_job = self.after(self.durations[0], self._next_frame)
        if save:
            self._save_config()

    def _next_frame(self):
        if not self.frames_tk:
            return
        self.frame_idx = (self.frame_idx + 1) % len(self.frames_tk)
        self.canvas.itemconfig(self.canvas_img, image=self.frames_tk[self.frame_idx])
        self._anim_job = self.after(self.durations[self.frame_idx], self._next_frame)

    def choose_image(self):
        # 우클릭 메뉴가 완전히 닫힌 뒤에 대화상자를 열어야 앞에 뜬다
        self.after(120, self._open_file_dialog)

    def _bring_to_front(self):
        """맥에서는 우리 프로세스가 앞에 있지 않으면 파일 창이 다른 앱 뒤에 숨는다."""
        if IS_MAC:
            try:
                import subprocess
                subprocess.run(["osascript", "-e",
                                'tell application "System Events" to set frontmost of '
                                f'(first process whose unix id is {os.getpid()}) to true'],
                               timeout=3, capture_output=True)
            except Exception:
                pass
        self.lift()
        self.update()

    def _open_file_dialog(self):
        self._bring_to_front()
        self.wm_attributes("-topmost", False)
        try:
            path = filedialog.askopenfilename(
                parent=self,
                title="펫 이미지 선택",
                filetypes=[("이미지", "*.png *.gif *.jpg *.jpeg *.webp *.bmp"), ("모든 파일", "*.*")],
            )
        finally:
            self.wm_attributes("-topmost", self.topmost_var.get())
        if path and self._load_image(path):
            self._save_config()

    def set_scale(self, s: float):
        self.scale = max(0.1, min(8.0, s))
        self._rebuild_frames()

    def _on_wheel(self, e):
        # Ctrl + 휠로 크기 조절
        if e.state & 0x4:
            delta = e.delta if IS_MAC else e.delta / 120
            self.set_scale(self.scale * (1.08 if delta > 0 else 1 / 1.08))

    # ------------------------------------------------------------------ 위치
    def _screen_size(self):
        return self.winfo_screenwidth(), self.winfo_screenheight()

    def _win_size(self):
        return self.img_w or 100, (self.img_h or 100) + BOB_MARGIN

    def _place(self):
        self.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _clamp_to_screen(self):
        sw, sh = self._screen_size()
        w, h = self._win_size()
        self.x = max(-w * 0.5, min(self.x, sw - w * 0.5))
        self.y = max(-h * 0.5, min(self.y, sh - h * 0.5))

    def _move_to_corner(self, where: str = "br", margin: int = 20):
        sw, sh = self._screen_size()
        w, h = self._win_size()
        taskbar = 48 if IS_WINDOWS else 0
        pos = {
            "br": (sw - w - margin, sh - h - margin - taskbar),
            "bl": (margin, sh - h - margin - taskbar),
            "tr": (sw - w - margin, margin),
            "tl": (margin, margin),
            "c": ((sw - w) // 2, (sh - h) // 2),
        }
        self.x, self.y = pos.get(where, pos["br"])
        self._place()
        self._save_config()

    def ask_position(self):
        self.after(120, self._ask_position_dialog)

    def _ask_position_dialog(self):
        from tkinter import simpledialog
        self._bring_to_front()
        sw, sh = self._screen_size()
        x = simpledialog.askinteger("위치 조정", f"X 좌표 (0 ~ {sw})", initialvalue=int(self.x), parent=self)
        if x is None:
            return
        y = simpledialog.askinteger("위치 조정", f"Y 좌표 (0 ~ {sh})", initialvalue=int(self.y), parent=self)
        if y is None:
            return
        self.x, self.y = float(x), float(y)
        self._clamp_to_screen()
        self._place()
        self._save_config()

    # ------------------------------------------------------------------ 드래그
    def _on_press(self, e):
        self._drag_start = (e.x_root, e.y_root, self.x, self.y)
        self._drag_moved = False

    def _on_drag(self, e):
        if not self._drag_start:
            return
        sx, sy, ox, oy = self._drag_start
        dx, dy = e.x_root - sx, e.y_root - sy
        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_moved = True
        self.x, self.y = ox + dx, oy + dy
        self._place()
        self._move_bubble()

    def _on_release(self, e):
        if self._drag_start and not self._drag_moved and self.talk_var.get():
            self.say_something()
        self._drag_start = None
        if self._drag_moved:
            self._save_config()

    def _on_right_click(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    # ------------------------------------------------------------------ 따라다니기
    def toggle_follow(self):
        if self.follow_var.get():
            self._start_follow()
        else:
            self._stop_follow()
        self._save_config()

    def _start_follow(self):
        if self._follow_job is None:
            self._follow_tick()

    def _stop_follow(self):
        if self._follow_job:
            self.after_cancel(self._follow_job)
            self._follow_job = None

    def _follow_tick(self):
        if not self.follow_var.get():
            self._follow_job = None
            return
        if self._drag_start is None:   # 드래그 중엔 따라가지 않음
            px, py = self.winfo_pointerxy()
            w, h = self._win_size()
            cx, cy = self.x + w / 2, self.y + h / 2
            dx, dy = px - cx, py - cy
            dist = math.hypot(dx, dy)
            if dist > FOLLOW_STOP_DIST:
                # 멀수록 빠르게, 가까우면 천천히 (부드러운 추적)
                step = min(dist - FOLLOW_STOP_DIST, max(2.0, dist * 0.08))
                self.x += dx / dist * step
                self.y += dy / dist * step
                self._clamp_to_screen()
                self._place()
                self._move_bubble()
                # 이동 방향으로 얼굴 돌리기
                if abs(dx) > 8:
                    want_flip = dx < 0
                    if want_flip != self.flip_var.get():
                        self.flip_var.set(want_flip)
                        self._rebuild_frames(save=False)
        self._follow_job = self.after(FOLLOW_FPS_MS, self._follow_tick)

    # ------------------------------------------------------------------ 둥실둥실
    def toggle_bob(self):
        if self.bob_var.get():
            self._start_bob()
        else:
            if self._bob_job:
                self.after_cancel(self._bob_job)
                self._bob_job = None
            if self.canvas_img is not None:
                self.canvas.coords(self.canvas_img, 0, 0)
        self._save_config()

    def _start_bob(self):
        if self._bob_job is None:
            self._bob_tick()

    def _bob_tick(self):
        if not self.bob_var.get():
            self._bob_job = None
            return
        self._bob_phase += 0.06
        off = (math.sin(self._bob_phase) + 1) / 2 * (BOB_MARGIN - 2)
        if self.canvas_img is not None:
            self.canvas.coords(self.canvas_img, 0, int(off))
        self._bob_job = self.after(33, self._bob_tick)

    # ------------------------------------------------------------------ 기타
    def toggle_topmost(self):
        self.wm_attributes("-topmost", self.topmost_var.get())
        self._save_config()

    def say_something(self):
        text = random.choice(self.quotes)
        self._show_bubble(text)

    def _show_bubble(self, text: str, ms: int = 3500):
        """상자 없이 텍스트만 띄운다. 어떤 배경에서도 읽히도록 어두운 외곽선을 깐다."""
        self._hide_bubble()
        b = tk.Toplevel(self)
        b.overrideredirect(True)
        b.wm_attributes("-topmost", True)
        if IS_MAC:
            b.wm_attributes("-transparent", True)
            b.configure(bg="systemTransparent")
        else:
            b.configure(bg=KEY_COLOR)
            b.wm_attributes("-transparentcolor", KEY_COLOR)

        font = ("Malgun Gothic", 13, "bold") if IS_WINDOWS else ("Apple SD Gothic Neo", 15, "bold")
        c = tk.Canvas(b, bg=self._bg_color(), highlightthickness=0, bd=0)
        c.pack()
        pad = 6
        # 외곽선: 어두운 글자를 8방향으로 깔고, 그 위에 밝은 글자
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):
            c.create_text(pad + dx, pad + dy, text=text, anchor="nw", font=font,
                          fill="#222222", width=280)
        c.create_text(pad, pad, text=text, anchor="nw", font=font, fill="#ffffff", width=280)
        x0, y0, x1, y1 = c.bbox("all")
        c.config(width=x1 - x0 + pad * 2, height=y1 - y0 + pad * 2)
        c.move("all", pad - x0, pad - y0)

        self._bubble = b
        self._move_bubble()
        self._bubble_job = self.after(ms, self._hide_bubble)

    def _move_bubble(self):
        if not self._bubble:
            return
        self._bubble.update_idletasks()
        bw, bh = self._bubble.winfo_reqwidth(), self._bubble.winfo_reqheight()
        w, _ = self._win_size()
        sw, _ = self._screen_size()
        bx = int(self.x + w / 2 - bw / 2)
        by = int(self.y - bh - 2)
        bx = max(0, min(bx, sw - bw))
        if by < 0:
            by = int(self.y + self._win_size()[1] + 2)
        self._bubble.geometry(f"+{bx}+{by}")

    def _hide_bubble(self):
        if self._bubble_job:
            self.after_cancel(self._bubble_job)
            self._bubble_job = None
        if self._bubble:
            self._bubble.destroy()
            self._bubble = None

    # ------------------------------------------------------------------ 설정
    def _load_config(self) -> dict:
        try:
            with open(config_path(), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        data = {
            "image": self.image_path if (self.image_path and not self.image_path.startswith(
                getattr(sys, "_MEIPASS", "\0"))) else None,
            "x": int(self.x), "y": int(self.y),
            "scale": self.scale,
            "flip": self.flip_var.get(),
            "bob": self.bob_var.get(),
            "follow": self.follow_var.get(),
            "topmost": self.topmost_var.get(),
            "talk": self.talk_var.get(),
        }
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def quit_app(self):
        self._save_config()
        self._hide_bubble()
        self.destroy()


def main():
    app = DesktopPet()
    app.mainloop()


if __name__ == "__main__":
    main()
