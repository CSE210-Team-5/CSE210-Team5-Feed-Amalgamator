# syntax=docker/dockerfile:1

FROM python:3.11

WORKDIR /code

COPY . .
RUN pip install --no-cache-dir setuptools==69.0.2 wheel==0.42.0 pdm==2.10.4
RUN pdm init -gn &&\
    pdm install &&\
    pdm list

EXPOSE 80

ENTRYPOINT ["pdm","run","gunicorn", "-b", "0.0.0.0:80","feed_amalgamator.__init__:create_app()"]