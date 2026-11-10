from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

ML = "cd /opt/solarsense && /home/airflow/ml-venv/bin/python src/"
DEFAULTS = {"retries": 2, "retry_delay": timedelta(minutes=5)}

with DAG(
    "solarsense_hourly",
    description="Clima → base horária → esperado × real → previsão",
    schedule="10 * * * *",
    start_date=datetime(2026, 11, 10),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULTS,
    tags=["solarsense"],
) as hourly:
    refresh_weather = BashOperator(task_id="refresh_weather", bash_command=ML + "load_weather.py --refresh")
    build_hourly = BashOperator(task_id="build_plant_hourly", bash_command=ML + "build_plant_hourly.py")
    predict_history = BashOperator(task_id="predict_history", bash_command=ML + "predict.py history")
    predict_forecast = BashOperator(task_id="predict_forecast", bash_command=ML + "predict.py forecast")

    refresh_weather >> build_hourly >> predict_history
    refresh_weather >> predict_forecast

with DAG(
    "solarsense_weekly_retrain",
    description="Retreino semanal dos 5 modelos e registro do campeão no MLflow",
    schedule="0 4 * * 1",
    start_date=datetime(2026, 11, 10),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULTS,
    tags=["solarsense"],
) as weekly:
    train = BashOperator(task_id="train", bash_command=ML + "train.py", execution_timeout=timedelta(hours=1))
    repredict_history = BashOperator(task_id="predict_history", bash_command=ML + "predict.py history")
    repredict_forecast = BashOperator(task_id="predict_forecast", bash_command=ML + "predict.py forecast")

    typical_months = BashOperator(task_id="predict_typical", bash_command=ML + "predict.py typical")

    train >> [repredict_history, repredict_forecast, typical_months]
