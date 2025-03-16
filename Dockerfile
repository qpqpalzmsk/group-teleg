# Python 3.10 기반 이미지 사용
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 봇 코드 복사
COPY . .

# 실행할 Python 스크립트 지정 (예: bot.py)
CMD ["python", "bot.py"]