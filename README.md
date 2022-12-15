# PynamoDB 入門

## PynamoDB とは

> PynamoDB is a Pythonic interface to Amazon’s DynamoDB. By using simple, yet powerful abstractions over the DynamoDB API, PynamoDB allows you to start developing immediately.  
> (PynamoDB は、Amazon の DynamoDB に対する Pythonic なインターフェースです。DynamoDB の API をシンプルかつ強力に抽象化することで、PynamoDB はすぐに開発を開始することができます。)  
> 引用: https://pynamodb.readthedocs.io/en/stable/

ざっくり言うと DynamoDB アクセス用の Python 製 [ORM](https://codezine.jp/article/detail/5858) です。  
機能が多いのでポイントとなる機能を中心にかいつまんで解説します。

## 簡単な例

以下の社員を管理するテーブル の登録、データの取得を例にします。

| 項目名           | データ型 | 備考                                           |
| ---------------- | -------- | ---------------------------------------------- |
| employee_no (PK) | Number   | 社員番号                                       |
| name             | String   | 名前                                           |
| joined_on        | String   | 入社日 (DynamoDB は日付型がないので String で) |
| is_byod          | Boolean  | BYOD してるか否か                              |

### インストール

pip でインストール可能。

```sh
$ pip install pynamodb
```

### サンプルコード

```python
# getting_started.py

from datetime import datetime

from pynamodb.attributes import (
    BooleanAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model


# モデルの定義
class Employee(Model):
    """社員テーブル"""

    class Meta:
        table_name = "employees"
        # 明示的に指定が必要（デフォルトはバージニア）
        region = "ap-northeast-1"

    # 社員番号
    employee_no = NumberAttribute(hash_key=True)
    # 名前
    name = UnicodeAttribute()
    # 入社日
    joined_on = UTCDateTimeAttribute(null=True)
    # BYOD
    is_byod = BooleanAttribute(default=False)


# テーブルの作成
Employee.create_table(wait=True, billing_mode="PAY_PER_REQUEST")

# 社員オブジェクトの生成
t3yamoto = Employee(
    19079,
    name="t3yamoto",
    joined_on=datetime(2020, 1, 1),
    is_byod=True,
)

# DynamoDB テーブルへ登録
t3yamoto.save()

# 登録したデータを取得してプリント
print(Employee.get(19079).__dict__)
```

```sh
$ python getting_started.py
{'attribute_values': {'is_byod': True, 'joined_on': datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), 'name': 't3yamoto', 'no': 19079}}
```

### boto3 でやると...

```python
# getting_started_boto3.py

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
```

```sh
$ python getting_started_boto3.py
{'employee_no': {'N': '19079'}, 'name': {'S': 't3yamoto'}, 'is_byod': {'BOOL': True}, 'joined_on': {'S': '2020-01-01T00:00:00'}}
```

## PynamoDB を使うメリット

### モデルを定義することで、テーブルに格納される項目が明確になる

- boto3 の場合は put_item する度に項目名を指定するため、typo があっても気が付かない (エラーにならず登録される)
- PynamoDB の場合はモデルに定義されていない項目は指定できない
- 単純にコードの見通しも良い

### モデルは Python のクラスなので、メソッドを生やせる

例えば、前述の社員テーブルの例で、当該社員の勤続日数を求めたい場合は以下のようにメソッドを追加すれば良い。

```python

class Employee(Model):
    """社員テーブル"""

    class Meta:
        table_name = "employees"
        # 明示的に指定が必要（デフォルトはバージニア）
        region = "ap-northeast-1"

    # 社員番号
    employee_no = NumberAttribute(hash_key=True)
    # 名前
    name = UnicodeAttribute()
    # 入社日
    joined_on = UTCDateTimeAttribute(null=True)
    # BYOD
    is_byod = BooleanAttribute(default=False)

    def get_length_of_service_in_days(self, d: datetime) -> int:
        """指定された日付時点の勤続日数を返します"""
        return (d - self.joined_on).days


# 社員オブジェクトの生成
t3yamoto = Employee(
    19079,
    name="t3yamoto",
    joined_on=datetime(2020, 1, 1),
    is_byod=True,
)

# 勤務日数をプリント
print(t3yamoto.get_length_of_service_in_days(datetime(2022, 12, 15)))
```

```sh
$ python getting_started_length_of_service.py
1079
```

### カスタム属性でよりコードを堅牢、メンテナンスしやすく

#### 基本的な属性

PynamoDB で用意されている属性は以下の通りです。

| 属性                 | 対応する DynamoDB データ型 | 対応する Python データ型 | 備考 |
| -------------------- | -------------------------- | ------------------------ | ---- |
| UnicodeAttribute     | String                     | str                      |      |
| UnicodeSetAttribute  | Sets(String)               | set[str]                 |      |
| NumberAttribute      | Number                     | Decimal                  |      |
| NumberSetAttribute   | Sets(Number)               | set[Decimal]             |      |
| BinaryAttribute      | Binary                     | Binary                   |      |
| BinarySetAttribute   | Sets(Binary)               | set[Binary]              |      |
| UTCDateTimeAttribute | String                     | datetime.datetime        |      |
| BooleanAttribute     | Boolean                    | bool                     |      |
| JSONAttribute        | String                     | dict                     |      |
| MapAttribute         | Map                        | dict                     |      |
| ListAttribute        | List                       | list                     |      |
| VersionAttribute     | Number                     | int                      | \*1  |
| TTLAttribute         | Number                     | datetime.datetime        |      |

\*1. テーブルの楽観ロック用。バージョン番号を自動で管理してくれて、条件付き書き込みでバージョンが変わっていないことを保証する

- 参考
  - https://pynamodb.readthedocs.io/en/stable/tutorial.html#defining-model-attributes
  - https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html#HowItWorks.DataTypes
  - https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/dynamodb/types.html
  - https://pynamodb.readthedocs.io/en/stable/optimistic_locking.html?highlight=VersionAttribute#version-attribute

##### 属性に設定可能なオプション

属性によって異なるため `UnicodeAttribute` を例に基本的なオプションを解説します。

| option 名       | 説明                                                        |
| --------------- | ----------------------------------------------------------- |
| hash_key        | True or False で設定 hash_key, range_key はどちらかのみ指定 |
| range_key       | True or False で設定 hash_key, range_key はどちらかのみ指定 |
| null            | True or False で設定 True なら null を許可                  |
| default         | 未設定の場合のデフォルト値                                  |
| default_for_new | 未設定の場合のデフォルト値 (新規登録時のみ)                 |
| attr_name       | DynamoDB 属性名 (指定しない場合はモデルに定義した変数名)    |

```python

class Sample(Model):
    class Meta:
        table_name = "sample"

    foo = UnicodeAttribute(hash_key=True)
    bar = UnicodeAttribute(range_key=True)
    baz = UnicodeAttribute(null=True, default="baz_value", attr_name="Baz")

```

#### カスタム属性

ユーザー独自の属性を定義することができる。以下の例は項目「役職」を管理するためのカスタム属性を管理する例。

```python
# custom_attribute.py

# import は省略

class Role(Enum):
    """役職"""

    # 一般社員
    MEMBER = "1"
    # マネージャー
    MANAGER = "2"


class RoleAttribute(UnicodeAttribute):
    """役職を DynamoDB で管理するためのカスタム属性
    serialize, deserialize メソッドを実装する必要がある
    """

    def serialize(self, role: Role) -> str:
        """
        Role(モデルで保持するデータ型) ---serialize---> str(DynamoDB に格納する際のデータ型)
        """
        return role.value

    def deserialize(self, value: str) -> Role:
        """
        Role(モデルで保持するデータ型) <---deserialize--- str(DynamoDB に格納する際のデータ型)
        """
        return Role(value)


class Employee(Model):
    """社員テーブル"""

    class Meta:
        table_name = "employees"
        # 明示的に指定が必要（デフォルトはバージニア）
        region = "ap-northeast-1"

    # 社員番号
    employee_no = NumberAttribute(hash_key=True)
    # 名前
    name = UnicodeAttribute()
    # 入社日
    joined_on = UTCDateTimeAttribute(null=True)
    # BYOD
    is_byod = BooleanAttribute(default=False)
    # 役職
    role = RoleAttribute()


# 社員オブジェクトの生成・DynamoDB に登録
t3yamoto = Employee(
    19079,
    name="t3yamoto",
    joined_on=datetime(2020, 1, 1),
    is_byod=True,
    role=Role.MEMBER,
).save()

# DynamoDB から取得してプリント
print(Employee.get(19079).role)

```

```sh
$ python custom_attribute.py
Role.MEMBER
```

カスタム属性を作成・使用することで、コードの可読性向上や、間違った値が入らない（堅牢性）の向上などが見込める。

### クエリが楽

#### GSI の定義

- https://pynamodb.readthedocs.io/en/latest/indexes.html

```python
# query.py

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
```

#### Query 方法

部署="AS", 入社日が 2020/1/2 以降, BYOD=True の社員をクエリしたい場合の例

```python
# query.py

# 社員オブジェクトの生成・DynamoDB に登録
# fmt:off
taro = Employee(1, name="taro", joined_on=datetime(2020, 1, 1), department="AS", is_byod=True).save()
jiro = Employee(2, name="jiro", joined_on=datetime(2020, 1, 2), department="AS", is_byod=True).save()
saburo = Employee(3, name="saburo", joined_on=datetime(2020, 1, 3), department="AS", is_byod=False).save()
shiro = Employee(4, name="shiro", joined_on=datetime(2020, 1, 4), department="AS", is_byod=True).save()
goro = Employee(5, name="goro", joined_on=datetime(2020, 1, 5), department="CI").save()
# fmt:on


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

```

## まとめ

- モデルを定義することでテーブルに格納する項目が明確に
  - スキーマレスな使い方をする場合はこのメリットはなさそう
- カスタム属性で快適・堅牢にコーディング
- クエリーも簡単に書ける
- まだまだ機能はあるのでこの先は [公式ドキュメント](https://pynamodb.readthedocs.io/en/latest/index.html) へ
