import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
import mariadb
from typing import Any, Generator, Optional
import hashlib
from datetime import date
from pathlib import Path
import uuid
import json
import ssl
import http.client
from urllib.parse import urlparse, urlunparse, unquote, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import traceback

# --- Pydantic model (อัปเกรดระบบ Data Validation) --------------------------------------

class Equipment(BaseModel):
    id: Optional[int] = None
    category_id: int = Field(..., gt=0, description="รหัสหมวดหมู่ต้องมากกว่า 0")
    name: str = Field(..., min_length=2, max_length=100, description="ชื่ออุปกรณ์ต้องมีความยาว 2-100 ตัวอักษร")
    brand: Optional[str] = Field(None, max_length=50, description="ชื่อแบรนด์ห้ามยาวเกิน 50 ตัวอักษร")
    serial_number: str = Field(..., min_length=3, max_length=50, description="Serial Number ต้องมีความยาว 3-50 ตัวอักษร")
    description: Optional[str] = None
    daily_rate: float = Field(..., ge=0, description="ราคาเช่ารายวันต้องไม่ติดลบ (0 หรือมากกว่า)")
    deposit_rate: float = Field(..., ge=0, description="ราคาเงินมัดจำต้องไม่ติดลบ (0 หรือมากกว่า)")
    status: Optional[str] = Field("available", pattern="^(available|rented|maintenance)$", description="สถานะต้องเป็น available, rented, หรือ maintenance เท่านั้น")
    image_urls: Optional[list[str]] = None
    primary_image_index: Optional[int] = 0

class CategoryImageUpdate(BaseModel):
    image_url: Optional[str] = None

class UserRegister(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, pattern="^[a-zA-Z0-9_]+$", description="Username ต้องยาว 4-20 ตัวอักษร และห้ามมีอักขระพิเศษ")
    password: str = Field(..., min_length=6, description="รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร")
    email: Optional[EmailStr] = Field(None, description="รูปแบบอีเมลต้องถูกต้อง (เช่น name@email.com)")
    phone: str = Field(..., min_length=9, max_length=10, pattern="^[0-9]+$", description="เบอร์โทรศัพท์ต้องเป็นตัวเลข 9-10 หลักเท่านั้น")
    id_card_number: Optional[str] = Field(None, min_length=13, max_length=13, pattern="^[0-9]+$", description="เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลักเท่านั้น")
    address: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(
        None,
        min_length=4,
        max_length=20,
        pattern="^[a-zA-Z0-9_]+$",
        description="Username ต้องยาว 4-20 ตัวอักษร และห้ามมีอักขระพิเศษ",
    )
    email: Optional[EmailStr] = Field(None, description="รูปแบบอีเมลต้องถูกต้อง (เช่น name@email.com)")
    phone: Optional[str] = Field(
        None,
        min_length=9,
        max_length=10,
        pattern="^[0-9]+$",
        description="เบอร์โทรศัพท์ต้องเป็นตัวเลข 9-10 หลักเท่านั้น",
    )
    id_card_number: Optional[str] = Field(
        None,
        min_length=13,
        max_length=13,
        pattern="^[0-9]+$",
        description="เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลักเท่านั้น",
    )
    address: Optional[str] = None

class RentalCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    equipment_id: int = Field(..., gt=0)
    start_date: date
    end_date: date
    contact_phone: str = Field(..., min_length=9, max_length=20)
    pickup_location: str = Field(..., min_length=2, max_length=255)
    purpose: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None

class RentalReturn(BaseModel):
    condition_after: Optional[str] = None
    penalty_fee: float = Field(0, ge=0)
    deposit_action: str = Field("refunded", pattern="^(paid|refunded|confiscated)$")
    actor_user_id: Optional[int] = None

class RentalStatusUpdate(BaseModel):
    rental_status: str = Field(..., pattern="^(pending|active|completed|cancelled)$")
    actor_user_id: Optional[int] = None
    remark: Optional[str] = None

class RentalCancelRequest(BaseModel):
    actor_user_id: int = Field(..., gt=0)
    remark: Optional[str] = None

class RentalConditionReviewUpdate(BaseModel):
    actor_user_id: int = Field(..., gt=0)
    condition_before: Optional[str] = None
    condition_after: Optional[str] = None
    review_note: Optional[str] = None

app = FastAPI(title="Camera Rental API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(BASE_DIR, "camera_store.db"))
DB_BACKEND = {"name": None, "detail": ""}
UPLOAD_DIR = Path(BASE_DIR) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# เปลี่ยน IP เป็น 192.168.1.131 และ Database เป็น camera_store
def get_mariadb_config() -> dict:
    return {
        "host": os.getenv("DB_HOST", "192.168.1.131"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"), # อย่าลืมแก้ถ้า user ไม่ใช่ root
        "password": os.getenv("DB_PASSWORD", "P@ssw0rd"), # แก้รหัสผ่านให้ตรงกับของเครื่องคุณ
        "database": os.getenv("DB_NAME", "camera_store"),
    }

def select_db_backend() -> str:
    if DB_BACKEND["name"]:
        return DB_BACKEND["name"]

    preferred_backend = os.getenv("DB_BACKEND", "auto").lower()

    if preferred_backend == "sqlite":
        DB_BACKEND["name"] = "sqlite"
        DB_BACKEND["detail"] = f"SQLite database at {SQLITE_DB_PATH}"
        return DB_BACKEND["name"]

    mariadb_config = get_mariadb_config()

    try:
        conn = mariadb.connect(**mariadb_config)
        conn.close()
        DB_BACKEND["name"] = "mariadb"
        DB_BACKEND["detail"] = f"MariaDB database {mariadb_config['database']} at {mariadb_config['host']}:{mariadb_config['port']}"
    except mariadb.Error as exc:
        if preferred_backend == "mariadb":
            raise
        DB_BACKEND["name"] = "sqlite"
        DB_BACKEND["detail"] = f"SQLite fallback at {SQLITE_DB_PATH} because MariaDB is unavailable: {exc}"

    return DB_BACKEND["name"]

def get_cursor(db: Any, dictionary: bool = False):
    if select_db_backend() == "sqlite":
        return db.cursor()
    return db.cursor(dictionary=dictionary) if dictionary else db.cursor()

def execute_sql(cursor: Any, query: str, params: tuple = ()):
    if select_db_backend() == "sqlite":
        cursor.execute(query.replace("%s", "?"), params)
        return
    cursor.execute(query, params)

def fetch_one(cursor: Any):
    row = cursor.fetchone()
    if row is None:
        return None
    if select_db_backend() == "sqlite":
        return dict(row)
    return row

def fetch_all(cursor: Any):
    rows = cursor.fetchall()
    if select_db_backend() == "sqlite":
        return [dict(row) for row in rows]
    return rows

# --- database helpers -----------------------------------------------------

def get_connection() -> Any:
    if select_db_backend() == "sqlite":
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    return mariadb.connect(**get_mariadb_config())

def get_db() -> Generator[Any, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_support_tables(db: Any):
    cur = get_cursor(db)
    if select_db_backend() == "sqlite":
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_condition_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                phase TEXT NOT NULL CHECK (phase IN ('before', 'after')),
                image_url TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) ON DELETE CASCADE
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS deposit_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('receive','refund','confiscate','penalty')),
                amount REAL NOT NULL,
                note TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_status_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                from_status TEXT CHECK (from_status IN ('pending','active','completed','cancelled')),
                to_status TEXT NOT NULL CHECK (to_status IN ('pending','active','completed','cancelled')),
                remark TEXT,
                changed_by INTEGER,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_form_details (
                rental_id INTEGER PRIMARY KEY,
                contact_phone TEXT NOT NULL,
                pickup_location TEXT NOT NULL,
                purpose TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) ON DELETE CASCADE
            )
            """,
        )
    else:
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_condition_images (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                rental_id INT NOT NULL,
                phase ENUM('before','after') NOT NULL,
                image_url TEXT NOT NULL,
                note TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_rci_rental
                    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS deposit_transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                rental_id INT NOT NULL,
                transaction_type ENUM('receive','refund','confiscate','penalty') NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                note TEXT NULL,
                created_by INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_dt_rental
                    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_dt_user
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                    ON DELETE SET NULL ON UPDATE CASCADE
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_status_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                rental_id INT NOT NULL,
                from_status ENUM('pending','active','completed','cancelled') NULL,
                to_status ENUM('pending','active','completed','cancelled') NOT NULL,
                remark TEXT NULL,
                changed_by INT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_rsl_rental
                    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_rsl_user
                    FOREIGN KEY (changed_by) REFERENCES users(user_id)
                    ON DELETE SET NULL ON UPDATE CASCADE
            )
            """,
        )
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS rental_form_details (
                rental_id INT PRIMARY KEY,
                contact_phone VARCHAR(20) NOT NULL,
                pickup_location VARCHAR(255) NOT NULL,
                purpose VARCHAR(255) NULL,
                note TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_rfd_rental
                    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """,
        )
    db.commit()

def get_table_columns(db: Any, table_name: str) -> set[str]:
    cur = get_cursor(db)
    if select_db_backend() == "sqlite":
        execute_sql(cur, f"PRAGMA table_info({table_name})")
        return {row[1] for row in cur.fetchall()}
    execute_sql(cur, f"SHOW COLUMNS FROM {table_name}")
    return {row[0] for row in cur.fetchall()}

def ensure_catalog_media_schema(db: Any):
    cur = get_cursor(db)
    cols = get_table_columns(db, "categories")
    if "image_url" not in cols:
        if select_db_backend() == "sqlite":
            execute_sql(cur, "ALTER TABLE categories ADD COLUMN image_url TEXT")
        else:
            execute_sql(cur, "ALTER TABLE categories ADD COLUMN image_url TEXT NULL")

    if select_db_backend() == "sqlite":
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS equipment_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_id) REFERENCES equipments(equipment_id) ON DELETE CASCADE
            )
            """,
        )
    else:
        execute_sql(
            cur,
            """
            CREATE TABLE IF NOT EXISTS equipment_images (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                equipment_id INT NOT NULL,
                image_url TEXT NOT NULL,
                is_primary TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_eq_img_equipment
                    FOREIGN KEY (equipment_id) REFERENCES equipments(equipment_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """,
        )
    db.commit()

def create_status_log(db: Any, rental_id: int, from_status: Optional[str], to_status: str, remark: Optional[str] = None, changed_by: Optional[int] = None):
    cur = get_cursor(db)
    execute_sql(
        cur,
        """
        INSERT INTO rental_status_logs (rental_id, from_status, to_status, remark, changed_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (rental_id, from_status, to_status, remark, changed_by),
    )

def create_deposit_transaction(db: Any, rental_id: int, transaction_type: str, amount: float, note: Optional[str] = None, created_by: Optional[int] = None):
    cur = get_cursor(db)
    execute_sql(
        cur,
        """
        INSERT INTO deposit_transactions (rental_id, transaction_type, amount, note, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (rental_id, transaction_type, amount, note, created_by),
    )

def get_user_role(db: Any, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    cur = get_cursor(db, dictionary=True)
    execute_sql(cur, "SELECT role FROM users WHERE user_id = %s", (user_id,))
    row = fetch_one(cur)
    if not row:
        return None
    return row.get("role")

def ensure_admin_actor(db: Any, actor_user_id: Optional[int]):
    role = get_user_role(db, actor_user_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")

def ensure_owner_or_admin(db: Any, actor_user_id: Optional[int], owner_user_id: int):
    if not actor_user_id:
        raise HTTPException(status_code=403, detail="actor_user_id is required")
    if actor_user_id == owner_user_id:
        return
    role = get_user_role(db, actor_user_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Owner or admin permission required")

@app.on_event("startup")
def startup_init_tables():
    db = get_connection()
    try:
        ensure_support_tables(db)
        ensure_catalog_media_schema(db)
    finally:
        db.close()

def get_equipment_images_rows(db: Any, equipment_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT image_id, equipment_id, image_url, is_primary
        FROM equipment_images
        WHERE equipment_id = %s
        ORDER BY is_primary DESC, image_id ASC
        """,
        (equipment_id,),
    )
    return fetch_all(cur)

def with_equipment_images(db: Any, equipment: dict) -> dict:
    rows = get_equipment_images_rows(db, equipment["id"])
    image_urls = [row["image_url"] for row in rows]
    primary = None
    for row in rows:
        if int(row.get("is_primary") or 0) == 1:
            primary = row["image_url"]
            break
    if not primary and image_urls:
        primary = image_urls[0]
    equipment["image_urls"] = image_urls
    equipment["primary_image_url"] = primary
    return equipment

def replace_equipment_images(db: Any, equipment_id: int, image_urls: list[str], primary_image_index: int = 0):
    cur = get_cursor(db)
    execute_sql(cur, "DELETE FROM equipment_images WHERE equipment_id = %s", (equipment_id,))
    urls = [str(u).strip() for u in (image_urls or []) if str(u).strip()]
    if not urls:
        return

    safe_primary_idx = max(0, min(primary_image_index, len(urls) - 1))
    for idx, url in enumerate(urls):
        execute_sql(
            cur,
            """
            INSERT INTO equipment_images (equipment_id, image_url, is_primary)
            VALUES (%s, %s, %s)
            """,
            (equipment_id, url, 1 if idx == safe_primary_idx else 0),
        )

def get_rental_with_join(db: Any, rental_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT
            r.rental_id as id,
            r.user_id,
            r.equipment_id,
            r.start_date,
            r.end_date,
            r.actual_return_date,
            r.total_rent_price,
            r.penalty_fee,
            r.deposit_status,
            r.rental_status,
            r.condition_before,
            r.condition_after,
            r.created_at,
            u.username,
            e.name as equipment_name,
            e.deposit_rate
        FROM rentals r
        JOIN users u ON u.user_id = r.user_id
        JOIN equipments e ON e.equipment_id = r.equipment_id
        WHERE r.rental_id = %s
        """,
        (rental_id,),
    )
    return fetch_one(cur)

def get_rental_images_rows(db: Any, rental_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT image_id, rental_id, phase, image_url, note, created_at
        FROM rental_condition_images
        WHERE rental_id = %s
        ORDER BY image_id DESC
        """,
        (rental_id,),
    )
    return fetch_all(cur)

def get_rental_logs_rows(db: Any, rental_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT log_id, rental_id, from_status, to_status, remark, changed_by, changed_at
        FROM rental_status_logs
        WHERE rental_id = %s
        ORDER BY log_id DESC
        """,
        (rental_id,),
    )
    return fetch_all(cur)

def get_rental_transactions_rows(db: Any, rental_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT transaction_id, rental_id, transaction_type, amount, note, created_by, created_at
        FROM deposit_transactions
        WHERE rental_id = %s
        ORDER BY transaction_id DESC
        """,
        (rental_id,),
    )
    return fetch_all(cur)

def get_rental_form_details_row(db: Any, rental_id: int):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT rental_id, contact_phone, pickup_location, purpose, note, created_at
        FROM rental_form_details
        WHERE rental_id = %s
        """,
        (rental_id,),
    )
    return fetch_one(cur)

def save_uploaded_image(file: UploadFile, rental_id: int) -> str:
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    rental_folder = UPLOAD_DIR / f"rental_{rental_id}"
    rental_folder.mkdir(parents=True, exist_ok=True)
    save_path = rental_folder / filename
    with open(save_path, "wb") as out_file:
        out_file.write(file.file.read())
    rel_path = save_path.relative_to(UPLOAD_DIR)
    return f"/uploads/{str(rel_path).replace('\\\\', '/')}"


def save_uploaded_equipment_image(file: UploadFile, equipment_id: Optional[int] = None) -> str:
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    folder_name = f"equipment_{equipment_id}" if equipment_id else "equipment_temp"
    equipment_folder = UPLOAD_DIR / folder_name
    equipment_folder.mkdir(parents=True, exist_ok=True)
    save_path = equipment_folder / filename
    with open(save_path, "wb") as out_file:
        out_file.write(file.file.read())
    rel_path = save_path.relative_to(UPLOAD_DIR)
    return f"/uploads/{str(rel_path).replace('\\\\', '/')}"

# --- Health Check Endpoint --------------------------------------------------

@app.get("/")
def health_check(db: Any = Depends(get_db)):
    """Check if API and database are working"""
    try:
        cur = get_cursor(db)
        execute_sql(cur, "SELECT 1")
        result = cur.fetchone()
        if result:
            return {
                "status": "ok",
                "message": "API and database are connected",
                "database": DB_BACKEND["detail"],
                "backend": select_db_backend()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/proxy-image")
def proxy_image(url: str):
    """Proxy external image to circumvent CORS issues"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    url = url.strip()
    # Some records already contain percent-encoded chars; decode to avoid double-encoded URLs.
    for _ in range(2):
        decoded = unquote(url)
        if decoded == url:
            break
        url = decoded

    # Normalize URL so spaces and special chars in path/query are safely encoded.
    normalized = urlparse(url)
    safe_path = quote(unquote(normalized.path), safe="/:@%+-._~")
    safe_query = quote(unquote(normalized.query), safe="=&:%+,-._~")
    url = urlunparse(
        (
            normalized.scheme,
            normalized.netloc,
            safe_path,
            normalized.params,
            safe_query,
            "",
        )
    )
    
    # Only allow proxying of external URLs
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Only external URLs are supported")
    
    # Create hash of URL as filename to avoid duplicates
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Try to parse extension from URL
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Default to jpg, detect from URL
    ext = ".jpg"
    if path.endswith((".png", ".webp", ".gif", ".jpeg")):
        for e in [".png", ".webp", ".gif", ".jpeg"]:
            if path.endswith(e):
                ext = e
                break
    
    filename = f"{url_hash}{ext}"
    cache_folder = UPLOAD_DIR / "image_cache"
    cache_folder.mkdir(parents=True, exist_ok=True)
    cache_path = cache_folder / filename

    def detect_content_type(file_path: Path) -> str:
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            return "image/gif"
        if header.startswith(b"RIFF") and b"WEBP" in header:
            return "image/webp"
        return "application/octet-stream"

    def download_to_cache() -> None:
        def try_raw_http_fetch(candidate_url: str) -> bool:
            parsed_candidate = urlparse(candidate_url)
            if parsed_candidate.scheme != "http" or not parsed_candidate.netloc:
                return False

            path_with_query = parsed_candidate.path or "/"
            if parsed_candidate.query:
                path_with_query = f"{path_with_query}?{parsed_candidate.query}"

            conn = http.client.HTTPConnection(parsed_candidate.netloc, timeout=15)
            try:
                conn.request(
                    "GET",
                    path_with_query,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
                        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Referer": f"{header_origin}/",
                        "Origin": header_origin,
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    },
                )
                resp = conn.getresponse()
                if resp.status != 200:
                    print(f"proxy: raw http fetch status={resp.status} reason={getattr(resp,'reason',None)} for {candidate_url}")
                    return False
                body = resp.read()
                if not body:
                    return False
                with open(cache_path, "wb") as f:
                    f.write(body)
                return True
            finally:
                conn.close()

        parsed_url = urlparse(url)
        print(f"proxy: download_to_cache start for url={url}, parsed={parsed_url}")
        candidates = [url]
        if parsed_url.scheme == "https":
            http_url = urlunparse(parsed_url._replace(scheme="http"))
            candidates.append(http_url)
        header_origin = f"https://{parsed_url.netloc}" if parsed_url.netloc else f"{parsed_url.scheme}://{parsed_url.netloc}"

        last_error: Optional[Exception] = None
        for idx, candidate in enumerate(candidates):
            print(f"proxy: trying candidate[{idx}] = {candidate}")
            req = Request(
                candidate,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": f"{header_origin}/",
                    "Origin": header_origin,
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )

            try:
                with urlopen(req, timeout=15) as resp:
                    body = resp.read()
                    with open(cache_path, "wb") as f:
                        f.write(body)
                print(f"proxy: successfully cached candidate {candidate} ({len(body)} bytes)")
                return
            except HTTPError as exc:
                last_error = exc
                print(f"proxy: HTTPError code={getattr(exc,'code',None)} reason={getattr(exc,'reason',None)} for {candidate}")
                try:
                    body_preview = exc.read()[:512]
                    print(f"proxy: HTTPError body preview: {body_preview!r}")
                except Exception:
                    pass
                traceback.print_exc()
                # Some sites block HTTPS hotlink but allow HTTP direct fetch.
                if getattr(exc, "code", None) in (403, 429) and idx < len(candidates) - 1:
                    print("proxy: will try next candidate due to 403/429")
                    continue
                if getattr(exc, "code", None) in (403, 429) and urlparse(candidate).scheme == "http":
                    if try_raw_http_fetch(candidate):
                        print("proxy: raw http fetch succeeded after HTTPError")
                        return
            except URLError as exc:
                last_error = exc
                print(f"proxy: URLError for {candidate}: {repr(exc)}")
                traceback.print_exc()
                reason = getattr(exc, "reason", None)
                if isinstance(reason, ssl.SSLCertVerificationError):
                    insecure_ctx = ssl._create_unverified_context()
                    try:
                        with urlopen(req, timeout=15, context=insecure_ctx) as resp:
                            body = resp.read()
                            with open(cache_path, "wb") as f:
                                f.write(body)
                        print("proxy: fetched with insecure SSL context and cached")
                        return
                    except Exception as insecure_exc:
                        last_error = insecure_exc
                        traceback.print_exc()
                        if idx < len(candidates) - 1:
                            print("proxy: will try next candidate after SSL insecure attempt failed")
                            continue

                if idx < len(candidates) - 1:
                    print("proxy: will try next candidate due to URLError")
                    continue
                if urlparse(candidate).scheme == "http":
                    if try_raw_http_fetch(candidate):
                        print("proxy: raw http fetch succeeded after URLError")
                        return

        if last_error:
            raise last_error
    
    # Return cached version if already exists
    if not cache_path.exists():
        try:
            download_to_cache()
        except Exception as e:
            print(f"Failed to cache external image {url}: {str(e)}")
            raise HTTPException(status_code=502, detail="Failed to fetch image from external source")
    
    # Determine content type from real file bytes (URL extension can be wrong)
    content_type = detect_content_type(cache_path)
    
    return FileResponse(str(cache_path), media_type=content_type)

# --- Authentication Endpoints -----------------------------------------------

@app.post("/register")
def register(user: UserRegister, db: Any = Depends(get_db)):
    """Register a new user (with identity details)"""
    cur = get_cursor(db)
    hashed_password = hash_password(user.password)
    
    try:
        execute_sql(
            cur,
            """INSERT INTO users (username, password, email, phone, id_card_number, address) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user.username, hashed_password, user.email, user.phone, user.id_card_number, user.address),
        )
        db.commit()
        return {"message": "User registered successfully", "username": user.username}
    except mariadb.Error as exc:
        if "Duplicate entry" in str(exc):
            raise HTTPException(status_code=400, detail="Username already exists")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {str(exc)}")

@app.post("/login")
def login(credentials: LoginRequest, db: Any = Depends(get_db)):
    """Login user"""
    cur = get_cursor(db, dictionary=True)
    hashed_password = hash_password(credentials.password)
    
    try:
        execute_sql(
            cur,
            "SELECT user_id, username, role FROM users WHERE username = %s AND password = %s",
            (credentials.username, hashed_password),
        )
        user = fetch_one(cur)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        return {
            "message": "Login successful",
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {str(exc)}")


@app.get("/users/{user_id}")
def get_user_profile(user_id: int, db: Any = Depends(get_db)):
    """Get profile detail by user ID"""
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT user_id, username, role, email, phone, id_card_number, address
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
    )
    user = fetch_one(cur)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}")
def update_user_profile(user_id: int, payload: UserProfileUpdate, db: Any = Depends(get_db)):
    """Update editable profile fields by user ID"""
    update_map = {
        "username": payload.username,
        "email": payload.email,
        "phone": payload.phone,
        "id_card_number": payload.id_card_number,
        "address": payload.address,
    }
    updates = [(k, v) for k, v in update_map.items() if v is not None]
    if not updates:
        raise HTTPException(status_code=400, detail="No profile fields to update")

    cur = get_cursor(db)
    set_clause = ", ".join([f"{k} = %s" for k, _ in updates])
    params = tuple(v for _, v in updates) + (user_id,)

    try:
        execute_sql(cur, f"UPDATE users SET {set_clause} WHERE user_id = %s", params)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        db.commit()
    except HTTPException:
        raise
    except mariadb.Error as exc:
        if "Duplicate entry" in str(exc):
            raise HTTPException(status_code=400, detail="Username already exists")
        raise HTTPException(status_code=400, detail=str(exc))
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=400, detail="Username already exists")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {str(exc)}")

    cur_profile = get_cursor(db, dictionary=True)
    execute_sql(
        cur_profile,
        """
        SELECT user_id, username, role, email, phone, id_card_number, address
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
    )
    result = fetch_one(cur_profile)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

# --- Equipment Endpoints (CRUD) ---------------------------------------------

@app.get("/categories")
def get_categories(db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        "SELECT category_id as id, name, description, image_url FROM categories ORDER BY category_id",
    )
    return fetch_all(cur)

@app.put("/categories/{category_id}/image")
def update_category_image(category_id: int, payload: CategoryImageUpdate, db: Any = Depends(get_db)):
    cur = get_cursor(db)
    execute_sql(
        cur,
        "UPDATE categories SET image_url = %s WHERE category_id = %s",
        (payload.image_url, category_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    db.commit()
    return {"id": category_id, "image_url": payload.image_url}

@app.get("/equipments")
def get_equipments(db: Any = Depends(get_db)):
    """Get all equipments"""
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT
            e.equipment_id as id,
            e.category_id,
            c.name as category_name,
            e.name,
            e.brand,
            e.serial_number,
            e.description,
            e.daily_rate,
            e.deposit_rate,
            e.status
        FROM equipments e
        LEFT JOIN categories c ON c.category_id = e.category_id
        ORDER BY e.equipment_id DESC
        """,
    )
    items = fetch_all(cur)
    return [with_equipment_images(db, item) for item in items]

@app.get("/equipments/{equipment_id}")
def get_equipment(equipment_id: int, db: Any = Depends(get_db)):
    """Get specific equipment by ID"""
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT
            e.equipment_id as id,
            e.category_id,
            c.name as category_name,
            e.name,
            e.brand,
            e.serial_number,
            e.description,
            e.daily_rate,
            e.deposit_rate,
            e.status
        FROM equipments e
        LEFT JOIN categories c ON c.category_id = e.category_id
        WHERE e.equipment_id = %s
        """,
        (equipment_id,),
    )
    equipment = fetch_one(cur)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return with_equipment_images(db, equipment)

@app.post("/equipments")
def add_equipment(eq: Equipment, db: Any = Depends(get_db)):
    """Add new equipment"""
    cur = get_cursor(db)
    try:
        execute_sql(
            cur,
            """INSERT INTO equipments (category_id, name, brand, serial_number, description, daily_rate, deposit_rate, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (eq.category_id, eq.name, eq.brand, eq.serial_number, eq.description, eq.daily_rate, eq.deposit_rate, eq.status),
        )
        eq_id = cur.lastrowid
        replace_equipment_images(db, eq_id, eq.image_urls or [], eq.primary_image_index or 0)
        db.commit()
    except mariadb.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    
    return get_equipment(eq_id, db)

@app.put("/equipments/{equipment_id}")
def update_equipment(equipment_id: int, eq: Equipment, db: Any = Depends(get_db)):
    """Update existing equipment"""
    cur = get_cursor(db)
    execute_sql(
        cur,
        """UPDATE equipments 
           SET category_id = %s, name = %s, brand = %s, serial_number = %s, description = %s, daily_rate = %s, deposit_rate = %s, status = %s 
           WHERE equipment_id = %s""",
        (eq.category_id, eq.name, eq.brand, eq.serial_number, eq.description, eq.daily_rate, eq.deposit_rate, eq.status, equipment_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")

    if eq.image_urls is not None:
        replace_equipment_images(db, equipment_id, eq.image_urls, eq.primary_image_index or 0)

    db.commit()
    return get_equipment(equipment_id, db)

@app.delete("/equipments/{equipment_id}")
def delete_equipment(equipment_id: int, db: Any = Depends(get_db)):
    """Delete equipment"""
    cur = get_cursor(db)
    execute_sql(cur, "DELETE FROM equipments WHERE equipment_id = %s", (equipment_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db.commit()
    return {"message": "Equipment deleted"}


@app.post("/equipments/images/upload")
def upload_equipment_image(
    actor_user_id: int = Form(...),
    equipment_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Any = Depends(get_db),
):
    """Upload equipment image file and return URL to be used in equipment_images."""
    ensure_admin_actor(db, actor_user_id)
    image_url = save_uploaded_equipment_image(file, equipment_id)
    return {"image_url": image_url}

# --- Rental Endpoints (Queue / Deposit / Condition) ------------------------

@app.get("/rentals")
def get_rentals(user_id: Optional[int] = None, db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    base_query = """
        SELECT
            r.rental_id as id,
            r.user_id,
            r.equipment_id,
            r.start_date,
            r.end_date,
            r.actual_return_date,
            r.total_rent_price,
            r.penalty_fee,
            r.deposit_status,
            r.rental_status,
            r.condition_before,
            r.condition_after,
            r.created_at,
            u.username,
            e.name as equipment_name,
            e.deposit_rate
        FROM rentals r
        JOIN users u ON u.user_id = r.user_id
        JOIN equipments e ON e.equipment_id = r.equipment_id
    """
    if user_id:
        execute_sql(cur, base_query + " WHERE r.user_id = %s ORDER BY r.rental_id DESC", (user_id,))
    else:
        execute_sql(cur, base_query + " ORDER BY r.rental_id DESC")
    return fetch_all(cur)

@app.get("/rentals/{rental_id}/images")
def get_rental_images(rental_id: int, db: Any = Depends(get_db)):
    return get_rental_images_rows(db, rental_id)

@app.post("/rentals/{rental_id}/images/batch")
def upload_rental_images_batch(
    rental_id: int,
    phase: str = Form(...),
    note: Optional[str] = Form(None),
    image_urls: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    actor_user_id: Optional[int] = Form(None),
    db: Any = Depends(get_db),
):
    if phase not in ("before", "after"):
        raise HTTPException(status_code=400, detail="Phase must be before or after")
    if not image_urls and not files:
        raise HTTPException(status_code=400, detail="Send image_urls or files")

    cur = get_cursor(db, dictionary=True)
    execute_sql(cur, "SELECT rental_id, user_id FROM rentals WHERE rental_id = %s", (rental_id,))
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    ensure_owner_or_admin(db, actor_user_id, rental["user_id"])

    final_urls = []
    if image_urls:
        parsed_urls = []
        try:
            data = json.loads(image_urls)
            if isinstance(data, list):
                parsed_urls = [str(item).strip() for item in data if str(item).strip()]
        except Exception:
            parsed_urls = [line.strip() for line in image_urls.splitlines() if line.strip()]
        final_urls.extend(parsed_urls)

    for file in files:
        final_urls.append(save_uploaded_image(file, rental_id))

    if not final_urls:
        raise HTTPException(status_code=400, detail="No valid image items found")

    cur_insert = get_cursor(db)
    for url in final_urls:
        execute_sql(
            cur_insert,
            """
            INSERT INTO rental_condition_images (rental_id, phase, image_url, note)
            VALUES (%s, %s, %s, %s)
            """,
            (rental_id, phase, url, note),
        )
    db.commit()
    return {"message": "Images uploaded", "count": len(final_urls), "items": final_urls}

@app.get("/rentals/{rental_id}/logs")
def get_rental_logs(rental_id: int, db: Any = Depends(get_db)):
    return get_rental_logs_rows(db, rental_id)

@app.get("/rentals/{rental_id}/transactions")
def get_rental_transactions(rental_id: int, db: Any = Depends(get_db)):
    return get_rental_transactions_rows(db, rental_id)

@app.get("/rentals/{rental_id}/details")
def get_rental_details(rental_id: int, db: Any = Depends(get_db)):
    rental = get_rental_with_join(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return {
        "rental": rental,
        "form": get_rental_form_details_row(db, rental_id),
        "images": get_rental_images_rows(db, rental_id),
        "logs": get_rental_logs_rows(db, rental_id),
        "transactions": get_rental_transactions_rows(db, rental_id),
    }

@app.post("/rentals/{rental_id}/images")
def upload_rental_image(
    rental_id: int,
    phase: str = Form(...),
    note: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    actor_user_id: Optional[int] = Form(None),
    db: Any = Depends(get_db),
):
    if phase not in ("before", "after"):
        raise HTTPException(status_code=400, detail="Phase must be before or after")
    if not image_url and not file:
        raise HTTPException(status_code=400, detail="Send image_url or file")

    cur = get_cursor(db, dictionary=True)
    execute_sql(cur, "SELECT rental_id, user_id FROM rentals WHERE rental_id = %s", (rental_id,))
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    ensure_owner_or_admin(db, actor_user_id, rental["user_id"])

    final_url = image_url
    if file:
        final_url = save_uploaded_image(file, rental_id)

    cur_insert = get_cursor(db)
    execute_sql(
        cur_insert,
        """
        INSERT INTO rental_condition_images (rental_id, phase, image_url, note)
        VALUES (%s, %s, %s, %s)
        """,
        (rental_id, phase, final_url, note),
    )
    image_id = cur_insert.lastrowid
    db.commit()
    return {
        "image_id": image_id,
        "rental_id": rental_id,
        "phase": phase,
        "image_url": final_url,
        "note": note,
    }

@app.post("/rentals")
def create_rental(payload: RentalCreate, db: Any = Depends(get_db)):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    cur = get_cursor(db, dictionary=True)
    execute_sql(cur, "SELECT user_id FROM users WHERE user_id = %s", (payload.user_id,))
    user = fetch_one(cur)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    execute_sql(
        cur,
        "SELECT equipment_id, daily_rate, deposit_rate, status FROM equipments WHERE equipment_id = %s",
        (payload.equipment_id,),
    )
    equipment = fetch_one(cur)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    if equipment["status"] != "available":
        raise HTTPException(status_code=400, detail="Equipment is not available")

    execute_sql(
        cur,
        """
        SELECT rental_id
        FROM rentals
        WHERE equipment_id = %s
          AND rental_status IN ('pending', 'active')
          AND NOT (end_date < %s OR start_date > %s)
        LIMIT 1
        """,
        (payload.equipment_id, payload.start_date, payload.end_date),
    )
    overlap = fetch_one(cur)
    if overlap:
        raise HTTPException(status_code=400, detail="Equipment already has a booking in this date range")

    rental_days = (payload.end_date - payload.start_date).days + 1
    total_price = float(equipment["daily_rate"]) * rental_days

    cur_insert = get_cursor(db)
    execute_sql(
        cur_insert,
        """
        INSERT INTO rentals (
            user_id,
            equipment_id,
            start_date,
            end_date,
            total_rent_price,
            penalty_fee,
            deposit_status,
            rental_status,
            condition_before
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            payload.user_id,
            payload.equipment_id,
            payload.start_date,
            payload.end_date,
            total_price,
            0,
            "paid",
            "pending",
            None,
        ),
    )
    rental_id = cur_insert.lastrowid

    execute_sql(
        cur_insert,
        """
        INSERT INTO rental_form_details (rental_id, contact_phone, pickup_location, purpose, note)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (rental_id, payload.contact_phone, payload.pickup_location, payload.purpose, payload.note),
    )

    deposit_rate = float(equipment["deposit_rate"] or 0)

    create_deposit_transaction(
        db,
        rental_id,
        "receive",
        deposit_rate,
        "Deposit received at queue creation",
        payload.user_id,
    )
    create_status_log(db, rental_id, None, "pending", "Created from rental request", payload.user_id)
    db.commit()

    rental = get_rental_with_join(db, rental_id)
    return rental

@app.put("/rentals/{rental_id}/status")
def update_rental_status(rental_id: int, payload: RentalStatusUpdate, db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        "SELECT rental_status, equipment_id, user_id FROM rentals WHERE rental_id = %s",
        (rental_id,),
    )
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    previous_status = rental["rental_status"]
    next_status = payload.rental_status
    if previous_status == next_status:
        return {"message": "Rental status unchanged"}

    allowed_transitions = {
        "pending": {"active", "cancelled"},
        "active": {"completed", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }
    if next_status not in allowed_transitions.get(previous_status, set()):
        raise HTTPException(status_code=400, detail=f"Invalid status transition: {previous_status} -> {next_status}")

    if next_status in ("active", "cancelled"):
        ensure_admin_actor(db, payload.actor_user_id)

    cur_update = get_cursor(db)
    execute_sql(
        cur_update,
        "UPDATE rentals SET rental_status = %s WHERE rental_id = %s",
        (next_status, rental_id),
    )

    if next_status == "active":
        execute_sql(
            cur_update,
            "UPDATE equipments SET status = %s WHERE equipment_id = %s",
            ("rented", rental["equipment_id"]),
        )
    elif next_status in ("cancelled", "completed"):
        execute_sql(
            cur_update,
            "UPDATE equipments SET status = %s WHERE equipment_id = %s",
            ("available", rental["equipment_id"]),
        )

    if next_status == "cancelled":
        cur_dep = get_cursor(db, dictionary=True)
        execute_sql(
            cur_dep,
            """
            SELECT e.deposit_rate
            FROM rentals r
            JOIN equipments e ON e.equipment_id = r.equipment_id
            WHERE r.rental_id = %s
            """,
            (rental_id,),
        )
        dep = fetch_one(cur_dep)
        deposit_amount = float(dep["deposit_rate"] or 0) if dep else 0
        execute_sql(
            cur_update,
            "UPDATE rentals SET deposit_status = %s WHERE rental_id = %s",
            ("refunded", rental_id),
        )
        create_deposit_transaction(
            db,
            rental_id,
            "refund",
            deposit_amount,
            "Refunded because rental cancelled",
            payload.actor_user_id,
        )

    create_status_log(
        db,
        rental_id,
        previous_status,
        next_status,
        payload.remark or "Updated via status endpoint",
        payload.actor_user_id or rental["user_id"],
    )
    db.commit()
    return {"message": "Rental status updated"}

@app.put("/rentals/{rental_id}/condition-review")
def update_rental_condition_review(rental_id: int, payload: RentalConditionReviewUpdate, db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        "SELECT rental_id, rental_status, user_id, condition_before, condition_after FROM rentals WHERE rental_id = %s",
        (rental_id,),
    )
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    ensure_admin_actor(db, payload.actor_user_id)

    before_value = payload.condition_before if payload.condition_before is not None else rental.get("condition_before")
    after_value = payload.condition_after if payload.condition_after is not None else rental.get("condition_after")

    if before_value == rental.get("condition_before") and after_value == rental.get("condition_after"):
        raise HTTPException(status_code=400, detail="No condition updates provided")

    cur_update = get_cursor(db)
    execute_sql(
        cur_update,
        "UPDATE rentals SET condition_before = %s, condition_after = %s WHERE rental_id = %s",
        (before_value, after_value, rental_id),
    )

    create_status_log(
        db,
        rental_id,
        rental["rental_status"],
        rental["rental_status"],
        payload.review_note or "Admin reviewed equipment condition",
        payload.actor_user_id,
    )
    db.commit()
    return get_rental_with_join(db, rental_id)

@app.put("/rentals/{rental_id}/return")
def return_rental(rental_id: int, payload: RentalReturn, db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT r.rental_id, r.equipment_id, r.rental_status, r.user_id, e.deposit_rate
        FROM rentals r
        JOIN equipments e ON e.equipment_id = r.equipment_id
        WHERE r.rental_id = %s
        """,
        (rental_id,),
    )
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if not payload.actor_user_id:
        raise HTTPException(status_code=403, detail="actor_user_id is required")

    actor_role = get_user_role(db, payload.actor_user_id)
    is_admin = actor_role == "admin"

    if not is_admin and payload.actor_user_id != rental["user_id"]:
        raise HTTPException(status_code=403, detail="Only rental owner can request return")

    if rental["rental_status"] != "active":
        raise HTTPException(status_code=400, detail="Only active rental can be returned")

    cur_update = get_cursor(db)

    # Customer flow: request return and wait for admin inspection/penalty decision.
    if not is_admin:
        if rental.get("actual_return_date"):
            raise HTTPException(status_code=400, detail="Return request already submitted")

        execute_sql(
            cur_update,
            """
            UPDATE rentals
            SET actual_return_date = %s,
                condition_after = %s
            WHERE rental_id = %s
            """,
            (date.today(), payload.condition_after, rental_id),
        )

        create_status_log(
            db,
            rental_id,
            rental["rental_status"],
            rental["rental_status"],
            "Customer submitted return request; waiting admin inspection",
            payload.actor_user_id,
        )
        db.commit()
        return {
            "message": "Return request submitted. Waiting admin inspection.",
            "rental": get_rental_with_join(db, rental_id),
        }

    # Admin flow: finalize inspection, penalty, deposit action, and completion.
    execute_sql(
        cur_update,
        """
        UPDATE rentals
        SET actual_return_date = %s,
            condition_after = %s,
            penalty_fee = %s,
            deposit_status = %s,
            rental_status = %s
        WHERE rental_id = %s
        """,
        (
            rental.get("actual_return_date") or date.today(),
            payload.condition_after,
            payload.penalty_fee,
            payload.deposit_action,
            "completed",
            rental_id,
        ),
    )
    execute_sql(
        cur_update,
        "UPDATE equipments SET status = %s WHERE equipment_id = %s",
        ("available", rental["equipment_id"]),
    )

    deposit_rate = float(rental["deposit_rate"] or 0)
    penalty_fee = float(payload.penalty_fee or 0)
    if payload.deposit_action == "refunded":
        refund_amount = max(deposit_rate - penalty_fee, 0)
        create_deposit_transaction(
            db,
            rental_id,
            "refund",
            refund_amount,
            f"Refund after return (penalty {penalty_fee})",
            payload.actor_user_id,
        )
    elif payload.deposit_action == "confiscated":
        create_deposit_transaction(
            db,
            rental_id,
            "confiscate",
            deposit_rate,
            "Deposit confiscated after return",
            payload.actor_user_id,
        )
    else:
        create_deposit_transaction(
            db,
            rental_id,
            "penalty",
            penalty_fee,
            "Penalty settled at return",
            payload.actor_user_id,
        )

    create_status_log(
        db,
        rental_id,
        rental["rental_status"],
        "completed",
        f"Admin inspected return and closed rental (penalty: {penalty_fee:,.2f})",
        payload.actor_user_id,
    )
    db.commit()
    return get_rental_with_join(db, rental_id)

@app.put("/rentals/{rental_id}/cancel-request")
def cancel_rental_request(rental_id: int, payload: RentalCancelRequest, db: Any = Depends(get_db)):
    cur = get_cursor(db, dictionary=True)
    execute_sql(
        cur,
        """
        SELECT r.rental_id, r.user_id, r.rental_status, e.deposit_rate, e.equipment_id
        FROM rentals r
        JOIN equipments e ON e.equipment_id = r.equipment_id
        WHERE r.rental_id = %s
        """,
        (rental_id,),
    )
    rental = fetch_one(cur)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    ensure_owner_or_admin(db, payload.actor_user_id, rental["user_id"])
    if rental["rental_status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending rental can be cancelled")

    cur_update = get_cursor(db)
    execute_sql(
        cur_update,
        "UPDATE rentals SET rental_status = %s, deposit_status = %s WHERE rental_id = %s",
        ("cancelled", "refunded", rental_id),
    )
    execute_sql(
        cur_update,
        "UPDATE equipments SET status = %s WHERE equipment_id = %s",
        ("available", rental["equipment_id"]),
    )

    deposit_amount = float(rental["deposit_rate"] or 0)
    create_deposit_transaction(
        db,
        rental_id,
        "refund",
        deposit_amount,
        "Refunded because customer cancelled request",
        payload.actor_user_id,
    )
    create_status_log(
        db,
        rental_id,
        "pending",
        "cancelled",
        payload.remark or "Cancelled by customer/admin",
        payload.actor_user_id,
    )
    db.commit()
    return {"message": "Rental request cancelled"}