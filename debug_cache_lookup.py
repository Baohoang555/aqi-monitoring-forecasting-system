from sqlalchemy import create_engine, text
from pathlib import Path
import json

# load .env
env = {}
with Path('backend/.env').open('r', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k,v=line.split('=',1)
        env[k.strip()] = v.strip().strip('"').strip("'")

DB_URL = env['DATABASE_URL']
if DB_URL.startswith('mysql://'):
    DB_URL = DB_URL.replace('mysql://','mysql+pymysql://',1)
engine = create_engine(DB_URL, future=True)

cache = json.loads(Path('backend/city_geo_cache.json').read_text())

cities = ['10Th Of Ramadan','Abuja','Al Ahsa','Bac Giang','Dong Ha']
for city in cities:
    print('---', city)
    country = None
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT city, country FROM dim_location WHERE city=:city'), {'city': city}).fetchall()
        print('dim rows', rows)
        for _, c in rows:
            if c:
                country = c
    print('country from dim', country)
    def normalize(city, country=None):
        key = city.strip()
        if country:
            key = f'{key},{country.strip()}'
        return key
    keys = []
    if country:
        keys.append(normalize(city, country))
    keys.append(normalize(city, 'Unknown'))
    keys.append(normalize(city, None))
    print('keys', keys)
    for key in keys:
        print('  key', key, 'in cache', key in cache, 'value', cache.get(key))
