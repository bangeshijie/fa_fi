# class Student:
#     school_name = "第一中学"
#
#     def __init__(self, value):
#         self.instance_attr = value  # 实例属性
#
#     @classmethod
#     def change_school(cls, new_name):
#         # cls 就是 Student 这个类
#         cls.school_name = new_name
#         cls.instance_attr = "new_value"
#         print(f"{cls.school_name} 的学校名称已修改为 {new_name}")
#
# s1=Student("1小")
# s2=Student("2小")
# s1.change_school("第2中学")
# print(s1.school_name)
# print(s2.school_name)
# print(Student.school_name)
#
# print(s1.instance_attr)
# print(s2.instance_attr)
# s1.change_school("第1小学")

#
# class Person:
#     def __init__(self, name: str):
#         self.name = name
#
#
# def get_person_name(one_person: Person):
#     return one_person.name

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = "John Doe"
    signup_ts: datetime | None = None
    friends: list[int] = []


external_data = {
    "id": "123",
    "signup_ts": "2017-06-01 12:22",
    "friends": [1, "2", b"3"],
}
user = User(**external_data)
print(user)
# > User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]
print(user.id)
# > 123
