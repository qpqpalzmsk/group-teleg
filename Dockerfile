# 기본 Python 이미지 (경량 버전 사용)
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    && pip install --upgrade pip

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 봇 코드 및 설정 파일 복사
COPY . .

# 실행 명령어
CMD ["python", "main.py"]