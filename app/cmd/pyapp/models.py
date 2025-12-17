#from sqlite3 import Date
from sqlalchemy import Boolean, Column, ForeignKey, Numeric, Float, Integer, String, types, func, DateTime, Date
from sqlalchemy.orm import relationship
from . import db_base
import json


# Global Defaults

DB_T_TYPE_DEBIT_NORMAL = "Debit Normal"
DB_T_TYPE_CREDIT_NORMAL = "Credit Normal"
DB_T_TYPE_DEBIT_ABNORMAL = "Debit Abnormal"
DB_T_TYPE_CREDIT_ABNORMAL = "Credit Adnormal"

UNDEFINED_DEBIT = "Undefined Debit"
UNDEFINED_CREDIT = "Undefined Credit"


# from sqlalchemy.types import TypeDecorator, DATETIME

# class _EnhDateTime(datetime):

#     def foo(self):
#         return 'foo'

# class EnhDateTime(TypeDecorator):

#     impl = DATETIME

#     def process_result_value(self, value, dialect):
#         if value is not None:
#             value = _EnhDateTime(
#                 value.year, value.month, value.day, value.hour, value.minute,
#                 value.second, value.microsecond, value.tzinfo
#             )
#         return value

def toSeconds(value):
    if type(value) == str:
        value = value.replace("mins", "")
    valueNew = int(value) * 60
    return valueNew

# class CastToPercentageType(types.TypeDecorator):
#     impl = types.Numeric
#     def column_expression(self, col):
#         return func.cast(col, Integer)
  
    # def bind_expression(self,col):
    #     return func.cast(col, String)

class ClientTransaction(db_base.Base):
    __tablename__ = "client_transaction"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    description = Column(String)
    amount = Column(Float)
    class_id = Column(Integer)
    source_id = Column(Integer, ForeignKey('client_transaction_source.id'))

# class ClientTransactionToClass(db_base.Base):
#     __tablename__ = "client_transaction_to_class"

#     id = Column(Integer, primary_key=True, index=True)
#     transaction_id = Column(Integer, ForeignKey('client_transaction.id'))
#     class_id = Column(Integer, ForeignKey('client_transaction_class.id'))

class ClientTransactionClass(db_base.Base):
    __tablename__ = "client_transaction_class"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    group_id = Column(Integer, ForeignKey('client_transaction_group.id'))
    type_id = Column(Integer, ForeignKey('client_transaction_type.id'))

class ClientTransactionGroup(db_base.Base):
    __tablename__ = "client_transaction_group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class ClientTransactionType(db_base.Base):
    __tablename__ = "client_transaction_type"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    hidden = Column(Boolean)

class ClientTransactionSource(db_base.Base):
    __tablename__ = "client_transaction_source"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    client_id = Column(Integer, ForeignKey('client.id'))

class ClientTransactionSourceFile(db_base.Base):
    __tablename__ = "client_transaction_source_file"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    data_hash = Column(String)
    client_id = Column(Integer, ForeignKey('client.id'))

class Client(db_base.Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    password_hashed = Column(String)
    type = Column(String)

