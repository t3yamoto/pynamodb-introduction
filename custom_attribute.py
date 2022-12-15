from datetime import datetime
from enum import Enum

from pynamodb.attributes import (
    BooleanAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model


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
