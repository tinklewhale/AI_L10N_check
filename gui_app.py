"""
AI 번역 검수 도구 - GUI 애플리케이션
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import pandas as pd
from translation_engine import TranslationEngine


class TranslationReviewApp:
    """번역 검수 GUI 애플리케이션"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI 번역 검수 도구")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 엔진 및 상태 변수
        self.engine: TranslationEngine = None
        self.review_thread: threading.Thread = None
        self.is_running = False
        
        # 언어 옵션
        self.languages = ["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어", "독일어", "러시아어"]
        
        # UI 구성
        self.create_widgets()
        
        # 모델 목록 초기화 (API 키가 없으면 비활성화)
        self.update_model_list()
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # === API 키 입력 섹션 ===
        ttk.Label(main_frame, text="API 키:", font=("맑은 고딕", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        api_frame = ttk.Frame(main_frame)
        api_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        api_frame.columnconfigure(0, weight=1)
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=40)
        self.api_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(api_frame, text="API 키 확인", command=self.test_api_key).grid(row=0, column=1)
        
        row += 1
        
        # === 언어 선택 섹션 ===
        lang_frame = ttk.LabelFrame(main_frame, text="언어 선택", padding="5")
        lang_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        lang_frame.columnconfigure(1, weight=1)
        lang_frame.columnconfigure(3, weight=1)
        
        ttk.Label(lang_frame, text="출발언어:").grid(row=0, column=0, padx=5, pady=5)
        self.source_lang_var = tk.StringVar(value="한국어")
        self.source_lang_combo = ttk.Combobox(lang_frame, textvariable=self.source_lang_var, 
                                             values=self.languages, state="readonly", width=15)
        self.source_lang_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.source_lang_combo.bind("<<ComboboxSelected>>", lambda e: self.on_language_change())
        
        ttk.Label(lang_frame, text="도착언어:").grid(row=0, column=2, padx=5, pady=5)
        self.target_lang_var = tk.StringVar(value="영어")
        self.target_lang_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang_var, 
                                             values=self.languages, state="readonly", width=15)
        self.target_lang_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.target_lang_combo.bind("<<ComboboxSelected>>", lambda e: self.on_language_change())
        
        row += 1
        
        # === AI 모델 선택 섹션 ===
        model_frame = ttk.LabelFrame(main_frame, text="AI 모델 선택", padding="5")
        model_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        model_frame.columnconfigure(1, weight=1)
        
        ttk.Label(model_frame, text="모델:").grid(row=0, column=0, padx=5, pady=5)
        self.model_var = tk.StringVar(value="gemini-1.5-pro")
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       state="readonly", width=30)
        self.model_combo.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(model_frame, text="모델 목록 새로고침", command=self.update_model_list).grid(row=0, column=2, padx=5)
        
        row += 1
        
        # === 파일 선택 섹션 ===
        file_frame = ttk.LabelFrame(main_frame, text="파일 선택", padding="5")
        file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly", width=50)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(file_frame, text="파일 선택", command=self.select_file).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="엑셀 템플릿 생성", command=self.create_template).grid(row=0, column=2, padx=5)
        
        row += 1
        
        # === 실행 버튼 섹션 ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="검수 시작", command=self.start_review, 
                                      style="Accent.TButton", width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="검수 중지", command=self.stop_review, 
                                     state="disabled", width=20)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # === 진행 상황 섹션 ===
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="5")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 통계 표시
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.stats_var = tk.StringVar(value="전체: 0 | 완료: 0 | 크리티컬: 0 | 남은 작업: 0")
        ttk.Label(stats_frame, textvariable=self.stats_var, font=("맑은 고딕", 9)).grid(row=0, column=0, sticky=tk.W)
        
        row += 1
        
        # === 로그 섹션 ===
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="5")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 초기 로그 메시지
        self.log("AI 번역 검수 도구를 시작했습니다.")
        self.log("API 키를 입력하고 확인 버튼을 눌러주세요.")
    
    def on_language_change(self):
        """언어 변경 시 호출"""
        # 언어가 같으면 경고
        if self.source_lang_var.get() == self.target_lang_var.get():
            messagebox.showwarning("경고", "출발언어와 도착언어가 같습니다.")
    
    def test_api_key(self):
        """API 키 테스트"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("오류", "API 키를 입력해주세요.")
            return
        
        try:
            self.log("API 키 확인 중...")
            models = TranslationEngine.get_available_models(api_key)
            if models:
                self.log(f"✓ API 키 확인 완료. 사용 가능한 모델: {len(models)}개")
                self.model_combo['values'] = models
                # 기본 모델이 목록에 있으면 유지, 없으면 첫 번째 모델 선택
                if self.model_var.get() not in models:
                    if models:
                        self.model_var.set(models[0])
                messagebox.showinfo("성공", f"API 키 확인 완료!\n사용 가능한 모델: {len(models)}개")
            else:
                self.log("⚠ API 키는 유효하지만 모델 목록을 가져올 수 없습니다.")
                messagebox.showwarning("경고", "API 키는 유효하지만 모델 목록을 가져올 수 없습니다.")
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ API 키 확인 실패: {error_msg}")
            messagebox.showerror("오류", f"API 키 확인 실패:\n{error_msg}")
    
    def update_model_list(self):
        """모델 목록 업데이트"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            # 기본 모델 목록만 표시
            default_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"]
            self.model_combo['values'] = default_models
            return
        
        try:
            models = TranslationEngine.get_available_models(api_key)
            if models:
                self.model_combo['values'] = models
                if self.model_var.get() not in models and models:
                    self.model_var.set(models[0])
            else:
                # 기본 모델 목록 사용
                default_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"]
                self.model_combo['values'] = default_models
        except Exception as e:
            self.log(f"모델 목록 가져오기 실패: {str(e)}")
            default_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"]
            self.model_combo['values'] = default_models
    
    def select_file(self):
        """파일 선택"""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.log(f"파일 선택: {os.path.basename(file_path)}")
    
    def create_template(self):
        """엑셀 템플릿 생성"""
        source_lang = self.source_lang_var.get()
        target_lang = self.target_lang_var.get()
        
        # 저장 위치 선택
        file_path = filedialog.asksaveasfilename(
            title="템플릿 저장",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 컬럼명 생성
            source_col = TranslationEngine._get_column_name(source_lang)
            target_col = TranslationEngine._get_column_name(target_lang)
            
            # 빈 데이터프레임 생성
            df = pd.DataFrame(columns=[
                source_col,
                target_col,
                "AI 번역",
                "AI 검수 등급",
                "AI 검수",
                "일관성 체크",
                "수정필요 체크"
            ])
            
            # 샘플 데이터 추가
            sample_data = {
                source_col: [f"샘플 {source_lang} 텍스트 1", f"샘플 {source_lang} 텍스트 2"],
                target_col: [f"Sample {target_lang} text 1", f"Sample {target_lang} text 2"],
                "AI 번역": ["", ""],
                "AI 검수 등급": ["", ""],
                "AI 검수": ["", ""],
                "일관성 체크": ["", ""],
                "수정필요 체크": ["", ""]
            }
            df = pd.DataFrame(sample_data)
            
            # 파일 저장
            df.to_excel(file_path, index=False, engine='openpyxl')
            self.log(f"템플릿 생성 완료: {os.path.basename(file_path)}")
            messagebox.showinfo("완료", f"템플릿이 생성되었습니다.\n{file_path}")
        except Exception as e:
            error_msg = str(e)
            self.log(f"템플릿 생성 실패: {error_msg}")
            messagebox.showerror("오류", f"템플릿 생성 실패:\n{error_msg}")
    
    def log(self, message: str):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def progress_callback(self, event_type: str, data):
        """진행률 콜백"""
        if event_type == "log":
            self.log(data)
        elif event_type == "progress":
            current = data.get("current", 0)
            total = data.get("total", 1)
            reviewed = data.get("reviewed", 0)
            critical = data.get("critical", 0)
            
            # 진행률 업데이트
            if total > 0:
                progress = int((current / total) * 100)
                self.progress_bar['value'] = progress
                self.progress_var.set(f"검수 중... ({current}/{total} 행 진행 중)")
            else:
                self.progress_bar['value'] = 0
                self.progress_var.set("대기 중...")
            
            # 통계 업데이트
            remaining = total - reviewed
            self.stats_var.set(f"전체: {total:,} | 완료: {reviewed:,} | 크리티컬: {critical:,} | 남은 작업: {remaining:,}")
    
    def start_review(self):
        """검수 시작"""
        # 입력 검증
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("오류", "API 키를 입력해주세요.")
            return
        
        model_name = self.model_var.get()
        if not model_name:
            messagebox.showerror("오류", "AI 모델을 선택해주세요.")
            return
        
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("오류", "유효한 엑셀 파일을 선택해주세요.")
            return
        
        source_lang = self.source_lang_var.get()
        target_lang = self.target_lang_var.get()
        
        if source_lang == target_lang:
            messagebox.showerror("오류", "출발언어와 도착언어가 같습니다.")
            return
        
        # 엔진 초기화
        try:
            self.engine = TranslationEngine(api_key, model_name, source_lang, target_lang)
            self.engine.set_progress_callback(self.progress_callback)
        except Exception as e:
            messagebox.showerror("오류", f"엔진 초기화 실패:\n{str(e)}")
            return
        
        # 실행 상태 변경
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar['value'] = 0
        self.progress_var.set("검수 시작...")
        
        # 로그 초기화
        self.log_text.delete(1.0, tk.END)
        self.log("=" * 60)
        self.log("번역 검수 시작")
        self.log(f"API 키: {api_key[:10]}...")
        self.log(f"모델: {model_name}")
        self.log(f"출발언어: {source_lang} → 도착언어: {target_lang}")
        self.log(f"파일: {os.path.basename(file_path)}")
        self.log("=" * 60)
        
        # 별도 스레드에서 실행
        self.review_thread = threading.Thread(target=self.run_review, args=(file_path,), daemon=True)
        self.review_thread.start()
    
    def run_review(self, file_path: str):
        """검수 실행 (별도 스레드)"""
        try:
            summary = self.engine.review_file(file_path)
            
            # 완료 메시지
            self.log("=" * 60)
            self.log("검수 완료 요약")
            self.log("=" * 60)
            self.log(f"검수 완료: {summary['reviewed']:,} 행")
            self.log(f"크리티컬 이슈: {summary['critical']:,} 행")
            self.log(f"검수 대기: {summary['remaining']:,} 행")
            
            if summary['exit_reason']:
                self.log(f"종료 이유: {summary['exit_reason']}")
            
            if summary['quota_error']:
                self.log("⚠️  토큰/할당량이 부족합니다!")
                self.log("다음 중 하나를 시도해보세요:")
                self.log("1. API 할당량 확인 (Google Cloud Console)")
                self.log("2. 유료 플랜으로 업그레이드")
                self.log("3. 다음 날까지 대기 (일일 할당량 리셋)")
                self.log("4. 다른 API 키 사용")
            else:
                self.log("✅ 모든 검수가 정상적으로 완료되었습니다!")
            
            self.log(f"결과 파일: {os.path.basename(summary['output_file'])}")
            self.log("=" * 60)
            
            # UI 업데이트 (메인 스레드에서)
            self.root.after(0, self.review_completed, summary)
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"오류 발생: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("오류", f"검수 중 오류 발생:\n{error_msg}"))
            self.root.after(0, self.review_completed, None)
    
    def review_completed(self, summary):
        """검수 완료 처리"""
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if summary:
            self.progress_var.set("검수 완료")
            self.progress_bar['value'] = 100
            messagebox.showinfo("완료", 
                              f"검수 완료!\n\n"
                              f"검수 완료: {summary['reviewed']:,} 행\n"
                              f"크리티컬 이슈: {summary['critical']:,} 행\n"
                              f"남은 작업: {summary['remaining']:,} 행\n\n"
                              f"결과 파일: {os.path.basename(summary['output_file'])}")
        else:
            self.progress_var.set("오류 발생")
            self.progress_bar['value'] = 0
    
    def stop_review(self):
        """검수 중지"""
        if self.engine:
            self.engine.stop()
            self.log("검수 중지 요청...")
            self.is_running = False


def main():
    """메인 함수"""
    root = tk.Tk()
    app = TranslationReviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

