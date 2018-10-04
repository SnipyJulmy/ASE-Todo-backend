import sqlite3

# global variable
conn = sqlite3.connect('todo_backend.sqlite')
c = conn.cursor()
c.execute(f'''select id,title,completed,t_order from todos''')
data = c.fetchall()

print(data)
