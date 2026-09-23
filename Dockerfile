FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home appuser
COPY --chown=appuser:appuser app.py ./app.py
COPY --chown=appuser:appuser app_pages ./app_pages
COPY --chown=appuser:appuser healthlens ./healthlens
COPY --chown=appuser:appuser ui ./ui
COPY --chown=appuser:appuser .streamlit/config.toml ./.streamlit/config.toml
USER appuser
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
