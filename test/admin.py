from flask import Flask, render_template_string, request, redirect
from sqlalchemy import create_engine, text
import pandas as pd
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
host_ip = "172.187.200.129"
user = 'agave'
password = 'agave'
port = '5433'
database = 'agave'
connection_url = f"postgresql+psycopg2://{user}:{password}@{host_ip}:{port}/{database}"
engine = create_engine(connection_url)

# In-memory access tracker
granted_accesses = []

# HTML template
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Access Control</title>
    <style>
        body { font-family: Arial; background-color: #f4f4f4; padding: 20px; color: #333; }
        h1, h2 { color: #111; }
        select, button { margin: 5px; padding: 5px; }
        table { border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #888; padding: 8px 12px; }
    </style>
</head>
<body>
    <h1>Admin: Manage Table Access (<code>pred</code>)</h1>

    <h2>Grant Access</h2>
    <form method="POST" action="/grant">
        <label>Seller:</label>
        <select name="seller_id" required>
            {% for seller in sellers %}
                <option value="{{ seller['id'] }}">{{ seller['registration_name'] }} ({{ seller['id'] }})</option>
            {% endfor %}
        </select>

        <label>Buyer:</label>
        <select name="buyer_id" required>
            {% for buyer in buyers %}
                <option value="{{ buyer['id'] }}">{{ buyer['registration_name'] }} ({{ buyer['id'] }})</option>
            {% endfor %}
        </select>

        <button type="submit">Grant Access</button>
    </form>

    <h2>Current Access Grants</h2>
    <table>
        <tr><th>Seller</th><th>Buyer</th><th>Action</th></tr>
        {% for access in access_list %}
        <tr>
            <td>{{ access['seller_name'] }}</td>
            <td>{{ access['buyer_name'] }}</td>
            <td>
                <form method="POST" action="/revoke">
                    <input type="hidden" name="seller_id" value="{{ access['seller_id'] }}">
                    <input type="hidden" name="buyer_id" value="{{ access['buyer_id'] }}">
                    <button type="submit">Revoke</button>
                </form>
            </td>
        </tr>
        {% endfor %}
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

def copy_sellers_preds_to_buyer(buyer_id, seller_ids):
    with engine.begin() as conn:
        # Step 1: Delete existing buyer's pred rows
        conn.execute(text("""
            DELETE FROM pred
            WHERE company_id = :buyer_id
        """), {"buyer_id": buyer_id})

        # Step 2: Copy seller preds
        for seller_id in seller_ids:
            seller_preds = pd.read_sql(
                text("SELECT * FROM pred WHERE company_id = :seller_id"),
                conn,
                params={"seller_id": seller_id}
            )

            if not seller_preds.empty:
                seller_preds['company_id'] = buyer_id

                # ✅ Regenerate a new UUID for 'id'
                if 'id' in seller_preds.columns:
                    seller_preds['id'] = [str(uuid.uuid4()) for _ in range(len(seller_preds))]

                # ✅ Modify container_id to avoid conflict
                if 'container_id' in seller_preds.columns:
                    suffix = seller_id[:8]  # first 8 chars of seller_id
                    seller_preds['container_id'] = seller_preds['container_id'].astype(str) + f"_{suffix}"

                # ✅ Now safe to insert
                seller_preds.to_sql('pred', con=conn, if_exists='append', index=False)



# Routes

@app.route('/')
def index():
    sellers, buyers = get_sellers_and_buyers()
    access_list = []
    for access in granted_accesses:
        seller_name = get_company_name(access['seller_id'])
        buyer_name = get_company_name(access['buyer_id'])
        access_list.append({
            'seller_id': access['seller_id'],
            'buyer_id': access['buyer_id'],
            'seller_name': seller_name,
            'buyer_name': buyer_name
        })
    return render_template_string(template, sellers=sellers, buyers=buyers, access_list=access_list)

@app.route('/grant', methods=['POST'])
def grant_access():
    seller_id = request.form['seller_id']
    buyer_id = request.form['buyer_id']

    if not any(a['seller_id'] == seller_id and a['buyer_id'] == buyer_id for a in granted_accesses):
        granted_accesses.append({'seller_id': seller_id, 'buyer_id': buyer_id})

    # Collect all sellers granted to this buyer
    seller_ids = [a['seller_id'] for a in granted_accesses if a['buyer_id'] == buyer_id]
    copy_sellers_preds_to_buyer(buyer_id, seller_ids)

    return redirect('/')

@app.route('/revoke', methods=['POST'])
def revoke_access():
    seller_id = request.form['seller_id']
    buyer_id = request.form['buyer_id']

    global granted_accesses
    granted_accesses = [
        a for a in granted_accesses
        if not (a['seller_id'] == seller_id and a['buyer_id'] == buyer_id)
    ]

    # Collect remaining sellers for this buyer
    seller_ids = [a['seller_id'] for a in granted_accesses if a['buyer_id'] == buyer_id]
    copy_sellers_preds_to_buyer(buyer_id, seller_ids)

    return redirect('/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)






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
