from datetime import datetime, timezone

from pynamodb.attributes import (
    BooleanAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model


class SampleGSI(GlobalSecondaryIndex):
    """GSI"""

    class Meta:
        # インデックス名
        index_name = "sample-gsi"
        # 射影属性
        projection = AllProjection()

    department = UnicodeAttribute(hash_key=True)
    joined_on = UTCDateTimeAttribute(range_key=True)


class Employee(Model):
    """社員テーブル"""

    class Meta:
        table_name = "employees2"
        # 明示的に指定が必要（デフォルトはバージニア）
        region = "ap-northeast-1"

    # 社員番号
    employee_no = NumberAttribute(hash_key=True)
    # 名前
    name = UnicodeAttribute()
    # 入社日
    joined_on = UTCDateTimeAttribute()
    # BYOD
    is_byod = BooleanAttribute(default=False)
    # 部署
    department = UnicodeAttribute()

    # GSI の定義
    sample_gsi = SampleGSI()


# テーブルの作成
if not Employee.exists():
    Employee.create_table(wait=True, billing_mode="PAY_PER_REQUEST")

# 社員オブジェクトの生成・DynamoDB に登録
# fmt:off
taro = Employee(1, name="taro", joined_on=datetime(2020, 1, 1), department="AS", is_byod=True).save()
jiro = Employee(2, name="jiro", joined_on=datetime(2020, 1, 2), department="AS", is_byod=True).save()
saburo = Employee(3, name="saburo", joined_on=datetime(2020, 1, 3), department="AS", is_byod=False).save()
shiro = Employee(4, name="shiro", joined_on=datetime(2020, 1, 4), department="AS", is_byod=True).save()
goro = Employee(5, name="goro", joined_on=datetime(2020, 1, 5), department="CI").save()
# fmt:on

# 部署="AS", 入社日が 2020/1/2 以降, BYOD=True の社員をクエリ

## PynamoDB の場合
result_iterator = Employee.sample_gsi.query(
    hash_key="AS",
    range_key_condition=Employee.joined_on >= datetime(2020, 1, 2),
    filter_condition=Employee.is_byod == True,
)

for employee in result_iterator:
    print(employee)
# employees2<2>
# employees2<4>

## boto3 の場合
import boto3

client = boto3.client("dynamodb")
pagenator = client.get_paginator("query")

response_iterator = pagenator.paginate(
    TableName="employees2",
    IndexName="sample-gsi",
    KeyConditionExpression="department = :department AND joined_on >= :joined_on",
    FilterExpression="is_byod = :is_byod",
    ExpressionAttributeValues={
        ":department": {"S": "AS"},
        ":joined_on": {
            "S": datetime(2020, 1, 2, tzinfo=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        },
        ":is_byod": {"BOOL": True},
    },
)

for page in response_iterator:
    for employee in page["Items"]:
        print(employee)
# {'department': {'S': 'AS'}, 'employee_no': {'N': '2'}, 'is_byod': {'BOOL': True}, 'name': {'S': 'jiro'}, 'joined_on': {'S': '2020-01-02T00:00:00.000000+0000'}}
# {'department': {'S': 'AS'}, 'employee_no': {'N': '4'}, 'is_byod': {'BOOL': True}, 'name': {'S': 'shiro'}, 'joined_on': {'S': '2020-01-04T00:00:00.000000+0000'}}
