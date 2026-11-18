FROM python:3.13-slim

# Hugging Face Spaces run the app as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

# A public demo: the two sample contracts, no server API key and no uploads.
# Visitors can search for free, or bring their own key for written answers.
ENV ACTIVE_SET=sample \
    ALLOW_UPLOADS=false \
    FASTEMBED_CACHE_PATH=/home/user/app/model_cache

# Download the local models and build the search index now,
# so the first visitor does not wait for them.
RUN python main.py index --set sample --scheme clause

EXPOSE 7860
CMD ["uvicorn", "clausemark.api.server:app", "--host", "0.0.0.0", "--port", "7860"]
