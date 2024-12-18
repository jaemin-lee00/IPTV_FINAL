
import mysql.connector

def connect_to_db():
    return mysql.connector.connect(
        host='192.168.101.227',
        user='Second',
        password='rkdwlsah12!*',
        database='second_pj',
        port=3306
    )