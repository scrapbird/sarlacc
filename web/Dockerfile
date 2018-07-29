FROM alpine

# Install python3.6
RUN apk add --no-cache python3  && \
	python3 -m ensurepip && \
	rm -r /usr/lib/python*/ensurepip && \
	pip3 install --upgrade pip setuptools && \
	if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
	if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
	rm -r /root/.cache

# Install nodejs
RUN apk add --update nodejs nodejs-npm nodejs-npm

# Install psycopg2 deps
RUN apk add postgresql-dev gcc python3-dev musl-dev

# Create root dir
RUN mkdir /sarlacc

# Add backend dir
ADD ./src/backend /sarlacc/backend

# Install backend deps
WORKDIR /sarlacc/backend
RUN pip3 install -r requirements.txt

# Add frontend dir
ADD ./src/frontend /sarlacc/frontend

# Configure and build web frontend
WORKDIR /sarlacc/frontend
RUN npm run build
RUN ln -s /sarlacc/frontend/build /sarlacc/backend/static

# Add user
RUN adduser -S sarlacc
USER sarlacc

WORKDIR /sarlacc/backend
CMD ["python", "app.py"]
