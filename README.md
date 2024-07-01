Capstone Project Proposal:

The Amazon data set is a free streaming dataset which has several GB of data, hence was selected for the capstone.
The technologies were mostly selected for learning purposes.
Steps of the project:
1.	Extract real time Amazon data from https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data
2.	Load data into AWS S3
3.	Use Kafka to stream data from S3 to dbt
4.	Transform data using Spark 
5.	Load transformed data to S3
6.	Create Tableau Dashboard
7.	Orchestrate with Airflow in Docker
   
Conceptual Data Model:

![image](https://github.com/DataExpert-ZachWilson-V4/capstone-project-deeptivarghese/assets/31417684/6327726c-4070-4c00-912b-7ec92118d631)

 
Output:
Live tableau dashboard that refreshes on a daily cadence and displays 
1.	products with max reviews, 
2.	top rated products, 
3.	products marked as best sellers, 
4.	products with best deals and corresponding savings (discount %), 
5.	new products added under each category etc.


Update 6/30/2024:

Initial proposal could not be implemented due to Docker repeatedly failing in my Windows10 laptop.
After long struggles, I finally decided I would  replicate an existing AWS project explained in Youtube. I watched parts 1,2, & 3 of this Zillow API project in tuplespectra channel  - https://www.youtube.com/watch?v=j_skupZ3zw0, https://www.youtube.com/watch?v=TvoiQ8Z1lGA, https://www.youtube.com/watch?v=Hfu3E0zLYDQ
I created an AWS account for the purpose of the project and deployed EC2 instance, S3 buckets, used Lambda functions, Redshift cluster and QuickSight.
Since I had to struggle with the SSH setup on Windows10 laptop, I could only use Product Category table from above Conceptual Data Model. Joining this table with other tables and analysing data will be done in later iterations of the project

I accidentally deleted the scripts from EC2 instance while trying to push code to capstone public repository. Luckily, I had saved the project in my private repository which I am sharing here.

Steps of the project:
1.	Extract real time Amazon data from [https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data](https://real-time-amazon-data.p.rapidapi.com/products-by-category) 
2.	Load json data into AWS S3 bucket - deevar-bucket
3.	Loading data into above S3 bucket at step 2 triggers a lambda function - copyRawJsonFile-lambdaFunction
4.	Above lambda function at step 3 loads json data to intermediate S3 bucket - copy-of-raw-json-bucket5
5.	Loading data into above intermediate S3 bucket at step 4 triggers a lambda function which performs transformations of the raw json file and converts to csv file- transformation-convert-to-csv-lambdaFunction
6.	Above lambda function at step 5 loads csv file with transformed data to final S3 bucket - cleaned-data-zone-csv-bucket5
7.	There is an S3 key sensor which keeps checking every 5 seconds upto 60 seconds if the above S3 bucket at step 6 has data
8.	If S3 bucket has transformed csv data, data is loaded to Redshift table named 'amazondata'
9.	Once the data is loaded into Redshift table, then QuickSight is connected to the Redshift cluster to visualize the Amazon Products by Category data ([rapid api dat](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data/playground/apiendpoint_7d5e4b9c-8c7b-4168-a303-e1e191d0745e)
    

![image](https://github.com/DeeptiVarghese/ubuntu/assets/31417684/366798a8-6ede-4c75-9a43-ff39c06f1e31)

Output:
Live QuickSight dashboard named 'Amazon analysis' that refreshes on an hourly cadence and displays https://us-west-2.quicksight.aws.amazon.com/sn/analyses/97f89226-142b-4fe4-a074-68a9dcbd4f93?#
1.	Prices per product, 
2.	Number of ratings per product, 
3.	Product Info chart that displays url, photo and star rating  of products, 
4.	Products and discount offered, 
5.	Number of discount offers per product,
6.	Comparison of product price vs start rating per product
7.	All charts can be filtered by 'best_seller', 'amazon_choice' and 'prime_status' fields



amazonanalytics.py is the main file which has Airflow DAG - amazon_analytics_dag which has an 'hourly' schedule interval. Brief explanation of the functions below:
1. 'extract_amazon_data' reads data from api https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data/playground/apiendpoint_7d5e4b9c-8c7b-4168-a303-e1e191d0745e and saves data as a json file in EC2 instance
2. Within amazon_analytics_dag, first task named 'tsk_extract_amazon_data_var' extracts data from Rapid API by calling above function from step 1 and passing a set of arguments like API link, query string & API host key to produce a json file 
3. Second task is named 'tsk_load_to_s3' which loads json file to S3 bucket named deevar-bucket
4. Third task is named 'tsk_is_file_in_s3_available' which is an S3 key sensor which keeps checking every 5 seconds upto 60 seconds if the above S3 bucket named cleaned-data-zone-csv-bucket5 has transformed data in csv file
5. Fourth task is named 'tsk_transfer_s3_to_redshift' which loads csv file from above step to Redshift table named 'amazondata' 
6. DAG - extract_amazon_data_var >> load_to_s3 >> is_file_in_s3_available >> transfer_s3_to_redshift


Below are the scripts for 2 lambda functions used 

1. copyRawJsonFile-lambdaFunction

import boto3
import json

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO implement
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
   
    
    target_bucket = 'copy-of-raw-json-bucket5'
    copy_source = {'Bucket': source_bucket, 'Key': object_key}
   
    waiter = s3_client.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=object_key)
    s3_client.copy_object(Bucket=target_bucket, Key=object_key, CopySource=copy_source)
    return {
        'statusCode': 200,
        'body': json.dumps('Copy completed successfully')
    }

2.Transformation-convert-to-csv-lambdaFunction

import json
import boto3
import json
import pandas as pd

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO implement
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    target_bucket = 'cleaned-data-zone-csv-bucket5'
    target_file_name = object_key[:-5]
    print(target_file_name)
   
    waiter = s3_client.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=object_key)
    
    response = s3_client.get_object(Bucket=source_bucket, Key=object_key)
    print(response)
    data=response['Body']
    print(data)
    data = response['Body'].read().decode('utf-8')
    print(data)
    data = json.loads(data)
    print(data)

    data=data["data"]["products"]
   
    df=pd.DataFrame(data,columns=['asin', 'product_title','currency', 'product_price', 'product_original_price',
                     'product_minimum_offer_price','product_star_rating','product_num_ratings', 'product_url',
                     'product_photo','product_num_offers','is_best_seller','is_amazon_choice',
                     'is_prime','climate_pledge_friendly','sales_volume','delivery'])
   
    df['product_price']=(df['product_price'].str[1:]).astype(float).fillna(0.0)

    df['product_original_price']=(df['product_original_price'].str[1:]).astype(float).fillna(0.0)

    df['product_minimum_offer_price']=(df['product_minimum_offer_price'].str[1:]).astype(float).fillna(0.0)

    df['product_star_rating']=(df['product_star_rating']).astype(float).fillna(0.0)
    
    df['product_num_ratings']=(df['product_num_ratings']).astype(int).fillna(0)

    df['product_num_offers']=(df['product_num_offers']).astype(int).fillna(0)
   
    print(df)
    
    # Convert DataFrame to CSV format
    csv_data = df.to_csv(index=False)
    
    # Upload CSV to S3
    bucket_name = target_bucket
    object_key = f"{target_file_name}.csv"
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_data)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('CSV conversion and S3 upload completed successfully')
    }


Below is query used to create the Redshift table 'amazondata'

CREATE TABLE IF NOT EXISTS amazondata (
        product_id VARCHAR(255) PRIMARY KEY,
        product_title VARCHAR(255),
        currency VARCHAR(255),
        product_price REAL,
        product_original_price REAL,
        product_minimum_offer_price REAL,
        product_star_rating REAL,
        product_num_ratings INT,
        product_url VARCHAR(255),
        product_photo VARCHAR(255),
        product_num_offers INT,
        is_best_seller VARCHAR(255),
        is_amazon_choice VARCHAR(255),
        is_prime VARCHAR(255),
        climate_pledge_friendly VARCHAR(255),
        sales_volume VARCHAR(255),
        delivery VARCHAR(255)
        );

      
        SELECT *
        FROM amazondata




