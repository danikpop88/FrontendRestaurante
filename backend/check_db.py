import psycopg

BD = "mesa_abuela_test"
try:
    with psycopg.connect(host="localhost", port=5432, dbname=BD,
                         user="postgres", password="restaurante") as con:
        with con.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' ORDER BY table_name")
            tablas = [r[0] for r in cur.fetchall()]
            print(f"Tablas ({len(tablas)}): {tablas}")
            for t in ("producto", "usuario", "mesa", "reserva"):
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                print(f"  {t}: {cur.fetchone()[0]}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")