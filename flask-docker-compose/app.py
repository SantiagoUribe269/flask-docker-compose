from flask import Flask, jsonify, request
from psycopg_pool import ConnectionPool
import os

def dbConnect():
    """Create a connection pool to connect to Postgres."""

    db_host = os.environ.get('DB_HOST')
    db_database = os.environ.get('DB_DATABASE')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')

    # Create a connection URL for the database.
    url = f'host = {db_host} dbname = {db_database} user = {db_user} password = {db_password}'

    # Connect to the Postgres database.
    pool = ConnectionPool(url)
    pool.wait()

    return pool

# Create a connection pool for Postgres.
pool = dbConnect()

app = Flask(__name__)

# existing code
@app.route('/volumes', methods=['GET', 'POST'])
def volumes():
    filename = '/data/test.txt'

    if request.method == 'POST':
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            f.write('Customer record')

        return 'Saved!', 201
    else:
        f = open(filename, 'r')

        return f.read(), 200


def save_item(priority, task, table, pool):
    """Inserts a new task into the Postgres database."""

    # Connect to an existing database
    with pool.connection() as conn:

        # Open a cursor to perform database operations
        with conn.cursor() as cur:

            # Prepare the database query.
            query = f'INSERT INTO {table} (priority, task) VALUES (%s, %s)'

            # Send the query to PostgreSQL.
            cur.execute(query, (priority, task))

            # Make the changes to the database persistent
            conn.commit()


def get_items(table, pool):
    """Get all the items from the Postgres database."""

    # Connect to an existing database
    with pool.connection() as conn:

        # Open a cursor to perform database operations
        with conn.cursor() as cur:

            # Prepare the database query.
            query = f'SELECT item_id, priority, task FROM {table}'

            # Send the query to PostgreSQL.
            cur.execute(query)

            items = []

            for rec in cur:
                item = {'id': rec[0], 'priority': rec[1], 'task':  rec[2]}
                items.append(item)

            # Return a list of items.
            return items


@app.route('/items', methods=['GET', 'POST'])
def items():
    match request.method:
        case 'POST':
            req = request.get_json()
            save_item(req['priority'], req['task'], 'item', pool)

            return {'message': 'item saved!'}, 201
        case 'GET':
            items = get_items('item', pool)

            return items, 200
        case _:
            return {'message': 'method not allowed'}, 405
        
@app.route("/about", methods=["GET"])
def about():
    version = os.getenv("APP_VERSION")
    return jsonify({"app_version": version}), 200

@app.route("/secrets", methods=["GET"])
def secrets():
    creds = dict()
    creds["DB_PASSWORD"] = os.getenv("DB_PASSWORD")
    creds["api_key"] = open("/run/secrets/api_key", "r").read()
    creds["api_key_v2"] = open("/api_key", "r").read()
    return jsonify(creds), 200

@app.route("/config", methods=["GET"])
def config():
    creds = dict()
    creds["config_dev"] = open("/config-dev.yml", "r").read()
    return jsonify(creds), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)