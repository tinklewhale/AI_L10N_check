"""
번역 검수 엔진 클래스
기존 translation_review.py의 로직을 클래스로 리팩토링
"""
import pandas as pd
import google.generativeai as genai
import time
import os
import json
import shutil
from typing import Callable, Optional, Dict, Any


class TranslationEngine:
    """번역 검수 엔진 클래스"""
    
    # Gemini 1.5 기능: 강제로 JSON만 뱉게 설정
    GENERATION_CONFIG = {
        "temperature": 0.2,
        "response_mime_type": "application/json"
    }
    
    # 검수용 프롬프트 템플릿
    REVIEW_PROMPT_TEMPLATE = """당신은 전문 게임 현지화 품질 검수자입니다.
{source_language} 텍스트와 {target_language} 번역을 검토한 후 다음을 제공하세요:
1. 품질 등급: 양호, 보통, 또는 크리티컬
2. 개선된 {target_language} 번역
3. 등급 판단 이유 (한국어로 작성)
4. 일관성 체크 (게임 맥락에서 용어, 톤, 스타일 일관성 분석, 한국어로 작성)

{source_language} 텍스트: {source_text}
{target_language} 번역: {target_text}

다음 JSON 형식으로만 응답하세요:
{{
    "rating": "양호|보통|크리티컬",
    "improved_translation": "개선된 {target_language} 번역",
    "review_reason": "등급 판단 이유 (한국어)",
    "consistency_check": "일관성 분석 (한국어)"
}}

JSON 형식으로만 응답하고, 추가 텍스트는 포함하지 마세요."""
    
    def __init__(self, api_key: str, model_name: str, source_language: str = "한국어", target_language: str = "영어"):
        """
        TranslationEngine 초기화
        
        Args:
            api_key: Gemini API 키
            model_name: 사용할 모델명
            source_language: 출발언어 (기본값: 한국어)
            target_language: 도착언어 (기본값: 영어)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.source_language = source_language
        self.target_language = target_language
        
        # API 설정
        genai.configure(api_key=api_key)
        
        # 모델 초기화
        self.model = genai.GenerativeModel(model_name, generation_config=self.GENERATION_CONFIG)
        
        # 진행률 콜백
        self.progress_callback: Optional[Callable] = None
        self.should_stop = False
        
        # 컬럼명 설정
        self.source_col = self._get_column_name(source_language)
        self.target_col = self._get_column_name(target_language)
        self.ai_translation_col = "AI 번역"
        self.ai_rating_col = "AI 검수 등급"
        self.ai_review_col = "AI 검수"
        self.consistency_col = "일관성 체크"
        self.check_col = "수정필요 체크"
    
    @staticmethod
    def _get_column_name(language: str) -> str:
        """언어명을 컬럼명으로 변환"""
        lang_map = {
            "한국어": "KO",
            "영어": "ENG",
            "일본어": "JP",
            "중국어": "CN",
            "스페인어": "ES",
            "프랑스어": "FR",
            "독일어": "DE",
            "러시아어": "RU"
        }
        return lang_map.get(language, language.upper()[:3])
    
    @staticmethod
    def get_available_models(api_key: str) -> list:
        """사용 가능한 모델 목록을 가져옴"""
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name.split('/')[-1] for m in genai.list_models() 
                              if 'generateContent' in m.supported_generation_methods]
            return available_models
        except Exception as e:
            print(f"Warning: Could not list models: {e}")
            return []
    
    def set_progress_callback(self, callback: Callable):
        """진행률 콜백 함수 설정"""
        self.progress_callback = callback
    
    def stop(self):
        """검수 중단 요청"""
        self.should_stop = True
    
    def _log(self, message: str):
        """로그 메시지 출력 (콜백이 있으면 콜백 사용)"""
        if self.progress_callback:
            self.progress_callback("log", message)
        else:
            print(message)
    
    def _update_progress(self, current: int, total: int, reviewed: int, critical: int):
        """진행률 업데이트"""
        if self.progress_callback:
            self.progress_callback("progress", {
                "current": current,
                "total": total,
                "reviewed": reviewed,
                "critical": critical
            })
    
    def review_translation(self, source_text: str, target_text: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        번역을 검수하고 결과를 반환
        
        Args:
            source_text: 출발언어 텍스트
            target_text: 도착언어 번역 텍스트
            max_retries: 최대 재시도 횟수
            
        Returns:
            검수 결과 딕셔너리 또는 None
        """
        if not isinstance(source_text, str) or str(source_text).strip() == "":
            return None
        
        if not isinstance(target_text, str) or str(target_text).strip() == "":
            return None
        
        prompt = self.REVIEW_PROMPT_TEMPLATE.format(
            source_language=self.source_language,
            target_language=self.target_language,
            source_text=source_text.strip(),
            target_text=target_text.strip()
        )
        
        # 재시도 로직
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                # 바로 JSON 로딩
                try:
                    result_json = json.loads(response.text)
                    return result_json
                except json.JSONDecodeError as json_err:
                    raise ValueError(f"JSON 파싱 실패: {str(json_err)[:100]}")
                
            except Exception as e:
                error_str = str(e).lower()
                # 토큰 부족 관련 에러 감지
                is_quota_error = any(keyword in error_str for keyword in [
                    "quota", "resource exhausted", "rate limit", "billing", 
                    "429", "insufficient", "exceeded", "limit"
                ])
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초로 증가
                    time.sleep(wait_time)
                else:
                    # 마지막 시도 실패 시
                    error_msg = f"API 오류 발생 (재시도 실패): {str(e)[:100]}"
                    if is_quota_error:
                        error_msg = f"토큰/할당량 부족: {str(e)[:100]}"
                    
                    return {
                        "rating": "보통",
                        "improved_translation": target_text,  # 원본 번역 유지
                        "review_reason": error_msg,
                        "consistency_check": "검수 실패로 인해 확인 불가",
                        "_is_quota_error": is_quota_error,
                        "_error": str(e)
                    }
        
        return {
            "rating": "보통",
            "improved_translation": target_text,
            "review_reason": "재시도 횟수 초과",
            "consistency_check": "검수 실패로 인해 확인 불가"
        }
    
    def review_file(self, input_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        엑셀 파일의 번역을 검수
        
        Args:
            input_file: 입력 엑셀 파일 경로
            output_file: 출력 엑셀 파일 경로 (None이면 자동 생성)
            
        Returns:
            검수 결과 요약 딕셔너리
        """
        self.should_stop = False
        
        # 출력 파일명 설정
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_Result.xlsx"
        
        # 원본 파일 확인
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_file}")
        
        # 결과 파일이 없으면 원본 복사
        if not os.path.exists(output_file):
            self._log(f"결과 파일 생성: {output_file}")
            shutil.copyfile(input_file, output_file)
        
        # 파일 크기 확인
        file_size = os.path.getsize(output_file)
        if file_size < 5000:
            self._log("경고: 파일 크기가 비정상적으로 작습니다.")
        
        # 파일 로드
        try:
            df = pd.read_excel(output_file, engine='openpyxl')
        except Exception as e:
            raise Exception(f"파일 로드 실패: {str(e)}")
        
        # 필수 컬럼 확인
        required_cols = [self.source_col, self.target_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")
        
        # 결과 컬럼 생성
        if self.ai_translation_col not in df.columns:
            df[self.ai_translation_col] = ""
        if self.ai_rating_col not in df.columns:
            df[self.ai_rating_col] = ""
        if self.ai_review_col not in df.columns:
            df[self.ai_review_col] = ""
        if self.consistency_col not in df.columns:
            df[self.consistency_col] = ""
        if self.check_col not in df.columns:
            df[self.check_col] = ""
        
        # CHECK_COL을 문자열 타입으로 설정
        if df[self.check_col].dtype != 'object':
            df[self.check_col] = df[self.check_col].astype(str)
        
        # 검수 대상 확인
        total_rows = len(df)
        rows_to_review = []
        
        for index, row in df.iterrows():
            source_text = row[self.source_col]
            target_text = row[self.target_col]
            ai_translation = row[self.ai_translation_col] if self.ai_translation_col in df.columns else ""
            ai_rating = row[self.ai_rating_col] if self.ai_rating_col in df.columns else ""
            
            # 출발언어와 도착언어가 모두 있어야 검수 가능
            if pd.isna(source_text) or str(source_text).strip() == "":
                continue
            if pd.isna(target_text) or str(target_text).strip() == "":
                continue
            
            # 이미 검수된 행은 스킵 (AI 번역과 AI 검수 등급이 모두 있으면)
            if (pd.notna(ai_translation) and str(ai_translation).strip() != "" and 
                pd.notna(ai_rating) and str(ai_rating).strip() != ""):
                continue
            
            rows_to_review.append(index)
        
        self._log(f"전체 행 수: {total_rows:,}")
        self._log(f"검수 대상: {len(rows_to_review):,} 행")
        
        # 검수 실행
        reviewed_count = 0
        critical_count = 0
        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 2
        
        exit_reason = None
        quota_error_detected = False
        
        try:
            for idx, index in enumerate(rows_to_review):
                if self.should_stop:
                    exit_reason = "사용자에 의한 중단"
                    break
                
                row = df.loc[index]
                source_text = row[self.source_col]
                target_text = row[self.target_col]
                
                # 검수 실행
                result = self.review_translation(source_text, target_text)
                
                if result:
                    # 토큰 부족 에러 확인
                    if result.get("_is_quota_error", False):
                        quota_error_detected = True
                        exit_reason = "토큰/할당량 부족으로 인한 종료"
                        self._log(f"⚠️  토큰/할당량 부족이 감지되었습니다!")
                        break
                    
                    # 성공한 경우 연속 실패 카운터 리셋
                    consecutive_failures = 0
                    
                    # 4개 열에 분리 저장
                    df.at[index, self.ai_translation_col] = result.get("improved_translation", target_text)
                    df.at[index, self.ai_rating_col] = result.get("rating", "")
                    df.at[index, self.ai_review_col] = result.get("review_reason", "")
                    df.at[index, self.consistency_col] = result.get("consistency_check", "")
                    
                    # 크리티컬인 경우 수정필요 체크
                    rating = result.get("rating", "")
                    if rating == "크리티컬":
                        df.at[index, self.check_col] = "✓"
                        critical_count += 1
                    
                    reviewed_count += 1
                else:
                    # 실패한 경우
                    consecutive_failures += 1
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        exit_reason = f"연속 {MAX_CONSECUTIVE_FAILURES}회 실패로 인한 중단"
                        self._log(f"경고: {MAX_CONSECUTIVE_FAILURES}회 연속 실패했습니다.")
                        break
                
                # 진행률 업데이트
                self._update_progress(idx + 1, len(rows_to_review), reviewed_count, critical_count)
                
                # Rate Limit 방지
                time.sleep(1.5)
                
                # 50개마다 중간 저장
                if reviewed_count % 50 == 0 and reviewed_count > 0:
                    df.to_excel(output_file, index=False, engine='openpyxl')
                    self._log(f"진행 상황 저장: {reviewed_count} 행 검수 완료")
        
        except Exception as e:
            exit_reason = f"예상치 못한 오류: {str(e)[:100]}"
            self._log(f"오류 발생: {e}")
        
        # 최종 저장
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # 결과 요약
        summary = {
            "total_rows": total_rows,
            "rows_to_review": len(rows_to_review),
            "reviewed": reviewed_count,
            "critical": critical_count,
            "remaining": len(rows_to_review) - reviewed_count,
            "exit_reason": exit_reason,
            "quota_error": quota_error_detected,
            "output_file": output_file
        }
        
        return summary

