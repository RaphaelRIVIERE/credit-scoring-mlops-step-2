FROM python:3.11-slim

WORKDIR /app

# libgomp1 est requis par LightGBM (absent de l'image slim par défaut)
RUN apt-get update && apt-get install -y libgomp1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY src/ src/
COPY model/ model/

ENV MODEL_PATH=model

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
