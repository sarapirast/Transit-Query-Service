import psycopg2
import json, sys, os, csv, datetime, argparse
import decimal



def _json_default(o):
    if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
        return o.isoformat()
    if isinstance(o, decimal.Decimal):
        return float(o)
    return str(o)


def Q1():
# -- Output: stop_name, sequence, time_offset
    query= "Q1"
    desc= "List all stops on Route 20 in order"
    inf= """SELECT s.stop_name, ls.sequence_number, ls.time_offset_minutes AS time_offset
        FROM line_stops ls
        JOIN lines l ON l.line_id= ls.line_id
        JOIN stops s ON s.stop_id= ls.stop_id
        WHERE l.line_name = %s  
        ORDER BY ls.sequence_number"""
    param= ("Route 20",) ##tuple
    return query,desc,inf,param

def Q2():
    # -- Output: trip_id, line_name, scheduled_departure
    query= "Q2"
    desc= " Trips during morning rush (7-9 AM)"
    inf= """SELECT t.trip_id, l.line_name, t.scheduled_departure
            FROM trips t
            JOIN lines l ON l.line_id = t.line_id
            WHERE (t.scheduled_departure::time) >= TIME '07:00'
            AND (t.scheduled_departure::time) <  TIME '09:00'
            ORDER BY t.scheduled_departure, t.trip_id"""
    param= ()
    return query,desc,inf,param

def Q3():
    # -- Output: stop_name, line_count
    # -- Uses: GROUP BY, HAVING
    query= "Q3"
    desc= "Transfer stops (stops on 2+ routes)"
    inf= """SELECT s.stop_name,
            COUNT(DISTINCT l.line_id) AS line_count
            FROM line_stops ls
            JOIN stops s ON s.stop_id = ls.stop_id
            JOIN lines l ON l.line_id = ls.line_id
            GROUP BY s.stop_name
            HAVING COUNT(DISTINCT l.line_id) >= 2
            ORDER BY line_count DESC, s.stop_name"""
    param= ()
    return query,desc,inf,param


def Q4():
    #-- Output: All stops for specific trip in order
    #-- Multi-table JOIN
    query= "Q4"
    desc= "Complete route for trip T0001"
    inf="""SELECT s.stop_name,
           ls.sequence_number AS sequence,
           ls.time_offset_minutes AS time_offset
           FROM trips t
           JOIN line_stops ls ON ls.line_id = t.line_id
           JOIN stops s ON s.stop_id  = ls.stop_id
           WHERE t.trip_id = %s
           ORDER BY ls.sequence_number"""
    param= ("T0001",) #tuple
    return query,desc,inf,param
def Q5():
    # -- Output: line_name
    query= "Q5"
    desc= "Routes serving both Wilshire / Veteran and Le Conte / Broxton"
    inf="""SELECT l.line_name
    FROM line_stops ls
    JOIN lines l ON l.line_id= ls.line_id
    JOIN stops s ON s.stop_id= ls.stop_id
    WHERE s.stop_name IN ('Wilshire / Veteran', 'Le Conte / Broxton')
    GROUP BY l.line_name
    HAVING COUNT(DISTINCT s.stop_name) = 2
    ORDER BY l.line_name"""
    param=()
    return query,desc,inf,param
def Q6():
    # -- Output: line_name, avg_passengers
    # -- Aggregation across stop_events
    query= "Q6"
    desc= "Average ridership by line"
    inf= """SELECT l.line_name,
    AVG(se.passengers_on + se.passengers_off)::FLOAT AS avg_passengers
    FROM stop_events se
    JOIN trips t ON t.trip_id = se.trip_id
    JOIN lines l ON l.line_id = t.line_id
    GROUP BY l.line_name
    ORDER BY avg_passengers DESC, l.line_name"""
    param=()
    return query,desc,inf,param
def Q7():
    # -- Output: stop_name, total_activity
    # -- total_activity = SUM(passengers_on + passengers_off)   
    query= "Q7"
    desc= "Top 10 busiest stops"
    inf= """SELECT s.stop_name,
    SUM(se.passengers_on + se.passengers_off) AS total_activity
    FROM stop_events se
    JOIN stops s ON s.stop_id = se.stop_id
    GROUP BY s.stop_name
    ORDER BY total_activity DESC, s.stop_name
    LIMIT 10"""
    param=()
    return query,desc,inf,param
def Q8():
    # -- Output: line_name, delay_count
    # -- WHERE actual > scheduled + interval '2 minutes'
    query= "Q8"
    desc= "Count delays by line (>2 min late)"
    inf= """SELECT l.line_name,
    COUNT(*) AS delay_count
    FROM stop_events se
    JOIN trips t ON t.trip_id = se.trip_id
    JOIN lines l ON l.line_id = t.line_id
    WHERE se.actual_time > se.scheduled_time + INTERVAL '2 minutes'
    GROUP BY l.line_name
    ORDER BY delay_count DESC, l.line_name"""
    param=()
    return query,desc,inf,param
def Q9():
    #-- Output: trip_id, delayed_stop_count
    # -- Uses: Subquery or HAVING
    query= "Q9"
    desc= "Trips with 3+ delayed stops"
    inf= """SELECT t.trip_id,
    COUNT(*) AS delayed_stop_count
    FROM stop_events se
    JOIN trips t ON t.trip_id = se.trip_id
    WHERE se.actual_time > se.scheduled_time + INTERVAL '2 minutes'
    GROUP BY t.trip_id
    HAVING COUNT(*) >= 3
    ORDER BY delayed_stop_count DESC, t.trip_id"""
    param=()
    return query,desc,inf,param
def Q10():
    #-- Output: stop_name, total_boardings
    # -- Subquery for AVG comparison
    query= "Q10"
    desc= "Stops with above-average ridership"
    inf= """WITH totals AS(SELECT se.stop_id, SUM(se.passengers_on) AS total_boardings
    FROM stop_events se
    GROUP BY se.stop_id)
    SELECT s.stop_name, t.total_boardings
    FROM totals t
    JOIN stops s ON s.stop_id = t.stop_id
    WHERE t.total_boardings > (SELECT AVG(total_boardings) FROM totals)
    ORDER BY t.total_boardings DESC, s.stop_name"""
    param= ()
    return query,desc,inf,param


def get_args():
    g= argparse.ArgumentParser()
    g.add_argument("--host",default="db")
    g.add_argument("--dbname",required=True)
    g.add_argument("--user",default="transit")
    g.add_argument("--password",default="transit123")
    g.add_argument("--query",required=True)
    g.add_argument("--format",default="json")
    # unrecognized arguments: --format json
    # g.add_argument("--datadir",required=True)
    # g.add_argument("--schema", default="schema.sql")
    return g.parse_args()

def connect(arg):
    return psycopg2.connect(host=arg.host,
                            dbname=arg.dbname,
                            user=arg.user,
                            password=arg.password
                            )


def ex(cur,sql,param):
    cur.execute(sql,param)
    col= [c[0]for c in cur.description]
    row= cur.fetchall()
    dict_row= [dict(zip(col,r))for r in row]
    return dict_row

def run_one(cur, fn):
    q, desc, sql, params = fn()
    rows = ex(cur, sql, params)
    d = {
        "query": q,
        "description": desc,
        "count": len(rows),
        "results": rows,
    }
    return d


args= get_args()
con, cur= None, None
con= connect(args)

try:
    with con, con.cursor() as cur:
        if args.query.upper() == "ALL":
            func = [Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10]
            out = {}
            for f in func:
                block = run_one(cur, f)
                out[block["query"]] = block
            print(json.dumps(out, indent=2, ensure_ascii=False, default=_json_default))
        else:
            fn = globals()[args.query]
            block = run_one(cur, fn)
            print(json.dumps(block, indent=2, ensure_ascii=False, default=_json_default))
finally:
    con.close()