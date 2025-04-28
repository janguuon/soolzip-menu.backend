import sqlite3

def check_database():
    # 데이터베이스 연결
    conn = sqlite3.connect('cocktail_orders.db')
    cursor = conn.cursor()

    print("=== 데이터베이스 정보 확인 ===")
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n1. 테이블 목록:")
    for table in tables:
        print(f"- {table[0]}")

    # 각 테이블의 스키마 조회
    for table in tables:
        print(f"\n2. {table[0]} 테이블 스키마:")
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

    # 각 테이블의 데이터 조회
    for table in tables:
        print(f"\n3. {table[0]} 테이블 데이터:")
        cursor.execute(f"SELECT * FROM {table[0]};")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  - {row}")
        else:
            print("  - 데이터가 없습니다.")

    # 연결 종료
    conn.close()

if __name__ == "__main__":
    check_database() 