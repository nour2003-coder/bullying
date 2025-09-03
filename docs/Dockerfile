FROM python:3.9-slim-buster AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim-buster

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# Download NLTK data
RUN python -c "import nltk; nltk.download(\'stopwords\'); nltk.download(\'punkt\'); nltk.download(\'wordnet\'); nltk.download(\'averaged_perceptron_tagger\')"

CMD ["python", "scraper.py"]