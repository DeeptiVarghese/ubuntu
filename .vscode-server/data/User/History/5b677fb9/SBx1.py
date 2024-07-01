from airflow import DAG
from datetime import timedelta, datetime
import json
from airflow.operators.python import PythonOperator



# Write the JSON response to a file
    with open(output_file_path, "w") as output_file:
        json.dump(response_data, output_file, indent=4)  # indent for pretty formatting
    output_list = [output_file_path, file_str]
    return output_list   






default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 8, 1),
    'email': ['myemail@domain.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=15)
}




with DAG('amazon_analytics_dag',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        extract_amazon_data_var = PythonOperator(
        task_id= 'tsk_extract_amazon_data_var',
        python_callable=extract_amazon_data,
        op_kwargs={'url': 'https://real-time-amazon-data.p.rapidapi.com/product-details', 'querystring': {"asin":"B07ZPKBL9V","country":"US"}, 'headers': api_host_key, 'date_string':dt_now_string}
        )