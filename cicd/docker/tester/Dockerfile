FROM python:3.10

RUN pip install poetry coverage
RUN poetry config virtualenvs.create false

WORKDIR /testing
COPY pyproject.toml poetry.lock ./

RUN poetry install -E webserver -E image-tools -E localdisplay


