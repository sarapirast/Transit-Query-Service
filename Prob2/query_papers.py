import sys, json, time, datetime, re, collections
import boto3
from boto3.dynamodb.conditions import Key


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

def get_table(table_name, region=None):
    ddb =boto3.resource("dynamodb", region_name=region) if region else boto3.resource("dynamodb")
    return ddb.Table(table_name)

def publish(it):
    if "published" in it:
        return it["published"]
    sk= it.get("Published") or it.get("SK") or ""
    return sk.split("#",1)[0] if sk else ""


def query_recent_in_category(table_name, category, limit=20):
    """
    Query 1: Browse recent papers in category.
    Uses: Main table partition key query with sort key descending.
    """
    response = dynamodb.Table(table_name).query(
        KeyConditionExpression=Key('PK').eq(f'CATEGORY#{category}'),
        ScanIndexForward=False,
        Limit=limit
    )
    return response['Items']

def query_papers_by_author(table_name, author_name):
    """
    Query 2: Find all papers by author.
    Uses: GSI1 (AuthorIndex) partition key query.
    """
    response = dynamodb.Table(table_name).query(
        IndexName='AuthorIndex',
        KeyConditionExpression=Key('GSI1PK').eq(f'AUTHOR#{author_name}')
    )
    return response['Items']

def get_paper_by_id(table_name, arxiv_id):
    """
    Query 3: Get specific paper by ID.
    Uses: GSI2 (PaperIdIndex) for direct lookup.
    """
    response = dynamodb.Table(table_name).query(
        IndexName='PaperIdIndex',
        KeyConditionExpression=Key('GSI2PK').eq(f'PAPER#{arxiv_id}')
    )
    return response['Items'][0] if response['Items'] else None

def query_papers_in_date_range(table_name, category, start_date, end_date):
    """
    Query 4: Papers in category within date range.
    Uses: Main table with composite sort key range query.
    """
    response = dynamodb.Table(table_name).query(
        KeyConditionExpression=(
            Key('PK').eq(f'CATEGORY#{category}') &
            Key('SK').between(f'{start_date}#', f'{end_date}#zzzzzzz')
        )
    )
    return response['Items']

def query_papers_by_keyword(table_name, keyword, limit=20):
    """
    Query 5: Papers containing keyword.
    Uses: GSI3 (KeywordIndex) partition key query.
    """
    response = dynamodb.Table(table_name).query(
        IndexName='KeywordIndex',
        KeyConditionExpression=Key('GSI3PK').eq(f'KEYWORD#{keyword.lower()}'),
        ScanIndexForward=False,
        Limit=limit
    )
    return response['Items']