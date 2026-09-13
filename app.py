import os
import requests
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_only')

# Environment Variables
JSONBIN_ID = os.environ.get('JSONBIN_ID')
JSONBIN_KEY = os.environ.get('JSONBIN_KEY')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'password')

URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    'Content-Type': 'application/json',
    'X-Master-Key': JSONBIN_KEY
}

def get_data():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('record', {'tasks': []})
    return {'tasks': []}

def save_data(data):
    requests.put(URL, json=data, headers=HEADERS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash('Username atau password salah!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data = get_data()
    tasks = data.get('tasks', [])
    
    # Filter Tanggal
    filter_date = request.args.get('date', '')
    if filter_date:
        tasks = [t for t in tasks if t['date'] == filter_date]
        
    return render_template('index.html', tasks=tasks, filter_date=filter_date)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    task_text = request.form['task']
    task_date = request.form['date'] or datetime.now().strftime('%Y-%m-%d')
    
    data = get_data()
    data['tasks'].append({
        'id': str(uuid.uuid4()),
        'task': task_text,
        'date': task_date,
        'completed': False
    })
    save_data(data)
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete(task_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    data = get_data()
    data['tasks'] = [t for t in data.get('tasks', []) if t['id'] != task_id]
    save_data(data)
    return redirect(url_for('index'))

@app.route('/toggle/<task_id>')
def toggle(task_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    data = get_data()
    for t in data.get('tasks', []):
        if t['id'] == task_id:
            t['completed'] = not t['completed']
            break
    save_data(data)
    return redirect(url_for('index'))

# Entry point untuk Vercel
if __name__ == '__main__':
    app.run(debug=True)
