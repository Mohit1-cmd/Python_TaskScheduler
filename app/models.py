def init_db(conn):
    """Create the tasks and logs tables if they do not already exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            command     TEXT        NOT NULL,
            status      VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            retries     INT         NOT NULL DEFAULT 0,
            created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            task_id     INT,
            output      TEXT,
            status      VARCHAR(20),
            executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    conn.commit()
    cursor.close()
