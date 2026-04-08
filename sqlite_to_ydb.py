import asyncio
import sqlite3
import ydb

ENDPOINT = 'grpcs://ydb.serverless.yandexcloud.net:2135'
YDB_DB_PATH = '/ru-central1/...'

# --- KEY_CONTENT - из-за сложного формата лучше читать из .env ---
KEY_CONTENT = """{
  "id": "...",
  "service_account_id": "...",
  "created_at": "...",
  "key_algorithm": "RSA_2048",
  "public_key": "-----BEGIN PUBLIC KEY-----...
  """
SQLITE_DB_PATH = 'путь/файл.db'

ydb_driver_config = ydb.DriverConfig(
    endpoint=ENDPOINT,
    database=YDB_DB_PATH,
    credentials=ydb.iam.ServiceAccountCredentials.from_content(KEY_CONTENT),
    root_certificates=ydb.load_ydb_root_certificate(),
)


def get_data_from_sqlite() -> list:
    """
    Возвращает все записи из таблицы table_name в SQLite, отсортированные по возрастанию id.
    [!] Если таблица большая, лучше загружать чанками.

    Returns:
        list[dict]: Список словарей, где каждый dict — строка таблицы (ключ: значение).
    """
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM table_name ORDER BY id ASC")
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    print(f"[+] Данные из SQLite загружены: {len(results)} шт.")
    return results


async def save_data_to_ydb(results: list):
    """
    Сохраняет results в (!) существующую таблицу table_name в YDB.
    [!] Она должна иметь точно такие же поля, как у передаваемых значений.
    Здесь данные приведены для примера.

    """
    async with ydb.aio.Driver(ydb_driver_config) as driver:
        await driver.wait(timeout=15)
        session = await driver.table_client.session().create()

        query = """
        DECLARE $data AS List<Struct<
            id: Int64, user_id: Int64, o_type: Utf8, o_name: Utf8,
            o_date: Utf8, o_place: Utf8, o_km: Float, o_link: Utf8,
            o_map_id: Utf8, o_gps_id: Utf8, o_comment: Utf8
        >>;
        
        UPSERT INTO table_name (
            id, user_id, o_type, o_name, o_date, o_place, 
            o_km, o_link, o_map_id, o_gps_id, o_comment, updated_at
        )
        SELECT id, user_id, o_type, o_name, o_date, o_place,
               o_km, o_link, o_map_id, o_gps_id, o_comment,
               CurrentUtcTimestamp() AS updated_at
        FROM AS_TABLE($data);
        """

        await session.transaction().execute(
            await session.prepare(query), {"$data": results}, commit_tx=True
        )
        print(f"[+] Данные в YDB сохранены: {len(results)} шт.")


results = get_data_from_sqlite()
asyncio.run(save_data_to_ydb(results))
