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
