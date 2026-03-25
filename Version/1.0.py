import tkinter as tk
from tkinter import messagebox, ttk
import caldav
from datetime import datetime, timedelta
from icalendar import Calendar
import calendar
import holidays

# --- CalDAV 설정 정보 (여기에 본인 정보를 입력하세요) ---
CALDAV_URL = ""
USERNAME = ""
PASSWORD = ""

# --- 고급 색상 테마 ---
THEMES = {
    "light": {
        "BG_COLOR": "#FDFDFD",       # 아주 밝은 배경
        "CELL_BG": "#FFFFFF",
        "TEXT_COLOR": "#2D3748",     # 부드러운 진회색
        "HEADER_BG": "#F7FAFC",      # 약간의 푸른빛 도는 회색
        "GRID_COLOR": "#EDF2F7",     # 연한 격자선
        "TODAY_BG": "#EBF8FF",       # 부드러운 강조 배경
        "TODAY_TEXT": "#2B6CB0",
        "EVENT_BG": "#E6FFFA",       # 민트 계열 파스텔
        "EVENT_TEXT": "#2C7A7B",
        "SAT_TEXT": "#3182CE",
        "SUN_TEXT": "#c80003",
        "BTN_BG": "#FFFFFF",
        "BTN_HOVER": "#EDF2F7",
        "TOGGLE_BTN_BG": "#4A5568",  # 세련된 진회색 바탕
        "TOGGLE_BTN_FG": "#FFFFFF"
    },
    "dark": {
        "BG_COLOR": "#000000",       # 세련된 완전 검정
        "CELL_BG": "#111111",        # 약간 밝은 검정
        "TEXT_COLOR": "#F7FAFC",
        "HEADER_BG": "#0A0A0A",
        "GRID_COLOR": "#333333",
        "TODAY_BG": "#1A365D",       # 깊은 파란색
        "TODAY_TEXT": "#BEE3F8",
        "EVENT_BG": "#1D4044",       # 어두운 민트
        "EVENT_TEXT": "#B2F5EA",
        "SAT_TEXT": "#63B3ED",
        "SUN_TEXT": "#c80003",
        "BTN_BG": "#222222",
        "BTN_HOVER": "#333333",
        "TOGGLE_BTN_BG": "#4A5568",
        "TOGGLE_BTN_FG": "#FFFFFF"
    }
}

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minjae's Premium Calendar")
        self.root.geometry("1150x850")
        
        # 화면 중앙에 배치
        window_width = 1150
        window_height = 850
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
        
        # 폰트 설정 (시스템 기본 제공 깔끔한 폰트들)
        self.font_main = ("Malgun Gothic", 11)
        self.font_bold = ("Malgun Gothic", 11, "bold")
        self.font_title = ("Malgun Gothic", 22, "bold")
        self.font_event = ("Malgun Gothic", 9)
        self.font_holiday = ("Malgun Gothic", 9, "bold")
        
        self.current_theme = "light"
        self.colors = THEMES[self.current_theme]
        self.root.configure(bg=self.colors["BG_COLOR"])

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.events_dict = {}

        calendar.setfirstweekday(calendar.SUNDAY)

        self.setup_ui()
        self.load_events()
        self.set_os_theme()

    def set_os_theme(self):
        try:
            import ctypes
            self.root.update()
            HWND = ctypes.windll.user32.GetParent(self.root.winfo_id())
            
            # 다크/라이트 모드 설정 (19, 20번 속성)
            is_dark = 1 if self.current_theme == "dark" else 0
            val = ctypes.c_int(is_dark)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND, 20, ctypes.byref(val), ctypes.sizeof(val))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND, 19, ctypes.byref(val), ctypes.sizeof(val))
            
            # 애니메이션 사용 중지 (DWMWA_TRANSITIONS_FORCEDISABLED = 3)
            # 천천히 바뀌는 효과를 즉시 바뀌게 강제함
            disable_transition = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND, 3, ctypes.byref(disable_transition), ctypes.sizeof(disable_transition))
        except Exception:
            pass

    def get_color(self, key):
        return self.colors[key]

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.colors = THEMES[self.current_theme]
        self.root.configure(bg=self.get_color("BG_COLOR"))
        
        # main_frame만 파괴하고 재생성하도록 변경 (root 전체 파괴 방지)
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
            
        self.setup_ui()
        self.update_calendar_ui()
        self.set_os_theme()

    def setup_ui(self):
        # 최외곽 메인 프레임 (여백 축소)
        self.main_frame = tk.Frame(self.root, bg=self.get_color("BG_COLOR"), padx=25, pady=0)
        self.main_frame.pack(expand=True, fill="both", pady=25)

        nav_frame = tk.Frame(self.main_frame, bg=self.get_color("BG_COLOR"))
        nav_frame.pack(fill="x", pady=(0, 10))

        center_nav = tk.Frame(nav_frame, bg=self.get_color("BG_COLOR"))
        center_nav.pack(anchor="center")

        def create_hover_button(parent, text, command, bg_key, fg_key, hover_key):
            bg = self.get_color(bg_key)
            hover_bg = self.get_color(hover_key)
            btn = tk.Button(parent, text=text, command=command, bg=bg, fg=self.get_color(fg_key), 
                            font=self.font_bold, relief="flat", padx=20, pady=10, cursor="hand2", bd=0)
            btn.bind("<Enter>", lambda e, b=btn, hb=hover_bg: b.config(bg=hb))
            btn.bind("<Leave>", lambda e, b=btn, cbg=bg: b.config(bg=cbg))
            return btn

        # 테마 토글 버튼 스타일링을 화살표 버튼과 동일하게 변경
        theme_text = "Dark" if self.current_theme == "light" else "Light"
        self.theme_btn = create_hover_button(nav_frame, theme_text, self.toggle_theme, "BTN_BG", "TEXT_COLOR", "BTN_HOVER")
        self.theme_btn.place(relx=0, rely=0.5, anchor="w")

        self.prev_btn = create_hover_button(center_nav, "◀", self.prev_month, "BTN_BG", "TEXT_COLOR", "BTN_HOVER")
        self.prev_btn.pack(side="left", padx=15)

        self.month_year_label = tk.Label(center_nav, text="", font=self.font_title, 
                                         bg=self.get_color("BG_COLOR"), fg=self.get_color("TEXT_COLOR"), width=12)
        self.month_year_label.pack(side="left")

        self.next_btn = create_hover_button(center_nav, "▶", self.next_month, "BTN_BG", "TEXT_COLOR", "BTN_HOVER")
        self.next_btn.pack(side="left", padx=15)

        # 우측 새로고침 버튼도 화살표 버튼과 동일하게 변경
        refresh_btn = create_hover_button(nav_frame, "새로고침", self.load_events, "BTN_BG", "TEXT_COLOR", "BTN_HOVER")
        refresh_btn.place(relx=1.0, rely=0.5, anchor="e")

        # 캘린더 테두리를 얇고 세련되게 처리
        cal_container = tk.Frame(self.main_frame, bg=self.get_color("GRID_COLOR"), bd=1)
        cal_container.pack(expand=True, fill="both")
        
        inner_cal = tk.Frame(cal_container, bg=self.get_color("BG_COLOR"))
        inner_cal.pack(expand=True, fill="both", padx=1, pady=1)

        # 요일 헤더 여백 확보
        days_frame = tk.Frame(inner_cal, bg=self.get_color("HEADER_BG"))
        days_frame.pack(fill="x")
        days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        day_colors = [self.get_color("SUN_TEXT")] + [self.get_color("TEXT_COLOR")]*5 + [self.get_color("SAT_TEXT")]

        for i, day in enumerate(days):
            lbl = tk.Label(days_frame, text=day, font=self.font_bold, 
                           bg=self.get_color("HEADER_BG"), fg=day_colors[i], pady=8)
            lbl.grid(row=0, column=i, sticky="nsew")
            days_frame.grid_columnconfigure(i, weight=1)

        self.cal_frame = tk.Frame(inner_cal, bg=self.get_color("GRID_COLOR"))
        self.cal_frame.pack(expand=True, fill="both")
        for i in range(7):
            self.cal_frame.grid_columnconfigure(i, weight=1, uniform="cell")

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar_ui()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar_ui()

    def update_calendar_ui(self):
        self.month_year_label.config(text=f"{self.current_year}년 {self.current_month}월")

        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        now = datetime.now()
        
        # 한국 공휴일 가져오기 (해당 연도)
        kr_holidays = holidays.KR(years=self.current_year)
        
        # 월별 주차(week) 수에 맞춰 빈 행 공간 제거
        for i in range(6):
            if i < len(cal):
                self.cal_frame.grid_rowconfigure(i, weight=1, uniform="cell")
            else:
                # 사용하지 않는 주차는 공간을 차지하지 않도록 초기화
                self.cal_frame.grid_rowconfigure(i, weight=0, uniform="")

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                cell_bg = self.get_color("CELL_BG")
                if day != 0:
                    is_today = (self.current_year == now.year and self.current_month == now.month and day == now.day)
                    if is_today:
                        cell_bg = self.get_color("TODAY_BG")

                day_frame = tk.Frame(self.cal_frame, bg=cell_bg)
                day_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

                if day != 0:
                    day_color = self.get_color("TEXT_COLOR")
                    if col == 0: day_color = self.get_color("SUN_TEXT")
                    if col == 6: day_color = self.get_color("SAT_TEXT")
                    
                    font_type = self.font_bold if is_today else self.font_main
                    if is_today:
                        day_color = self.get_color("TODAY_TEXT")

                    day_lbl = tk.Label(day_frame, text=str(day), font=font_type, 
                                       bg=cell_bg, fg=day_color, anchor="ne")
                    day_lbl.pack(fill="x", padx=12, pady=10)

                    date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    current_date = datetime(self.current_year, self.current_month, day).date()
                    
                    # 1. 공휴일 표시 (최우선)
                    holiday_name = kr_holidays.get(current_date)
                    if holiday_name:
                        # 일요일/토요일과 겹쳐도 공휴일 텍스트 색상을 빨간색으로 강제
                        day_lbl.config(fg=self.get_color("SUN_TEXT")) 
                        hol_lbl = tk.Label(day_frame, text=holiday_name, font=self.font_holiday, 
                                           bg="#c80003", # 요청하신 완전한 빨강색
                                           fg="white", anchor="center", padx=4, pady=2, relief="flat")
                        hol_lbl.pack(fill="x", padx=4, pady=1)

                    # 2. 개인 일정 표시
                    if date_str in self.events_dict:
                        events = self.events_dict[date_str]
                        for idx, event in enumerate(events):
                            if idx < 4:
                                ev_lbl = tk.Label(day_frame, text=f"{event}", font=self.font_event, 
                                                bg=self.get_color("EVENT_BG"), fg=self.get_color("EVENT_TEXT"), 
                                                anchor="center", padx=4, pady=2, relief="flat")
                                ev_lbl.pack(fill="x", padx=4, pady=1)
                        if len(events) > 4:
                            more_lbl = tk.Label(day_frame, text=f"+ {len(events)-4} more", 
                                                font=self.font_event, 
                                                bg=cell_bg, fg="#A0AEC0", anchor="center")
                            more_lbl.pack(fill="x", padx=4, pady=1)

    def load_events(self):
        self.events_dict = {}
        try:
            client = caldav.DAVClient(url=CALDAV_URL, username=USERNAME, password=PASSWORD)
            principal = client.principal()
            calendars = principal.calendars()

            if not calendars:
                messagebox.showinfo("알림", "연결된 캘린더가 없습니다.")
                return

            # 가능한 모든 일정을 가져오기 위한 매우 넓은 날짜 범위 설정
            # (윈도우 환경 OSError 및 tzlocal 의존성 방지를 위해 1970년 대신 2000년부터 시작)
            start_date = datetime(2000, 1, 1)
            end_date = datetime(2100, 1, 1)

            for calendar_obj in calendars:
                if hasattr(calendar_obj, 'search'):
                    results = calendar_obj.search(event=True, start=start_date, end=end_date)
                else:
                    results = calendar_obj.date_search(start=start_date, end=end_date)
                
                for event in results:
                    ical_data = Calendar.from_ical(event.data)
                    for component in ical_data.walk():
                        if component.name == "VEVENT" and component.get('dtstart'):
                            summary = str(component.get('summary'))
                            dtstart = component.get('dtstart').dt
                            
                            try:
                                date_str = dtstart.strftime("%Y-%m-%d")
                                if date_str not in self.events_dict:
                                    self.events_dict[date_str] = []
                                self.events_dict[date_str].append(summary)
                            except Exception:
                                pass 

            self.update_calendar_ui()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("오류", f"일정을 불러오는 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()
