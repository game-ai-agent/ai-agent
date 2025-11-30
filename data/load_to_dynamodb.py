"""
Kaggle Steam 게임 데이터를 DynamoDB에 로드하는 스크립트

실행 방법:
1. Kaggle에서 games.json 다운로드
2. data/ 디렉토리에 games.json 배치
3. python data/load_to_dynamodb.py 실행
"""
import boto3
import pandas as pd
import json
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# DynamoDB 설정 (서울 리전)
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
TABLE_NAME = 'GameMetadata'


def create_table():
    """DynamoDB 테이블 생성"""
    try:
        # 기존 테이블 확인
        existing_tables = [table.name for table in dynamodb.tables.all()]

        if TABLE_NAME in existing_tables:
            print(f"테이블 '{TABLE_NAME}'이 이미 존재합니다.")
            response = input("기존 테이블을 삭제하고 다시 만드시겠습니까? (y/N): ")
            if response.lower() == 'y':
                table = dynamodb.Table(TABLE_NAME)
                table.delete()
                print("기존 테이블 삭제 중...")
                table.wait_until_not_exists()
                print("삭제 완료!")
            else:
                return dynamodb.Table(TABLE_NAME)

        # 새 테이블 생성
        print(f"테이블 '{TABLE_NAME}' 생성 중...")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'app_id', 'KeyType': 'HASH'}  # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'app_id', 'AttributeType': 'S'}  # String
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand 과금 (예상 못한 큰 비용 방지)
        )

        # 테이블 생성 대기
        table.wait_until_exists()
        print(f" 테이블 '{TABLE_NAME}' 생성 완료!")
        return table

    except Exception as e:
        print(f" 테이블 생성 오류: {e}")
        raise


def load_data_from_json(file_path='data/games.json'):
    """Kaggle JSON 데이터 로드"""
    try:
        print(f"\n데이터 파일 '{file_path}' 로드 중...")

        # JSON 읽기 (dict 구조)
        df = pd.read_json(file_path)

        # JSON 최상위 key(appid)를 index가 아니라 컬럼으로 만들기
        df.index.name = "appid"
        df.reset_index(inplace=True)

        print(f" {len(df)} 개 게임 데이터 로드 완료!")
        print(f"컬럼: {list(df.columns)}")
        return df

    except FileNotFoundError:
        print(f" 파일을 찾을 수 없습니다: {file_path}")
        print("\nKaggle에서 데이터를 다운로드하세요:")
        print("https://www.kaggle.com/datasets/trolukovich/steam-games-complete-dataset")
        raise
    except Exception as e:
        print(f" 데이터 로드 오류: {e}")
        raise


def upload_to_dynamodb(df, table, batch_size=25):
    """데이터를 DynamoDB에 업로드 (배치 처리)"""
    print(f"\nDynamoDB에 데이터 업로드 중...")

    total_count = 0
    error_count = 0

    # 배치 처리 (DynamoDB는 최대 25개씩 배치 쓰기 가능)
    with table.batch_writer() as batch:
        for idx, game in df.iterrows():
            try:
                # app_id가 없으면 인덱스 기반으로 생성
                app_id = str(game.get('app_id', f"game_{idx}"))

                # DynamoDB 아이템 구성
                item = {
                    'app_id': app_id,
                    'name': str(game.get('name', 'Unknown')),
                    'price': float(game.get('price', 0.0)),
                    'genres': game.get('genres', []) if isinstance(game.get('genres'), list) else [],
                    'categories': game.get('categories', []) if isinstance(game.get('categories'), list) else [],
                    'positive_reviews': int(game.get('positive', 0)),
                    'negative_reviews': int(game.get('negative', 0))
                }

                # tags 처리 (딕셔너리면 키만 추출)
                tags = game.get('tags', {})
                if isinstance(tags, dict):
                    item['tags'] = list(tags.keys())[:10]  # 상위 10개 태그만
                elif isinstance(tags, list):
                    item['tags'] = tags[:10]
                else:
                    item['tags'] = []

                # DynamoDB에 쓰기
                batch.put_item(Item=item)
                total_count += 1

                # 진행 상황 출력
                if total_count % 100 == 0:
                    print(f"  진행: {total_count}/{len(df)} 게임 업로드 완료...")

            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 처음 5개 에러만 출력
                    print(f"  게임 '{game.get('name', 'Unknown')}' 업로드 실패: {e}")

    print(f"\n 업로드 완료!")
    print(f"   성공: {total_count - error_count} 개")
    print(f"   실패: {error_count} 개")
    return total_count - error_count


def verify_upload(table, sample_size=5):
    """업로드된 데이터 검증"""
    print(f"\n데이터 검증 중 (샘플 {sample_size}개)...")

    try:
        response = table.scan(Limit=sample_size)
        items = response.get('Items', [])

        print(f"\n샘플 데이터:")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item.get('name')} - ${item.get('price')} - {item.get('genres')}")

        # 전체 아이템 수 (근사치)
        print(f"\n전체 아이템 수 (근사치): {response.get('Count', 0)}")

    except Exception as e:
        print(f" 검증 오류: {e}")


def main():
    """메인 실행 함수"""
    print("="*60)
    print("Steam 게임 데이터 → DynamoDB 로더")
    print("="*60)

    # 1. 테이블 생성
    table = create_table()

    # 2. 데이터 로드
    df = load_data_from_json()

    # 3. DynamoDB 업로드
    uploaded_count = upload_to_dynamodb(df, table)

    # 4. 검증
    verify_upload(table)

    print("\n" + "="*60)
    print(f" 모든 작업 완료! ({uploaded_count}개 게임 업로드)")
    print("="*60)


if __name__ == "__main__":
    main()
