FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn httpx python-multipart

# 复制项目文件
COPY . .

# 创建 UI 目录
RUN mkdir -p /app/ui
COPY ui/index.html /app/ui/index.html

# 报告目录
RUN mkdir -p /app/reports

EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
