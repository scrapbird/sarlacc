FROM python:3.4-alpine
ADD ./src /sarlacc
WORKDIR /sarlacc
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
