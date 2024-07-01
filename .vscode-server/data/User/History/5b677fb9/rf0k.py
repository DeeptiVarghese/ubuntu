from airflow import DAG
from datetime import timedelta, datetime
import json
import requests
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator




# Load JSON config file
with open('/home/ubuntu/airflow/config_api.json', 'r') as config_file:
    api_host_key = json.load(config_file)


now = datetime.now()
dt_now_string = now.strftime("%d%m%Y%H%M%S")

# Define the S3 bucket
s3_bucket = 'cleaned-data-zone-csv-bucket5'

def extract_amazon_data(**kwargs):
    url = kwargs['url']
    headers = kwargs['headers']
    querystring = kwargs['querystring']
    dt_string = kwargs['date_string']
    # return headers
    response = requests.get(url, headers=headers, params=querystring)
    response_data = response.json()

 # Specify the output file path
    output_file_path = f"/home/ubuntu/response_data_{dt_string}.json"
    file_str = f'response_data_{dt_string}.csv'

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
        # op_kwargs={'url': 'https://real-time-amazon-data.p.rapidapi.com/product-details', 'querystring': {"asin":"B07ZPKBL9V","country":"US"}, 'headers': api_host_key, 'date_string':dt_now_string}
        op_kwargs={'url': 'https://real-time-amazon-data.p.rapidapi.com/products-by-category', 'querystring': {"category_id":"2478868012","page":"1","country":"US","sort_by":"RELEVANCE","product_condition":"ALL"}, 'headers': api_host_key, 'date_string':dt_now_string}
        )
        #"asin":"B07ZPKBL9V","country":"US"



        load_to_s3 = BashOperator(
            task_id = 'tsk_load_to_s3',
            bash_command = 'aws s3 mv {{ ti.xcom_pull("tsk_extract_amazon_data_var")[0]}} s3://deevar-bucket/',
        )


        is_file_in_s3_available = S3KeySensor(
        task_id='tsk_is_file_in_s3_available',
        bucket_key='{{ti.xcom_pull("tsk_extract_amazon_data_var")[1]}}',
        bucket_name=s3_bucket,
        aws_conn_id='aws_s3_conn',
        wildcard_match=False,  # Set this to True if you want to use wildcards in the prefix
        timeout=60,  # Optional: Timeout for the sensor (in seconds)
        poke_interval=5,  # Optional: Time interval between S3 checks (in seconds)
        )
        
        transfer_s3_to_redshift = S3ToRedshiftOperator(
        task_id="tsk_transfer_s3_to_redshift",
        aws_conn_id='aws_s3_conn',
        redshift_conn_id='conn_id_redshift',
        s3_bucket=s3_bucket,
        s3_key='{{ti.xcom_pull("tsk_extract_amazon_data_var")[1]}}',
        schema="PUBLIC",
        table="amazondata",
        copy_options=["csv IGNOREHEADER 1"],
    )

        extract_amazon_data_var >> load_to_s3 >> is_file_in_s3_available >> transfer_s3_to_redshift