# utils/s3_utils.py

import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import NoCredentialsError, ClientError

def get_s3_client():
    """Initialize and return an S3 client using Streamlit secrets."""
    AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
    AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]

    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

def save_to_s3(filename, df, bucket_name=None):
    """
    Saves the given dataframe to S3 as a CSV.
    """
    if bucket_name is None:
        bucket_name = st.secrets["BUCKET_NAME"]

    s3_client = get_s3_client()
    csv_buffer = df.to_csv(index=False)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=filename, Body=csv_buffer)
        print(f"File saved to S3: {filename}")
    except (NoCredentialsError, ClientError) as e:
        print(f"Failed to upload {filename} to S3: {e}")

def load_from_s3(filename, bucket_name=None):
    """
    Loads a CSV file from S3 into a pandas DataFrame.
    """
    if bucket_name is None:
        bucket_name = st.secrets["BUCKET_NAME"]

    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=filename)
        df = pd.read_csv(response['Body'])
        print(f"Loaded file from S3: {filename}")
        return df
    except ClientError as e:
        print(f"File not found in S3: {filename}")
        return pd.DataFrame()
