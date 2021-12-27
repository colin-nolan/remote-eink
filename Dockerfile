FROM python:3.10-alpine as base

FROM base as builder

RUN mkdir /install
WORKDIR /install

RUN apk add --update alpine-sdk libffi-dev

RUN pip install poetry
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.path "${PWD}/venv"
RUN poetry install --no-dev --remove-untracked


FROM base

COPY --from=builder /install/venv /usr/local/remote-eink
