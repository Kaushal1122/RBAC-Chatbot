FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 7860

CMD uvicorn milestone_3.main:app --host 0.0.0.0 --port 8000 & streamlit run milestone_4/app.py --server.port=7860 --server.address=0.0.0.0
