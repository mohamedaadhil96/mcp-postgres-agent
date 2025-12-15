# main.py
# PostgreSQL MCP Server
import psycopg2
from psycopg2.extras import RealDictCursor
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD"),
}


mcp = FastMCP("postgres-mcp-server")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@mcp.tool()
def list_tables(schema: str = "public") -> List[str]:
    """List tables in a PostgreSQL schema"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
                """,
                (schema,),
            )
            return [row[0] for row in cur.fetchall()]


@mcp.tool()
def describe_table(table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
    """Describe columns of a table"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table_name),
            )
            return cur.fetchall()


@mcp.tool()
def run_select_query(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Run a SAFE SELECT query only.
    Non-SELECT queries are rejected.
    """
    if not query.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed")

    limited_query = f"{query.rstrip(';')} LIMIT {limit}"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(limited_query)
            return cur.fetchall()


@mcp.tool()
def search_movies(
    search_term: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search for movies by title/description, genre, or release year.
    """
    query = """
        SELECT 
            f.film_id,
            f.title,
            c.name as genre,
            f.release_year,
            f.rental_rate,
            f.rating,
            f.description
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    if search_term:
        query += " AND (f.title ILIKE %s OR f.description ILIKE %s)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if genre:
        query += " AND c.name ILIKE %s"
        params.append(f"%{genre}%")

    if year:
        query += " AND f.release_year = %s"
        params.append(year)

    query += " ORDER BY f.title LIMIT %s"
    params.append(limit)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall()


@mcp.tool()
def get_customer_history(customer_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get rental history for a customer.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    r.rental_id,
                    r.rental_date,
                    r.return_date,
                    f.title,
                    p.amount
                FROM rental r
                JOIN inventory i ON r.inventory_id = i.inventory_id
                JOIN film f ON i.film_id = f.film_id
                LEFT JOIN payment p ON r.rental_id = p.rental_id
                WHERE r.customer_id = %s
                ORDER BY r.rental_date DESC
                LIMIT %s
                """,
                (customer_id, limit),
            )
            return cur.fetchall()


@mcp.tool()
def rent_movie(customer_id: int, inventory_id: int, staff_id: int) -> str:
    """
    Rent a movie (create a new rental).
    Raises error if inventory is not available.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check availability
            cur.execute(
                """
                SELECT rental_id 
                FROM rental 
                WHERE inventory_id = %s AND return_date IS NULL
                """,
                (inventory_id,),
            )
            if cur.fetchone():
                return f"Error: Inventory item {inventory_id} is already rented out."

            # Create rental
            cur.execute(
                """
                INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id)
                VALUES (NOW(), %s, %s, %s)
                RETURNING rental_id
                """,
                (inventory_id, customer_id, staff_id),
            )
            rental_id = cur.fetchone()[0]
            conn.commit()
            return f"Successfully rented. Rental ID: {rental_id}"


@mcp.tool()
def return_movie(rental_id: int) -> str:
    """
    Return a rented movie (update return date).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if rental exists and not already returned
            cur.execute(
                "SELECT return_date FROM rental WHERE rental_id = %s", (rental_id,)
            )
            row = cur.fetchone()
            if not row:
                return f"Error: Rental ID {rental_id} not found."
            if row[0]:
                return f"Error: Rental ID {rental_id} already returned on {row[0]}."

            # Update return date
            cur.execute(
                """
                UPDATE rental 
                SET return_date = NOW() 
                WHERE rental_id = %s
                """,
                (rental_id,),
            )
            conn.commit()
            return f"Successfully returned rental {rental_id}."


@mcp.tool()
def get_available_inventory(film_id: int) -> List[Dict[str, Any]]:
    """
    Get available inventory for a film (items not currently rented out).
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT inventory_id, store_id
                FROM inventory
                WHERE film_id = %s
                AND inventory_id NOT IN (
                    SELECT inventory_id FROM rental WHERE return_date IS NULL
                )
                """,
                (film_id,),
            )
            return cur.fetchall()


@mcp.tool()
def analyze_revenue(by_category: bool = True) -> List[Dict[str, Any]]:
    """
    Analyze revenue. Default is by category.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if by_category:
                cur.execute(
                    """
                    SELECT c.name as category, SUM(p.amount) as revenue
                    FROM payment p
                    JOIN rental r ON p.rental_id = r.rental_id
                    JOIN inventory i ON r.inventory_id = i.inventory_id
                    JOIN film_category fc ON i.film_id = fc.film_id
                    JOIN category c ON fc.category_id = c.category_id
                    GROUP BY c.name
                    ORDER BY revenue DESC
                    """
                )
            else:
                # By Store
                cur.execute(
                    """
                    SELECT s.store_id, SUM(p.amount) as revenue
                    FROM payment p
                    JOIN staff s ON p.staff_id = s.staff_id
                    GROUP BY s.store_id
                    ORDER BY revenue DESC
                    """
                )
            return cur.fetchall()


if __name__ == "__main__":
    mcp.run()
