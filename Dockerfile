FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Step 1: Preprocess
RUN python milestone_1/preprocess_docs.py

# Step 2: Chunk
RUN python milestone_1/chunker.py

# Step 3: Embed
RUN python milestone_2/embedder.py

EXPOSE 7860

CMD ["uvicorn", "milestone_3.main:app", "--host", "0.0.0.0", "--port", "7860"]
