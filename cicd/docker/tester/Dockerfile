FROM python:3.10

RUN curl -fsSL https://uploader.codecov.io/latest/linux/codecov > /usr/local/bin/codecov \
    && chmod +x /usr/local/bin/codecov

RUN pip install poetry coverage
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /tmp/

RUN cd /tmp \
    && poetry install -E webserver -E image-tools -E localdisplay


