# Git 및 GitFork 설정 가이드

## 1. Git 저장소 초기화 (이미 완료된 경우 생략)

```bash
git init
```

## 2. 파일 추가 및 첫 커밋

```bash
# .gitignore 추가
git add .gitignore

# 자동검수 폴더의 소스 파일 추가
git add 자동검수/*.py
git add 자동검수/*.txt
git add 자동검수/*.md
git add 자동검수/*.bat

# README 추가
git add README.md

# 첫 커밋
git commit -m "Initial commit: AI 번역 검수 도구"
```

## 3. GitHub/GitLab 원격 저장소 생성

1. GitHub (https://github.com) 또는 GitLab에 로그인
2. "New repository" 클릭
3. 저장소 이름 입력 (예: `translation-review-tool`)
4. Public 또는 Private 선택
5. "Create repository" 클릭

## 4. 원격 저장소 연결

```bash
# 원격 저장소 URL 추가 (예시)
git remote add origin https://github.com/사용자명/저장소명.git

# 또는 SSH 사용
git remote add origin git@github.com:사용자명/저장소명.git
```

## 5. GitFork에서 사용하기

### GitFork 설치

1. https://git-fork.com 에서 GitFork 다운로드 및 설치

### GitFork에서 저장소 열기

1. GitFork 실행
2. "File" > "Open Repository" 또는 `Ctrl+O`
3. 프로젝트 폴더 선택: `Z:\VibeCoding\디바인엣지 자동번역`
4. 저장소가 열립니다

### GitFork에서 커밋 및 푸시

1. **변경사항 확인**: 왼쪽 패널에서 "Uncommitted Changes" 확인
2. **파일 스테이징**:
   - 변경된 파일을 선택
   - "Stage" 버튼 클릭 또는 `Ctrl+S`
3. **커밋 메시지 작성**: 하단에 커밋 메시지 입력
4. **커밋**: "Commit" 버튼 클릭 또는 `Ctrl+Enter`
5. **푸시**: "Push" 버튼 클릭 또는 `Ctrl+Shift+P`

### GitFork 주요 기능

- **브랜치 관리**: 왼쪽 패널에서 브랜치 생성/전환
- **히스토리 보기**: 커밋 히스토리 그래프 확인
- **병합/리베이스**: GUI로 쉽게 병합 작업
- **충돌 해결**: 충돌 발생 시 시각적으로 해결

## 6. 첫 푸시

```bash
# 메인 브랜치 이름 확인 (main 또는 master)
git branch -M main

# 원격 저장소에 푸시
git push -u origin main
```

또는 GitFork에서:

1. "Push" 버튼 클릭
2. 원격 저장소 선택
3. 브랜치 선택 (main)
4. "Push" 클릭

## 7. 일상적인 작업 흐름

1. **코드 수정**
2. **GitFork에서 변경사항 확인**
3. **변경된 파일 스테이징**
4. **커밋 메시지 작성 및 커밋**
5. **원격 저장소에 푸시**

## 주의사항

- `.gitignore`에 포함된 파일(엑셀 파일, 빌드 결과물 등)은 Git에 추가되지 않습니다
- API 키는 절대 Git에 커밋하지 마세요
- 민감한 정보가 포함된 파일은 `.gitignore`에 추가하세요
