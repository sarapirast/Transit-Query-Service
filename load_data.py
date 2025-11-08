import psycopg2
import json, sys, os, csv, datetime, argparse
import decimal


def get_args():
    g= argparse.ArgumentParser()
    g.add_argument("--host",default="localhost")
    g.add_argument("--dbname",required=True)
    g.add_argument("--user",required=True)
    g.add_argument("--password",required=True)
    g.add_argument("--datadir",required=True)
    g.add_argument("--schema", default="schema.sql")
    return g.parse_args()





def connect(arg):
    return psycopg2.connect(host=arg.host,
                            dbname=arg.dbname,
                            user=arg.user,
                            password=arg.password
                            )

path= r"C:/HW/EE547HW/HW3/schema.sql"

def run_s(cur,path):
    with open(path,'r',encoding= 'utf-8') as file:
        sql=file.read()
        cur.execute(sql)



# loading the tables with data


def load(cur,path,exinfo,params):
    count= 0 #row count 
    with open(path, newline="", encoding="utf-8") as file:
        r= csv.DictReader(file)
        for row in r:
            # INSERT INTO table_name (column1, column2, column3, ...)
            # VALUES (value1, value2, value3, ...);
            param= tuple(row[i] for i in params)
            cur.execute(exinfo,param)
            count +=1
    return count



def load_lines(cur,path): 
    # line_name,vehicle_type
    # Route 2,bus
    # Route 4,bus
    # Route 20,bus
    exinfo= "INSERT INTO lines (line_name,vehicle_type) VALUES (%s,%s) ON CONFLICT (line_name) DO NOTHING"
    p= ["line_name","vehicle_type"]
    return load(cur,path,exinfo,p)

    

def load_stops(cur,path):
    # stop_name,latitude,longitude
    # Wilshire / Veteran,34.057616,-118.447888
    # Le Conte / Broxton,34.063594,-118.446732
    exinfo="""INSERT INTO stops (stop_name,latitude, longitude) VALUES (%s,%s,%s)
    ON CONFLICT (stop_name) DO NOTHING"""
    p= ["stop_name","latitude","longitude"]
    return load(cur,path,exinfo,p)


def load_line_stops(cur,path):
    #line_name,stop_name,sequence,time_offset
    # Route 20,Wilshire / Veteran,1,0
    # Route 20,Le Conte / Broxton,2,5
    exinfo= """INSERT INTO line_stops (line_id, stop_id, sequence_number, time_offset_minutes) 
    VALUES( 
        (SELECT line_id FROM lines WHERE line_name = %s),
        (SELECT stop_id FROM stops WHERE stop_name  = %s),
        %s,%s) ON CONFLICT (line_id, stop_id) DO NOTHING"""
    p= ["line_name","stop_name","sequence", "time_offset"]
    return load(cur,path,exinfo,p)

def load_trips(cur,path):
    #trip_id,line_name,scheduled_departure,vehicle_id
    # T0001,Route 2,2025-10-01 06:00:00,V101
    exinfo= """INSERT INTO trips (trip_id, line_id, scheduled_departure, vehicle_id)
    VALUES ( %s,
        (SELECT line_id FROM lines WHERE line_name = %s),
        %s,%s)ON CONFLICT (trip_id) DO NOTHING"""
    p= ["trip_id","line_name","scheduled_departure","vehicle_id"]
    return load(cur,path,exinfo,p)


def load_stop_events(cur,path):
    #trip_id,stop_name,scheduled,actual,passengers_on,passengers_off
    # T0001,Le Conte / Broxton,2025-10-01 06:00:00,2025-10-01 06:00:00,29,0
    # T0001,Le Conte / Westwood,2025-10-01 06:02:00,2025-10-01 06:02:00,25,29
    exinfo= """INSERT INTO stop_events (trip_id, stop_id, scheduled_time, actual_time, passengers_on, passengers_off)
        VALUES (%s,
            (SELECT stop_id FROM stops WHERE stop_name = %s),
            %s, %s, %s, %s) ON CONFLICT(trip_id,stop_id,scheduled_time) DO NOTHING"""
    p=["trip_id","stop_name","scheduled","actual","passengers_on","passengers_off"]
    return load(cur,path,exinfo,p)




args= get_args()
con, cur= None, None
try:
    con= connect(args)
    cur= con.cursor()

    cur.execute("SELECT to_regclass('public.lines')")
    exists = cur.fetchone()[0] is not None
    if not exists:
        con.autocommit = True
        run_s(cur, args.schema)   # your helper
        con.autocommit = False

    lines_csv= os.path.join(args.datadir, "lines.csv")
    stops_csv= os.path.join(args.datadir, "stops.csv")
    line_stops_csv= os.path.join(args.datadir, "line_stops.csv")
    trips_csv= os.path.join(args.datadir, "trips.csv")
    stop_events_csv= os.path.join(args.datadir, "stop_events.csv")

    print("lines:",load_lines(cur,lines_csv))
    print("stops:",load_stops(cur,stops_csv))
    print("line_stops:",load_line_stops(cur,line_stops_csv))
    print("trips:",load_trips(cur,trips_csv))
    print("stop_events:",load_stop_events(cur,stop_events_csv))

    con.commit()
except psycopg2.DatabaseError as e:
    print("Error:",e)
    if con:
        con.rollback()
except Exception as e:
    print("Error:",e)
    if con:
        con.rollback()
finally:
    if cur:
        cur.close()
    if con:
        con.close()

