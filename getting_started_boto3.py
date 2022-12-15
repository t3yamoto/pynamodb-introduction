import time
from datetime import datetime

import boto3

client = boto3.client("dynamodb")

# テーブルの作成
client.create_table(
    TableName="employees_boto3",
    BillingMode="PAY_PER_REQUEST",
    AttributeDefinitions=[
        {"AttributeName": "employee_no", "AttributeType": "N"},
    ],
    KeySchema=[
        {"AttributeName": "employee_no", "KeyType": "HASH"},
    ],
)

time.sleep(10)

# DynamoDB テーブルへ登録
client.put_item(
    TableName="employees_boto3",
    Item={
        "employee_no": {"N": "19079"},
        "name": {"S": "t3yamoto"},
        "joined_on": {
            "S": datetime(2020, 1, 1).isoformat(),
        },
        "is_byod": {"BOOL": True},
    },
)

# 登録したデータを取得してプリント
res = client.get_item(
    TableName="employees_boto3", Key={"employee_no": {"N": "19079"}}
)
print(res["Item"])
