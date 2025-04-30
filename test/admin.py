from flask import Flask, render_template_string, request, redirect
from sqlalchemy import create_engine, text
import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy.pool import QueuePool


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
host_ip = "172.187.200.129"
user = 'agave'
password = 'agave'
port = '5433'
database = 'agave'
connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
#engine = create_engine(connection_url)
engine = create_engine(
    connection_url,
    pool_pre_ping=True,      # ✅ checks if connection is alive before using it
    pool_recycle=1800,       # ✅ recycle connections every 30 mins (optional but recommended)
    poolclass=QueuePool
)

# HTML template
template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Access Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: "Segoe UI", Arial, sans-serif;
            background-color: #f7f9fc;
            padding: 30px;
            margin: 0;
            color: #333;
        }
        h1 {
            margin-bottom: 10px;
            color: #2c3e50;
        }
        h2 {
            margin-top: 30px;
            color: #34495e;
        }
        form {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
        }
        label {
            min-width: 100px;
            align-self: center;
        }
        select, button {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #ccc;
            font-size: 14px;
        }
        button {
            background-color: #2ecc71;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #27ae60;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-top: 10px;
        }
        th, td {
            padding: 12px 16px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f1f1f1;
        }
        .action-form {
            margin: 0;
        }
        .action-form button {
            background-color: #e74c3c;
        }
        .action-form button:hover {
            background-color: #c0392b;
        }
        @media (max-width: 600px) {
            form {
                flex-direction: column;
            }
            label {
                margin-bottom: 5px;
            }
        }
    </style>
</head>
<body>
    <h1>Admin: Manage Access to <code>pred</code> Table</h1>

    <h2>Grant Access</h2>
    <form method="POST" action="/grant">
        <label for="seller_id">Seller:</label>
        <select name="seller_id" id="seller_id" required>
            {% for seller in sellers %}
                <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} ({{ seller['id'] }})</option>
            {% endfor %}
        </select>

        <label for="buyer_id">Buyer:</label>
        <select name="buyer_id" id="buyer_id" required>
            {% for buyer in buyers %}
                <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} ({{ buyer['id'] }})</option>
            {% endfor %}
        </select>

        <button type="submit">Grant Access</button>
    </form>

    <h2>Current Access Grants</h2>
    <table>
        <thead>
            <tr>
                <th>Seller</th>
                <th>Buyer</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
        {% for access in access_list %}
            <tr>
                <td>{{ access['seller_name'] }}</td>
                <td>{{ access['buyer_name'] }}</td>
                <td>
                    <form class="action-form" method="POST" action="/revoke">
                        <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
                        <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
                        <button type="submit">Revoke</button>
                    </form>
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""


# Helper Functions

def get_sellers_and_buyers():
    query = "SELECT id, registration_name, account_type FROM company"
    companies = pd.read_sql(query, engine)
    companies['account_type'] = companies['account_type'].str.lower()
    sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
    buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')
    return sellers, buyers

def get_company_name(company_id):
    query = "SELECT registration_name FROM company WHERE id = :company_id"
    with engine.connect() as conn:
        result = conn.execute(text(query), {"company_id": company_id}).fetchone()
    return result[0] if result else "Unknown"

def get_granted_accesses():
    query = """
        SELECT buyer_company_id AS buyer_id, seller_company_id AS seller_id
        FROM company_access_control
        WHERE status = 'approved' AND delete_time IS NULL
    """
    return pd.read_sql(query, engine).to_dict('records')

def log_access_change(seller_id, buyer_id, status):
    now = datetime.utcnow()

    with engine.begin() as conn:
        # Check if an entry exists regardless of status
        existing = conn.execute(text("""
            SELECT id, status FROM company_access_control
            WHERE seller_company_id = :seller_id AND buyer_company_id = :buyer_id
            ORDER BY create_time DESC
            LIMIT 1
        """), {"seller_id": seller_id, "buyer_id": buyer_id}).fetchone()

        if status == 'approved':
            if existing:
                # If status is not approved, update it
                if existing[1] != 'approved':
                    conn.execute(text("""
                        UPDATE company_access_control
                        SET status = 'approved',
                            update_time = :now,
                            delete_time = NULL,
                            updater = 'admin'
                        WHERE id = :id
                    """), {"id": existing[0], "now": now})
                # Else do nothing (already approved)
            else:
                # No row exists, safe to insert
                conn.execute(text("""
                    INSERT INTO company_access_control (
                        id, buyer_company_id, seller_company_id, requested_by_user_id, status,
                        create_time, update_time, creator, updater
                    ) VALUES (
                        :id, :buyer_id, :seller_id, :requested_by, 'approved',
                        :now, :now, 'admin', 'admin'
                    )
                """), {
                    "id": str(uuid.uuid4()),
                    "buyer_id": buyer_id,
                    "seller_id": seller_id,
                    "requested_by": "00000000-0000-0000-0000-000000000000",  # placeholder
                    "now": now
                })

        elif status == 'revoked' and existing:
            conn.execute(text("""
                UPDATE company_access_control
                SET status = 'revoked',
                    update_time = :now,
                    delete_time = :now,
                    updater = 'admin'
                WHERE id = :id
            """), {"id": existing[0], "now": now})


def copy_sellers_preds_to_buyer(buyer_id, seller_ids):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM pred WHERE company_id = :buyer_id"), {"buyer_id": buyer_id})
        for seller_id in seller_ids:
            seller_preds = pd.read_sql(
                text("SELECT * FROM pred WHERE company_id = :seller_id"),
                conn,
                params={"seller_id": seller_id}
            )
            if not seller_preds.empty:
                seller_preds['company_id'] = buyer_id
                if 'id' in seller_preds.columns:
                    seller_preds['id'] = [str(uuid.uuid4()) for _ in range(len(seller_preds))]
                if 'container_id' in seller_preds.columns:
                    suffix = seller_id[:8]
                    seller_preds['container_id'] = seller_preds['container_id'].astype(str) + f"_{suffix}"
                seller_preds.to_sql('pred', con=conn, if_exists='append', index=False)

# Routes

@app.route('/')
def index():
    sellers, buyers = get_sellers_and_buyers()
    accesses = get_granted_accesses()
    access_list = []
    for access in accesses:
        access_list.append({
            'seller_id': access['seller_id'],
            'buyer_id': access['buyer_id'],
            'seller_name': get_company_name(access['seller_id']),
            'buyer_name': get_company_name(access['buyer_id']),
        })
    return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

@app.route('/grant', methods=['POST'])
def grant_access():
    seller_id = request.form['seller_id']
    buyer_id = request.form['buyer_id']
    log_access_change(seller_id, buyer_id, 'approved')

    all_seller_ids = [
        a['seller_id'] for a in get_granted_accesses()
        if a['buyer_id'] == buyer_id
    ]
    copy_sellers_preds_to_buyer(buyer_id, all_seller_ids)
    return redirect('/')

@app.route('/revoke', methods=['POST'])
def revoke_access():
    seller_id = request.form['seller_id']
    buyer_id = request.form['buyer_id']
    log_access_change(seller_id, buyer_id, 'revoked')

    remaining_seller_ids = [
        a['seller_id'] for a in get_granted_accesses()
        if a['buyer_id'] == buyer_id
    ]
    copy_sellers_preds_to_buyer(buyer_id, remaining_seller_ids)
    return redirect('/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)







# from flask import Flask, render_template_string, request, redirect
# from sqlalchemy import create_engine, text
# import pandas as pd
# import uuid
# from datetime import datetime

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # Database connection
# host_ip = "172.187.200.129"
# user = 'agave'
# password = 'agave'
# port = '5433'
# database = 'agave'
# connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
# engine = create_engine(connection_url)

# #HTML template remains unchanged...
# template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Admin Access Control</title>
#     <style>
#         body { font-family: Arial; background-color: #f4f4f4; padding: 20px; color: #333; }
#         h1, h2 { color: #111; }
#         select, button { margin: 5px; padding: 5px; }
#         table { border-collapse: collapse; margin-top: 20px; }
#         th, td { border: 1px solid #888; padding: 8px 12px; }
#     </style>
# </head>
# <body>
#     <h1>Admin: Manage Table Access (<code>pred</code>)</h1>

#     <h2>Grant Access</h2>
#     <form method="POST" action="/grant">
#         <label>Seller:</label>
#         <select name="seller_id" required>
#             {% for seller in sellers %}
#                 <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} ({{ seller['id'] }})</option>
#             {% endfor %}
#         </select>

#         <label>Buyer:</label>
#         <select name="buyer_id" required>
#             {% for buyer in buyers %}
#                 <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} ({{ buyer['id'] }})</option>
#             {% endfor %}
#         </select>

#         <button type="submit">Grant Access</button>
#     </form>

#     <h2>Current Access Grants</h2>
#     <table>
#         <tr><th>Seller</th><th>Buyer</th><th>Action</th></tr>
#         {% for access in access_list %}
#         <tr>
#             <td>{{ access['seller_name'] }}</td>
#             <td>{{ access['buyer_name'] }}</td>
#             <td>
#                 <form method="POST" action="/revoke">
#                     <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
#                     <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
#                     <button type="submit">Revoke</button>
#                 </form>
#             </td>
#         </tr>
#         {% endfor %}
#     </table>
# </body>
# </html>
# """

# # Helper Functions

# def get_sellers_and_buyers():
#     query = "SELECT id, registration_name, account_type FROM company"
#     companies = pd.read_sql(query, engine)
#     companies['account_type'] = companies['account_type'].str.lower()
#     sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
#     buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')
#     return sellers, buyers

# def get_company_name(company_id):
#     query = "SELECT registration_name FROM company WHERE id = :company_id"
#     with engine.connect() as conn:
#         result = conn.execute(text(query), {"company_id": company_id}).fetchone()
#     return result[0] if result else "Unknown"

# def get_granted_accesses():
#     query = """
#         SELECT buyer_company_id AS buyer_id, seller_company_id AS seller_id
#         FROM company_access_control
#         WHERE status = 'granted' AND delete_time IS NULL
#     """
#     return pd.read_sql(query, engine).to_dict('records')

# def log_access_change(seller_id, buyer_id, status):
#     # Check if existing row exists
#     query = """
#         SELECT id FROM company_access_control
#         WHERE seller_company_id = :seller_id AND buyer_company_id = :buyer_id
#         AND delete_time IS NULL
#         ORDER BY create_time DESC
#         LIMIT 1
#     """
#     now = datetime.utcnow()
#     with engine.begin() as conn:
#         existing = conn.execute(text(query), {"seller_id": seller_id, "buyer_id": buyer_id}).fetchone()

#         if status == 'granted':
#             if existing:
#                 # Update existing record
#                 conn.execute(text("""
#                     UPDATE company_access_control
#                     SET status = 'granted', update_time = :now, updater = 'admin'
#                     WHERE id = :id
#                 """), {"id": existing[0], "now": now})
#             else:
#                 # Insert new record
#                 # Add requested_by_user_id in the INSERT
#                 # Replace 'granted' with 'approved' in your SQL
#                 conn.execute(text("""
#                     INSERT INTO company_access_control (
#                         id, buyer_company_id, seller_company_id, requested_by_user_id, status,
#                         create_time, update_time, creator, updater
#                     ) VALUES (
#                         :id, :buyer_id, :seller_id, :requested_by, 'approved',
#                         :now, :now, 'admin', 'admin'
#                     )
#                 """), {
#                     "id": str(uuid.uuid4()),
#                     "buyer_id": buyer_id,
#                     "seller_id": seller_id,
#                     "requested_by": "00000000-0000-0000-0000-000000000000",  # Use real user ID
#                     "now": now
#                 })
#         elif status == 'revoked' and existing:
#             # Soft delete or revoke the access
#             conn.execute(text("""
#                 UPDATE company_access_control
#                 SET status = 'revoked', update_time = :now, delete_time = :now, updater = 'admin'
#                 WHERE id = :id
#             """), {"id": existing[0], "now": now})

# def copy_sellers_preds_to_buyer(buyer_id, seller_ids):
#     with engine.begin() as conn:
#         conn.execute(text("DELETE FROM pred WHERE company_id = :buyer_id"), {"buyer_id": buyer_id})
#         for seller_id in seller_ids:
#             seller_preds = pd.read_sql(
#                 text("SELECT * FROM pred WHERE company_id = :seller_id"),
#                 conn,
#                 params={"seller_id": seller_id}
#             )
#             if not seller_preds.empty:
#                 seller_preds['company_id'] = buyer_id
#                 if 'id' in seller_preds.columns:
#                     seller_preds['id'] = [str(uuid.uuid4()) for _ in range(len(seller_preds))]
#                 if 'container_id' in seller_preds.columns:
#                     suffix = seller_id[:8]
#                     seller_preds['container_id'] = seller_preds['container_id'].astype(str) + f"_{suffix}"
#                 seller_preds.to_sql('pred', con=conn, if_exists='append', index=False)

# # Routes

# @app.route('/')
# def index():
#     sellers, buyers = get_sellers_and_buyers()
#     accesses = get_granted_accesses()
#     access_list = []
#     for access in accesses:
#         access_list.append({
#             'seller_id': access['seller_id'],
#             'buyer_id': access['buyer_id'],
#             'seller_name': get_company_name(access['seller_id']),
#             'buyer_name': get_company_name(access['buyer_id']),
#         })
#     return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

# @app.route('/grant', methods=['POST'])
# def grant_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']
#     log_access_change(seller_id, buyer_id, 'granted')
#     all_seller_ids = [a['seller_id'] for a in get_granted_accesses() if a['buyer_id'] == buyer_id]
#     copy_sellers_preds_to_buyer(buyer_id, all_seller_ids)
#     return redirect('/')

# @app.route('/revoke', methods=['POST'])
# def revoke_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']
#     log_access_change(seller_id, buyer_id, 'revoked')
#     remaining_seller_ids = [a['seller_id'] for a in get_granted_accesses() if a['buyer_id'] == buyer_id]
#     copy_sellers_preds_to_buyer(buyer_id, remaining_seller_ids)
#     return redirect('/')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)







# from flask import Flask, render_template_string, request, redirect
# from sqlalchemy import create_engine, text
# import pandas as pd
# import uuid

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # Database connection
# host_ip = "172.187.200.129"
# user = 'agave'
# password = 'agave'
# port = '5433'
# database = 'agave'
# connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
# engine = create_engine(connection_url)

# # In-memory access tracker
# granted_accesses = []

# # HTML template
# template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Admin Access Control</title>
#     <style>
#         body { font-family: Arial; background-color: #f4f4f4; padding: 20px; color: #333; }
#         h1, h2 { color: #111; }
#         select, button { margin: 5px; padding: 5px; }
#         table { border-collapse: collapse; margin-top: 20px; }
#         th, td { border: 1px solid #888; padding: 8px 12px; }
#     </style>
# </head>
# <body>
#     <h1>Admin: Manage Table Access (<code>pred</code>)</h1>

#     <h2>Grant Access</h2>
#     <form method="POST" action="/grant">
#         <label>Seller:</label>
#         <select name="seller_id" required>
#             {% for seller in sellers %}
#                 <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} ({{ seller['id'] }})</option>
#             {% endfor %}
#         </select>

#         <label>Buyer:</label>
#         <select name="buyer_id" required>
#             {% for buyer in buyers %}
#                 <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} ({{ buyer['id'] }})</option>
#             {% endfor %}
#         </select>

#         <button type="submit">Grant Access</button>
#     </form>

#     <h2>Current Access Grants</h2>
#     <table>
#         <tr><th>Seller</th><th>Buyer</th><th>Action</th></tr>
#         {% for access in access_list %}
#         <tr>
#             <td>{{ access['seller_name'] }}</td>
#             <td>{{ access['buyer_name'] }}</td>
#             <td>
#                 <form method="POST" action="/revoke">
#                     <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
#                     <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
#                     <button type="submit">Revoke</button>
#                 </form>
#             </td>
#         </tr>
#         {% endfor %}
#     </table>
# </body>
# </html>
# """

# # Helper Functions

# def get_sellers_and_buyers():
#     query = "SELECT id, registration_name, account_type FROM company"
#     companies = pd.read_sql(query, engine)
#     companies['account_type'] = companies['account_type'].str.lower()
#     sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
#     buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')
#     return sellers, buyers

# def get_company_name(company_id):
#     query = "SELECT registration_name FROM company WHERE id = :company_id"
#     with engine.connect() as conn:
#         result = conn.execute(text(query), {"company_id": company_id}).fetchone()
#     return result[0] if result else "Unknown"

# def copy_sellers_preds_to_buyer(buyer_id, seller_ids):
#     with engine.begin() as conn:
#         # Step 1: Delete existing buyer's pred rows
#         conn.execute(text("""
#             DELETE FROM pred
#             WHERE company_id = :buyer_id
#         """), {"buyer_id": buyer_id})

#         # Step 2: Copy seller preds
#         for seller_id in seller_ids:
#             seller_preds = pd.read_sql(
#                 text("SELECT * FROM pred WHERE company_id = :seller_id"),
#                 conn,
#                 params={"seller_id": seller_id}
#             )

#             if not seller_preds.empty:
#                 seller_preds['company_id'] = buyer_id

#                 # ✅ Regenerate a new UUID for 'id'
#                 if 'id' in seller_preds.columns:
#                     seller_preds['id'] = [str(uuid.uuid4()) for _ in range(len(seller_preds))]

#                 # ✅ Modify container_id to avoid conflict
#                 if 'container_id' in seller_preds.columns:
#                     suffix = seller_id[:8]  # first 8 chars of seller_id
#                     seller_preds['container_id'] = seller_preds['container_id'].astype(str) + f"_{suffix}"

#                 # ✅ Now safe to insert
#                 seller_preds.to_sql('pred', con=conn, if_exists='append', index=False)



# # Routes

# @app.route('/')
# def index():
#     sellers, buyers = get_sellers_and_buyers()
#     access_list = []
#     for access in granted_accesses:
#         seller_name = get_company_name(access['seller_id'])
#         buyer_name = get_company_name(access['buyer_id'])
#         access_list.append({
#             'seller_id': access['seller_id'],
#             'buyer_id': access['buyer_id'],
#             'seller_name': seller_name,
#             'buyer_name': buyer_name
#         })
#     return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

# @app.route('/grant', methods=['POST'])
# def grant_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     if not any(a['seller_id'] == seller_id and a['buyer_id'] == buyer_id for a in granted_accesses):
#         granted_accesses.append({'seller_id': seller_id, 'buyer_id': buyer_id})

#     # Collect all sellers granted to this buyer
#     seller_ids = [a['seller_id'] for a in granted_accesses if a['buyer_id'] == buyer_id]
#     copy_sellers_preds_to_buyer(buyer_id, seller_ids)

#     return redirect('/')

# @app.route('/revoke', methods=['POST'])
# def revoke_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     global granted_accesses
#     granted_accesses = [
#         a for a in granted_accesses
#         if not (a['seller_id'] == seller_id and a['buyer_id'] == buyer_id)
#     ]

#     # Collect remaining sellers for this buyer
#     seller_ids = [a['seller_id'] for a in granted_accesses if a['buyer_id'] == buyer_id]
#     copy_sellers_preds_to_buyer(buyer_id, seller_ids)

#     return redirect('/')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)






# from flask import Flask, render_template_string, request, redirect
# from sqlalchemy import create_engine, text
# import pandas as pd
# import uuid

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # DB connection
# host_ip = "172.187.200.129"
# user = 'agave'
# password = 'agave'
# port = '5433'
# database = 'agave'
# connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
# engine = create_engine(connection_url)

# # In-memory access tracker
# granted_accesses = []

# # HTML template
# template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Admin Access Control</title>
#     <style>
#         body { font-family: Arial; background-color: #f4f4f4; padding: 20px; color: #333; }
#         h1, h2 { color: #111; }
#         select, button { margin: 5px; padding: 5px; }
#         table { border-collapse: collapse; margin-top: 20px; }
#         th, td { border: 1px solid #888; padding: 8px 12px; }
#     </style>
# </head>
# <body>
#     <h1>Admin: Manage Table Access (<code>pred</code>)</h1>

#     <h2>Grant Access</h2>
#     <form method="POST" action="/grant">
#         <label>Seller:</label>
#         <select name="seller_id" required>
#             {% for seller in sellers %}
#                 <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} ({{ seller['id'] }})</option>
#             {% endfor %}
#         </select>

#         <label>Buyer:</label>
#         <select name="buyer_id" required>
#             {% for buyer in buyers %}
#                 <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} ({{ buyer['id'] }})</option>
#             {% endfor %}
#         </select>

#         <button type="submit">Grant Access</button>
#     </form>

#     <h2>Current Access Grants</h2>
#     <table>
#         <tr><th>Seller</th><th>Buyer</th><th>Action</th></tr>
#         {% for access in access_list %}
#         <tr>
#             <td>{{ access['seller_name'] }}</td>
#             <td>{{ access['buyer_name'] }}</td>
#             <td>
#                 <form method="POST" action="/revoke">
#                     <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
#                     <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
#                     <button type="submit">Revoke</button>
#                 </form>
#             </td>
#         </tr>
#         {% endfor %}
#     </table>
# </body>
# </html>
# """

# # Helper functions
# def get_sellers_and_buyers():
#     query = "SELECT id, registration_name, account_type FROM company"
#     companies = pd.read_sql(query, engine)
#     companies['account_type'] = companies['account_type'].str.lower()
#     sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
#     buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')
#     return sellers, buyers

# def get_company_name(company_id):
#     query = "SELECT registration_name FROM company WHERE id = :company_id"
#     with engine.connect() as conn:
#         result = conn.execute(text(query), {"company_id": company_id}).fetchone()
#     return result[0] if result else "Unknown"

# def copy_pred_from_seller_to_buyer(seller_id, buyer_id):
#     with engine.begin() as conn:
#         # Fetch seller's pred rows
#         seller_preds = pd.read_sql(
#             text("SELECT * FROM pred WHERE company_id = :seller_id"),
#             conn,
#             params={"seller_id": seller_id}
#         )

#         # Replace seller's company_id with buyer's
#         if not seller_preds.empty:
#             seller_preds['company_id'] = buyer_id
#             # Optional: assign new UUIDs to avoid PK conflicts if needed
#             if 'id' in seller_preds.columns:
#                 seller_preds['id'] = [str(uuid.uuid4()) for _ in range(len(seller_preds))]
#             seller_preds.to_sql('pred', con=conn, if_exists='append', index=False)

# def remove_pred_for_buyer(buyer_id, seller_id):
#     with engine.begin() as conn:
#         # Delete only rows cloned from that seller
#         conn.execute(text("""
#             DELETE FROM pred
#             WHERE company_id = :buyer_id
#         """), {"buyer_id": buyer_id})

# @app.route('/')
# def index():
#     sellers, buyers = get_sellers_and_buyers()
#     access_list = []
#     for access in granted_accesses:
#         seller_name = get_company_name(access['seller_id'])
#         buyer_name = get_company_name(access['buyer_id'])
#         access_list.append({
#             'seller_id': access['seller_id'],
#             'buyer_id': access['buyer_id'],
#             'seller_name': seller_name,
#             'buyer_name': buyer_name
#         })
#     return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

# @app.route('/grant', methods=['POST'])
# def grant_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     # Prevent duplicate grants
#     if not any(a['seller_id'] == seller_id and a['buyer_id'] == buyer_id for a in granted_accesses):
#         granted_accesses.append({'seller_id': seller_id, 'buyer_id': buyer_id})
#         copy_pred_from_seller_to_buyer(seller_id, buyer_id)

#     return redirect('/')

# @app.route('/revoke', methods=['POST'])
# def revoke_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     global granted_accesses
#     granted_accesses = [
#         a for a in granted_accesses
#         if not (a['seller_id'] == seller_id and a['buyer_id'] == buyer_id)
#     ]

#     remove_pred_for_buyer(buyer_id, seller_id)
#     return redirect('/')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)




# from flask import Flask, render_template_string, request, redirect
# from sqlalchemy import create_engine
# import pandas as pd

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # Database connection
# host_ip = "172.187.200.129"
# user = 'agave'
# password = 'agave'
# port = '5433'
# database = 'agave'
# connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
# engine = create_engine(connection_url)

# # In-memory access grant store
# granted_accesses = []

# # HTML Template
# template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Admin Access Control</title>
#     <style>
#         body { font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; color: #222; }
#         h1, h2 { color: #333; }
#         select, button { margin: 5px; padding: 5px; }
#         table { border-collapse: collapse; margin-top: 20px; }
#         th, td { border: 1px solid #888; padding: 8px 12px; }
#     </style>
# </head>
# <body>
#     <h1>Admin: Manage Table Access (<code>pred</code>)</h1>

#     <h2>Grant Access</h2>
#     <form method="POST" action="/grant">
#         <label for="seller_id">Seller:</label>
#         <select name="seller_id" required>
#             {% for seller in sellers %}
#                 <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} (ID: {{ seller['id'] }})</option>
#             {% endfor %}
#         </select>

#         <label for="buyer_id">Buyer:</label>
#         <select name="buyer_id" required>
#             {% for buyer in buyers %}
#                 <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} (ID: {{ buyer['id'] }})</option>
#             {% endfor %}
#         </select>

#         <button type="submit">Grant Access</button>
#     </form>

#     <h2>Current Access Grants</h2>
#     <table>
#         <tr>
#             <th>Seller</th>
#             <th>Buyer</th>
#             <th>Action</th>
#         </tr>
#         {% for access in access_list %}
#         <tr>
#             <td>{{ access['seller_name'] }}</td>
#             <td>{{ access['buyer_name'] }}</td>
#             <td>
#                 <form method="POST" action="/revoke" style="display:inline;">
#                     <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
#                     <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
#                     <button type="submit">Revoke</button>
#                 </form>
#             </td>
#         </tr>
#         {% endfor %}
#     </table>
# </body>
# </html>
# """

# def get_sellers_and_buyers():
#     query = "SELECT id, registration_name, account_type FROM company"
#     companies = pd.read_sql(query, engine)

#     # Normalize account_type to lowercase
#     companies['account_type'] = companies['account_type'].str.lower()

#     sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
#     buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')

#     return sellers, buyers

# def get_company_name(company_id):
#     query = "SELECT registration_name FROM company WHERE id = %s"
#     result = engine.execute(query, (company_id,)).fetchone()
#     return result[0] if result else "Unknown"

# @app.route('/')
# def index():
#     sellers, buyers = get_sellers_and_buyers()

#     access_list = []
#     for access in granted_accesses:
#         seller_name = get_company_name(access['seller_id'])
#         buyer_name = get_company_name(access['buyer_id'])
#         access_list.append({
#             'seller_id': access['seller_id'],
#             'buyer_id': access['buyer_id'],
#             'seller_name': seller_name,
#             'buyer_name': buyer_name
#         })

#     return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

# @app.route('/grant', methods=['POST'])
# def grant_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     # Avoid duplicate grants
#     if not any(a['seller_id'] == seller_id and a['buyer_id'] == buyer_id for a in granted_accesses):
#         granted_accesses.append({'seller_id': seller_id, 'buyer_id': buyer_id})

#     return redirect('/')

# @app.route('/revoke', methods=['POST'])
# def revoke_access():
#     seller_id = request.form['seller_id']
#     buyer_id = request.form['buyer_id']

#     global granted_accesses
#     granted_accesses = [
#         a for a in granted_accesses
#         if not (a['seller_id'] == seller_id and a['buyer_id'] == buyer_id)
#     ]

#     return redirect('/')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)






# from flask import Flask, render_template_string, request, redirect
# from sqlalchemy import create_engine
# import pandas as pd

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Needed for session (if you want later)

# # Database connection
# host_ip = "172.187.200.129"
# user = 'agave'
# password = 'agave'
# port = '5433'
# database = 'agave'

# connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
# engine = create_engine(connection_url)

# # In-memory list to store granted accesses
# granted_accesses = []  # Each item will be a dict {seller_id, buyer_id}

# # HTML Template
# template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Admin Access Control (No DB)</title>
# </head>
# <body>
#     <h1>Admin: Manage Table Access (pred)</h1>

#     <h2>Grant Access</h2>
#     <form method="POST" action="/grant">
#         <label for="seller_id">Seller:</label>
#         <select name="seller_id" required>
#             {% for seller in sellers %}
#                 <option value="{{ seller['id'] }}">{{ seller['name'] }} (ID: {{ seller['id'] }})</option>
#             {% endfor %}
#         </select>

#         <label for="buyer_id">Buyer:</label>
#         <select name="buyer_id" required>
#             {% for buyer in buyers %}
#                 <option value="{{ buyer['id'] }}">{{ buyer['name'] }} (ID: {{ buyer['id'] }})</option>
#             {% endfor %}
#         </select>

#         <button type="submit">Grant Access</button>
#     </form>

#     <h2>Current Access Grants</h2>
#     <table border="1">
#         <tr>
#             <th>Seller</th>
#             <th>Buyer</th>
#             <th>Action</th>
#         </tr>
#         {% for access in access_list %}
#         <tr>
#             <td>{{ access['seller_name'] }}</td>
#             <td>{{ access['buyer_name'] }}</td>
#             <td>
#                 <form method="POST" action="/revoke" style="display:inline;">
#                     <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
#                     <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
#                     <button type="submit">Revoke</button>
#                 </form>
#             </td>
#         </tr>
#         {% endfor %}
#     </table>
# </body>
# </html>
# """

# def get_sellers_and_buyers():
#     query = "SELECT id, registration_name, account_type FROM company"
#     companies = pd.read_sql(query, engine)
#     sellers = companies[companies['account_type'] == 'seller'].to_dict('records')
#     buyers = companies[companies['account_type'] == 'buyer'].to_dict('records')
#     return sellers, buyers

# def get_company_name(company_id):
#     query = "SELECT name FROM company WHERE id = %s"
#     result = engine.execute(query, (company_id,)).fetchone()
#     return result[0] if result else "Unknown"

# @app.route('/')
# def index():
#     sellers, buyers = get_sellers_and_buyers()

#     # Prepare current access list with names
#     access_list = []
#     for access in granted_accesses:
#         seller_name = get_company_name(access['seller_id'])
#         buyer_name = get_company_name(access['buyer_id'])
#         access_list.append({
#             'seller_id': access['seller_id'],
#             'buyer_id': access['buyer_id'],
#             'seller_name': seller_name,
#             'buyer_name': buyer_name
#         })

#     return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

# @app.route('/grant', methods=['POST'])
# def grant_access():
#     seller_id = int(request.form['seller_id'])
#     buyer_id = int(request.form['buyer_id'])

#     # Avoid duplicate grants
#     if not any(access['seller_id'] == seller_id and access['buyer_id'] == buyer_id for access in granted_accesses):
#         granted_accesses.append({
#             'seller_id': seller_id,
#             'buyer_id': buyer_id
#         })

#     return redirect('/')

# @app.route('/revoke', methods=['POST'])
# def revoke_access():
#     seller_id = int(request.form['seller_id'])
#     buyer_id = int(request.form['buyer_id'])

#     # Remove the matching access
#     global granted_accesses
#     granted_accesses = [
#         access for access in granted_accesses
#         if not (access['seller_id'] == seller_id and access['buyer_id'] == buyer_id)
#     ]

#     return redirect('/')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)
