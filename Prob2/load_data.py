import boto3
import json, sys, os, datetime, re, collections
import time
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/getting-started-step-1.html
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html#GSI.scenario



# denormalize for efficient retrieval


processing=[]
def time_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace('+00:00', 'Z')


STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'can', 'this', 'that', 'these', 'those', 'we', 'our', 'use', 'using',
    'based', 'approach', 'method', 'paper', 'propose', 'proposed', 'show'
}

partition_key_name= 'Category'; partition_key_type= 'S'
sort_key_name= 'Published'; sort_key_type= 'S'


WORD = re.compile(r"[A-Za-z0-9']+")


def load_papers(path):
    with open(path, 'r', encoding="utf-8") as file:
        data= json.load(file)
        if isinstance(data,dict) and "papers" in data:
            return data["papers"]
        else:
            return data


def top(text,k):
    words = (w.lower() for w in WORD.findall(text or ""))
    cnt = collections.Counter(w for w in words if w not in STOPWORDS and not w.isdigit())
    return [w for w, _ in cnt.most_common(k)]


def en_table(table_name, region= None):
    dynamodb= boto3.resource('dynamodb',region_name=region) if region else boto3.resource('dynamodb')
    try:
        table= dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
        {"AttributeName": partition_key_name,'KeyType':'HASH'},
        {"AttributeName": sort_key_name,'KeyType':'RANGE'},
    ],
        AttributeDefinitions=[
            {'AttributeName': partition_key_name, 'AttributeType': partition_key_type},
            {'AttributeName': sort_key_name,'AttributeType':sort_key_type},
            {'AttributeName': "Author", 'AttributeType':'S'},
            {'AttributeName': "PaperId", 'AttributeType':'S'},
            {'AttributeName': "Keyword", 'AttributeType':'S'},
            {'AttributeName': "Type", 'AttributeType':'S'},
            ],
            BillingMode= "PAY_PER_REQUEST",
            GlobalSecondaryIndexes= [
                {
                    "IndexName": "AuthorIndex",
                    "KeySchema": [
                        {"AttributeName":"Author", "KeyType":"HASH"},
                        {"AttributeName":"PaperId","KeyType":"RANGE"},
                    ],
                    "Projection": {"ProjectionType":"ALL"},
                },
                {
                    "IndexName": "PaperIdIndex",
                    "KeySchema": [
                        {"AttributeName": "PaperId", "KeyType":"HASH"},
                        {"AttributeName": "Type", "KeyType": "RANGE"},
                        ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                "IndexName": "KeywordIndex",
                "KeySchema": [
                    {"AttributeName": "Keyword", "KeyType": "HASH"},
                    {"AttributeName": "PaperId", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                },
            ],
    )
        time.sleep(20)
        processing.append(f"[{time_now()}] table created")
        return table
    except Exception:
        table= boto3.resource('dynamodb', region_name=region).Table(table_name) if region else boto3.resource('dynamodb').Table(table_name)
        time.sleep(20)
        processing.append(f"[{time_now()}] no new table")
        return table


def get_info(p):
    paperid= p.get("arxiv_id")
    title= p.get("title","")
    abstract= p.get("abstract","")
    categ= p.get("categories") or []
    if isinstance(categ, str): ##for mult cat
        categ= categ.split()
    authors= p.get("authors") or []
    publish= str(p.get("published") or "")
    update= p.get("updated","")

    wo= top(abstract,k=10)
    date_part= publish.split("T", 1)[0] or publish
    pid_tag= f"PID#{paperid}"
    items= []
    for c in (categ or ["uncategorized"]):
        pk= f"CATEGORY#{c}"
        sk= f"{date_part}#{pid_tag}"
        items.append({
            "Category": pk,
            "Published": sk,
            "Type":"Paper",
            "PaperId": pid_tag,
            "Title": title,
            "Abstract": abstract,
            "Authors":authors,
            "Categories": categ,
            "Keywords": wo,
            "Updated": update,
            "AbstractStats": p.get("abstract_stats"),
        })


    first_cat = (categ[0] if categ else "uncategorized")
    first_pk= f"CATEGORY#{first_cat}"
    for a in authors:
        items.append({
            "Category": first_pk,
            "Published": f"{date_part}#{a}#{pid_tag}",
            "Type": "Author",
            "Author": a,
            "PaperId": pid_tag,
            "Title": title,
        })

    for i in wo:
        items.append({
            "Category": first_pk,
            "Published": f"{date_part}#{i}#{pid_tag}",
            "Type": "Keyword",
            "Keyword": i,
            "PaperId": pid_tag,
            "Title": title,
        })

    return items



def ptd(path,region):
    papers = load_papers(path)
    processing.append(f"[{time_now()}] loaded {len(papers)} papers from {path}")
    table = en_table(table_name, region=region)
    all_items = []
    cat_n,auth_n,kw_n= 0,0,0
    for p in papers:
        its = get_info(p)
        all_items.extend(its)
        cats = p.get("categories") or []
        cat_n += (len(cats) or 1)
        auth_n += len(p.get("authors") or [])
        kw_n   += len(top(p.get("abstract", "") or "", 10))
    processing.append(f"[{time_now()}]writing {len(all_items)}items...")
    with table.batch_writer(overwrite_by_pkeys=["Category","Published"]) as b:
        for it in all_items:
            b.put_item(Item=it)
    total = len(all_items)
    n_p   = max(1, len(papers))
    processing.append(f"[{time_now()}]created{total} items(denormalized)")
    processing.append(f"[{time_now()}]factor:{total / n_p:.1f}x")
    processing.append(f"[{time_now()}]breakdown: Category items={cat_n}, Author={auth_n}, Keyword items={kw_n}")



paper_path= sys.argv[1]
table_name= sys.argv[2]
region= None
if len(sys.argv) >=5 and sys.argv[3] == "--region":
    region= sys.argv[4]

ptd(paper_path,region)

print("\n".join(processing))
