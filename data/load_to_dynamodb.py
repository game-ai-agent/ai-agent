"""
대용량 Kaggle Steam 게임 데이터를 DynamoDB에 로드하는 스크립트
- pandas 제거
- ijson 기반 스트리밍 파서 적용 (10GB 파일 대응)
- DynamoDB batch_writer 로 대량 업로드
"""

import boto3
import json
import os
from dotenv import load_dotenv
from decimal import Decimal
import ijson

# 환경 변수 로드
load_dotenv()

# AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
TABLE_NAME = "GameMetadata"


def create_table():
    """DynamoDB 테이블 생성"""
    existing_tables = [t.name for t in dynamodb.tables.all()]

    if TABLE_NAME in existing_tables:
        print(f"테이블 '{TABLE_NAME}'이 이미 존재합니다.")
        return dynamodb.Table(TABLE_NAME)

    print(f"테이블 '{TABLE_NAME}' 생성 중...")

    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "app_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "app_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()

    print("테이블 생성 완료!")
    return table


def convert_floats_to_decimal(obj):
    """재귀적으로 float → Decimal 변환"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    else:
        return obj


def stream_json_games(file_path):
    """10GB dict-of-dicts JSON을 스트리밍으로 읽기"""
    print(f"스트리밍 로드 시작: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        parser = ijson.items(f, "")
        data = next(parser)  # 최상위 dict

        for appid, game in data.items():
            game = convert_floats_to_decimal(game)
            game["app_id"] = str(appid)
            yield game


def upload_stream_to_dynamodb(stream, table):
    """스트리밍된 데이터를 DynamoDB로 업로드"""
    print("\nDynamoDB 업로드 시작..")
    count = 0

    with table.batch_writer() as batch:
        for item in stream:
            try:
                batch.put_item(Item=item)
                count += 1

                if count % 1000 == 0:
                    print(f"  진행: {count}개 업로드 완료")

            except Exception as e:
                print(f"업로드 실패: {e}")

    print(f"\n업로드 완료! 총 {count}개 업로드됨.")
    return count


def main():
    print("=" * 60)
    print(" Steam JSON → DynamoDB 로더 (Streaming 기반)")
    print("=" * 60)

    table = create_table()

    stream = stream_json_games("data/games.json")
    uploaded = upload_stream_to_dynamodb(stream, table)

    print("=" * 60)
    print(f" 전체 업로드 완료: {uploaded} 개")
    print("=" * 60)


if __name__ == "__main__":
    main()
