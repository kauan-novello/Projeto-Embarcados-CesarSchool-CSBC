FROM apache/airflow:3.1.3-python3.12

COPY requirements.txt /tmp/ml-requirements.txt
RUN grep -v -E "^(jupyter|seaborn)" /tmp/ml-requirements.txt > /tmp/ml-runtime.txt \
    && python -m venv /home/airflow/ml-venv \
    && /home/airflow/ml-venv/bin/pip install --no-cache-dir -r /tmp/ml-runtime.txt
