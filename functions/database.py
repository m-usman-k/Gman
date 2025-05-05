import sqlite3


from config import DATABASE_PATH

def db_connection():
    connection = sqlite3.connect(database=DATABASE_PATH)
    return connection

def setup_tables():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                draws INTEGER NOT NULL DEFAULT 0,
                total_games INTEGER NOT NULL DEFAULT 0,
                win_rate FLOAT NOT NULL DEFAULT 0.0
            )
            """
        )

        cursor.close()

def ensure_user_exists(user_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.close()

def set_balance(user_id: int, amount: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET points = ? WHERE id = ?", (amount, user_id))
        conn.commit()
        cursor.close()

def add_balance(user_id: int, amount: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (amount, user_id))
        conn.commit()
        cursor.close()

def remove_win_rate(user_id: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET win_rate = 0.0 WHERE id = ?", (user_id,))
        conn.commit()
        cursor.close()

def set_wins(user_id: int, wins: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET wins = ? WHERE id = ?", (wins, user_id))
        cursor.execute("UPDATE users SET total_games = wins + losses + draws WHERE id = ?", (user_id,))
        cursor.execute("UPDATE users SET win_rate = CASE WHEN total_games > 0 THEN (wins * 100.0) / total_games ELSE 0 END WHERE id = ?", (user_id,))
        conn.commit()
        cursor.close()

def set_losses(user_id: int, losses: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET losses = ? WHERE id = ?", (losses, user_id))
        cursor.execute("UPDATE users SET total_games = wins + losses + draws WHERE id = ?", (user_id,))
        cursor.execute("UPDATE users SET win_rate = CASE WHEN total_games > 0 THEN (wins * 100.0) / total_games ELSE 0 END WHERE id = ?", (user_id,))
        conn.commit()
        cursor.close()

def adjust_win_rate(user_id: int, percentage: float):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET win_rate = ? WHERE id = ?", (percentage, user_id))
        conn.commit()
        cursor.close()

def get_user_stats(user_id: int):
    ensure_user_exists(user_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT points, wins, losses, draws, total_games, win_rate 
            FROM users 
            WHERE id = ?
            """,
            (user_id,)
        )
        stats = cursor.fetchone()
        cursor.close()
        return {
            'points': stats[0],
            'wins': stats[1],
            'losses': stats[2],
            'draws': stats[3],
            'total_games': stats[4],
            'win_rate': stats[5]
        }

def transfer_points(from_user_id: int, to_user_id: int, amount: int) -> bool:
    """
    Transfer points from one user to another
    Returns True if transfer was successful, False if sender doesn't have enough points
    """
    ensure_user_exists(from_user_id)
    ensure_user_exists(to_user_id)
    
    with db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if sender has enough points
        cursor.execute("SELECT points FROM users WHERE id = ?", (from_user_id,))
        sender_points = cursor.fetchone()[0]
        
        if sender_points < amount:
            cursor.close()
            return False
            
        # Perform the transfer
        cursor.execute("UPDATE users SET points = points - ? WHERE id = ?", (amount, from_user_id))
        cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (amount, to_user_id))
        
        conn.commit()
        cursor.close()
        return True