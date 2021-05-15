FROM python:3.9-slim

ENV API_STATUS_MONITOR_WHL="api_status_monitor-0.0.1-py3-none-any.whl"

RUN useradd -m statusmonitor
RUN mkdir /opt/statusmonitor && chown statusmonitor:statusmonitor /opt/statusmonitor
WORKDIR /opt/statusmonitor
USER statusmonitor

COPY conf/ /opt/statusmonitor/conf
COPY "dist/$API_STATUS_MONITOR_WHL" .

RUN python3 -m venv statusmonitor-venv && . statusmonitor-venv/bin/activate && \
    pip install $API_STATUS_MONITOR_WHL

ARG command
ENV COMMAND=$command
ENTRYPOINT . statusmonitor-venv/bin/activate && statusmonitor $COMMAND
