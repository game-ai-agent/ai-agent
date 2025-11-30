"""
DynamoDB 기반 게임 메타데이터 필터링 도구
정확한 조건 필터링 (가격, 장르, 멀티플레이어 등)
"""
from strands import tool
import boto3
from boto3.dynamodb.conditions import Attr
import os
from decimal import Decimal
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-west-2'))


@tool
def filter_games(
    app_ids: list = None,
    max_price: float = None,
    min_price: float = None,
    genres: list = None,
    must_have_multiplayer: bool = None,
    limit: int = 10
) -> list:
    """DynamoDB에서 게임 메타데이터를 필터링합니다.

    Args:
        app_ids: Vector DB(Bedrock KB)에서 찾은 게임 ID 리스트. 이 ID들 중에서만 필터링
        max_price: 최대 가격 (USD 기준). 예: 20.0
        min_price: 최소 가격 (USD 기준)
        genres: 필수 장르 리스트. 예: ["Puzzle", "Adventure"]
        must_have_multiplayer: 멀티플레이어 필수 여부 (True/False)
        limit: 반환할 최대 게임 수 (기본: 10)

    Returns:
        조건에 맞는 게임 리스트 (가격순 정렬)

    Examples:
        # 2만원 이하 퍼즐 게임
        filter_games(max_price=20.0, genres=["Puzzle"])

        # Vector DB 결과 중 협동 게임만
        filter_games(app_ids=["10", "20", "30"], must_have_multiplayer=True)
    """
    try:
        table = dynamodb.Table('GameMetadata')

        # 필터 조건 구성
        filter_expr = None

        # app_ids로 필터링 (Vector DB 결과와 교차 검증)
        if app_ids and len(app_ids) > 0:
            # DynamoDB의 IN 연산은 100개 제한이 있으므로 batch로 처리
            filter_expr = Attr('app_id').is_in(app_ids[:100])

        # 가격 필터 (float → Decimal 변환)
        if max_price is not None:
            price_filter = Attr('price').lte(Decimal(str(max_price)))
            filter_expr = filter_expr & price_filter if filter_expr else price_filter

        if min_price is not None:
            price_filter = Attr('price').gte(Decimal(str(min_price)))
            filter_expr = filter_expr & price_filter if filter_expr else price_filter

        # 장르 필터 (모든 장르를 포함해야 함)
        if genres:
            for genre in genres:
                genre_filter = Attr('genres').contains(genre)
                filter_expr = filter_expr & genre_filter if filter_expr else genre_filter

        # 멀티플레이어 필터
        if must_have_multiplayer:
            mp_filter = Attr('categories').contains('Multi-player')
            filter_expr = filter_expr & mp_filter if filter_expr else mp_filter

        # DynamoDB 검색 실행
        if filter_expr:
            response = table.scan(FilterExpression=filter_expr, Limit=limit * 2)
        else:
            response = table.scan(Limit=limit * 2)

        games = response['Items']

        # 가격순 정렬 (낮은 가격 우선, Decimal 처리)
        games.sort(key=lambda x: float(x.get('price', Decimal('999999'))))

        # Decimal을 float로 변환 (JSON 직렬화를 위해)
        for game in games:
            if 'price' in game:
                game['price'] = float(game['price'])
            # 다른 숫자 필드도 변환
            for key in ['positive', 'negative', 'metacritic_score']:
                if key in game and isinstance(game[key], Decimal):
                    game[key] = int(game[key]) if game[key] % 1 == 0 else float(game[key])

        # 상위 N개만 반환
        return games[:limit]

    except Exception as e:
        print(f"DynamoDB 필터링 오류: {e}")
        return []


@tool
def get_game_by_id(app_id: str) -> dict:
    """app_id로 특정 게임의 상세 정보를 가져옵니다.

    Args:
        app_id: 게임 ID

    Returns:
        게임 상세 정보 딕셔너리
    """
    try:
        table = dynamodb.Table('GameMetadata')
        response = table.get_item(Key={'app_id': app_id})
        game = response.get('Item', {})

        # Decimal을 float/int로 변환
        if game:
            if 'price' in game:
                game['price'] = float(game['price'])
            for key in ['positive', 'negative', 'metacritic_score']:
                if key in game and isinstance(game[key], Decimal):
                    game[key] = int(game[key]) if game[key] % 1 == 0 else float(game[key])

        return game
    except Exception as e:
        print(f"게임 조회 오류: {e}")
        return {}
