from datetime import datetime, timedelta, timezone
import sqlite3
import obhapp.config as config

def cleanup_old_entries():
    """Cleanup old entries in the database."""
    db_filename = config.DATABASE_FILENAME
    print(f"Cleaning up old entries in {db_filename}")
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # Check existing data
    # print("Existing messages:")
    # for row in cursor.execute("SELECT * FROM messages"):
    #     print(row)

    # print("Existing change_log entries:")
    # for row in cursor.execute("SELECT * FROM change_log"):
    #     print(row)

    # Calculate the cutoff date
    # Convert Python's time to UTC
    now_utc = datetime.now(timezone.utc)
    cutoff_date = now_utc - timedelta(days=30)
    cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    # print(f"Cutoff date: {cutoff_date_str}")

    # Delete old entries
    cursor.execute("DELETE FROM messages WHERE created_at < ?", (cutoff_date_str,))
    cursor.execute("DELETE FROM change_log WHERE change_time < ?", (cutoff_date_str,))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    cleanup_old_entries()
