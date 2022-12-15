from datetime import datetime

from pynamodb.attributes import (
    BooleanAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model


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
