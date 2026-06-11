import oracledb

USER = "GVDW_OWNER"
PASSWORD = "TxcE47g!"
DSN = "PIV-CLU-SCAN:1521/PDW1"

pool = oracledb.create_pool(
    user=USER,
    password=PASSWORD,
    dsn=DSN,
    min=2,
    max=10,
    increment=1
)

def get_connection():
    conn = pool.acquire()

    cur = conn.cursor()
    cur.execute("ALTER SESSION SET NLS_NUMERIC_CHARACTERS = ',.'")
    cur.close()

    return conn


def executar_transacao(callback):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        callback(cursor)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
