from aiohttp import web
import aiohttp_cors
import sqlite3
import os

TODOS = {
    0: {'title': 'build an API', 'order': 1, 'completed': False},
    1: {'title': '?????', 'order': 2, 'completed': False},
    2: {'title': 'profit!', 'order': 3, 'completed': False}
}

TAGS = {
    0: {'name': 'cooking'},
    1: {'name': 'sport'}
}

# global variable
conn = sqlite3.connect('./todo_backend.sqlite')


def nb_tags(c):
    try:
        c.execute('select count(*) from tags;')
        return c.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def nb_todos(c):
    try:
        c.execute('select count(*) from todos;')
        return c.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def mk_one_todo_url(request, id):
    return str(request.url.join(request.app.router['one_todo'].url_for(id=str(id))))


def mk_one_tag_url(request, id):
    return str(request.url.join(request.app.router['one_tag'].url_for(id=str(id))))


# return the tags of a specified todo id
def get_tags_from_id(todo_id):
    c = conn.cursor()
    c.execute(f'''select id,title from tags, assoc 
                  where assoc.todo_id = {todo_id} and assoc.tag_id = tags.id''')
    data = c.fetchall()
    return data


# return the todos of a specific tag id
def get_todos_from_id(tag_id):
    c = conn.cursor()
    c.execute(f'''select id,title,completed,t_order from todos, assoc
                  where assoc.tag_id = {tag_id} and assoc.todo_id = todos.id''')
    data = c.fetchall()
    return data


def get_all_todos(request):
    c = conn.cursor()
    c.execute(f'''select id,title,completed,t_order from todos''')
    todos = c.fetchall()

    return web.json_response([
        {
            'id': data[0],
            "title": data[1],
            "completed": bool(data[2]),
            "order": data[3],
            "url": mk_one_todo_url(request, data[0]),
            "tags": [
                {
                    "id": tag[0],
                    "title": tag[1],
                    "url": mk_one_tag_url(request, tag[0])
                }
                for tag in get_tags_from_id(data[0])
            ]
        }
        for data in todos
    ])


def remove_all_todos(request):
    c = conn.cursor()
    c.execute('''delete from todos''')
    c.execute('''delete from assoc''')
    return web.Response(status=204)


def get_one_todo(request):
    todo_id = int(request.match_info['id'])

    c = conn.cursor()
    c.execute(f'''select id,title,completed,t_order from todos as t where t.id = {todo_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    url = mk_one_todo_url(request, data[0])

    tags = get_tags_from_id(todo_id)

    r_todo = {
        'id': data[0],
        "title": data[1],
        "completed": bool(data[2]),
        "order": data[3],
        "url": url,
        "tags": [
            {
                "id": tag[0],
                "title": tag[1],
                "url": url
            }
            for tag in tags
        ]
    }

    return web.json_response({'id': id, **r_todo})


async def create_todo(request):
    data = await request.json()

    # cursor
    c = conn.cursor()

    # check data
    if 'title' not in data:
        return web.json_response({'error': '"title" is a required field'})
    title = data['title']
    if not isinstance(title, str) or not len(title):
        return web.json_response({'error': '"title" must be a string with at least one character'})

    if bool(data.get('completed', False)):
        completed = 1
    else:
        completed = 0

    if 'order' not in data:
        order = nb_tags(c) + 1
    else:
        order = data['order']

    # insert data
    c.execute(f'''insert into todos (title, completed, t_order) values ('{title}',{completed},{order})''')
    new_id = c.lastrowid
    conn.commit()

    tags = get_tags_from_id(new_id)

    url = mk_one_todo_url(request, new_id)

    r_todo = {
        'id': new_id,
        "title": title,
        "completed": bool(completed),
        "order": order,
        "url": url,
        "tags": [
            {
                "id": tag[0],
                "title": tag[1],
                "url": url
            }
            for tag in tags
        ]
    }

    return web.json_response({'id': id, **r_todo})


async def update_todo(request):
    todo_id = int(request.match_info['id'])

    c = conn.cursor()
    c.execute(f'''select id,title,completed,t_order from todos as t where t.id = {todo_id}''')
    todo = c.fetchone()

    if todo is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    data = await request.json()

    if 'title' not in data:
        title = todo[1]
    else:
        title = data['title']

    if 'completed' not in data:
        completed = bool(todo[2])
    else:
        completed = data['completed']

    if 'order' not in data:
        order = todo[3]
    else:
        order = data['order']

    c.execute(f'''update todos set title = '{title}',completed = {completed},t_order = {order}
                  where id = {todo_id}''')
    conn.commit()

    c.execute(f'''select id,title,completed,t_order from todos as t where t.id = {todo_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    url = mk_one_todo_url(request, data[0])

    tags = get_tags_from_id(todo_id)

    r_todo = {
        'id': data[0],
        "title": data[1],
        "completed": bool(data[2]),
        "order": data[3],
        "url": url,
        "tags": [
            {
                "id": tag[0],
                "title": tag[1],
                "url": url
            }
            for tag in tags
        ]
    }

    return web.json_response({'id': id, **r_todo})


def remove_todo(request):
    id = int(request.match_info['id'])

    c = conn.cursor()
    c.execute(f'''select * from todos as t where t.id = {id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    c.execute(f'''delete from todos where id = {id}''')
    conn.commit()

    return web.Response(status=204)


def delete_all_tags_from_todo(request):
    tag_id = int(request.match_info['id'])
    c = conn.cursor()
    c.execute(f'''delete from assoc where assoc.tag_id = {tag_id}''')
    conn.commit()
    return web.Response(status=204)


def remove_tags(request):
    c = conn.cursor()
    c.execute('''delete from tags''')
    c.execute('''delete from assoc''')
    return web.Response(status=204)


def get_all_tags(request):
    c = conn.cursor()
    c.execute(f'''select id,title from tags''')
    tags = c.fetchall()

    return web.json_response([
        {
            'id': tag[0],
            "title": tag[1],
            "url": mk_one_tag_url(request, tag[0]),
            "todos": [
                {
                    "id": todo[0],
                    "title": todo[1],
                    "completed": bool(todo[2]),
                    "order": todo[3],
                    "url": mk_one_todo_url(request, todo[0]),

                }
                for todo in get_todos_from_id(tag[0])
            ]
        }
        for tag in tags
    ])


async def create_tag(request):
    data = await request.json()
    c = conn.cursor()

    # check data
    if 'title' not in data:
        return web.json_response({'error': '"title" is a required field'})
    title = data['title']

    if not isinstance(title, str) or not len(title):
        return web.json_response({'error': '"title" must be a string with at least one character'})

    # insert data
    c.execute(f'''insert into tags (title) values ('{title}')''')
    new_id = c.lastrowid
    conn.commit()

    url = mk_one_tag_url(request, new_id)

    r_tag = {
        'id': new_id,
        "title": title,
        "url": url,
        "todos": [
            {
                "id": todo[0],
                "title": todo[1],
                "completed": bool(todo[2]),
                "order": todo[3],
                "url": mk_one_todo_url(request, todo[0]),
            }
            for todo in get_todos_from_id(new_id)
        ]
    }

    return web.json_response({'id': id, **r_tag})


def remove_one_tag(request):
    tag_id = int(request.match_info['id'])
    c = conn.cursor()
    c.execute(f'''select * from tags as t where t.id = {tag_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    c.execute(f'''delete from tags where id = {tag_id}''')
    conn.commit()

    return web.Response(status=204)


async def update_one_tag(request):
    tag_id = int(request.match_info['id'])

    c = conn.cursor()
    c.execute(f'''select id,title from tags as t where t.id = {tag_id}''')
    todo = c.fetchone()

    if todo is None:
        return web.json_response({'error': 'Tag not found'}, status=404)

    data = await request.json()

    if 'title' not in data:
        title = todo[1]
    else:
        title = data['title']

    c.execute(f'''update tags set title = '{title}' where id = {tag_id}''')
    conn.commit()

    c.execute(f'''select id,title from tags as t where t.id = {tag_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    url = mk_one_tag_url(request, tag_id)

    r_tag = {
        'id': data[0],
        "title": data[1],
        "url": url,
        "todos": [
            {
                "id": todo[0],
                "title": todo[1],
                "completed": bool(todo[2]),
                "order": todo[3],
                "url": mk_one_todo_url(request, todo[0]),
            }
            for todo in get_todos_from_id(data[0])
        ]
    }

    return web.json_response({'id': tag_id, **r_tag})


def delete_one_tag_from_todo(request):
    todo_id = int(request.match_info['id'])
    tag_id = int(request.match_info['tag_id'])

    c = conn.cursor()
    c.execute(f'''delete from assoc where todo_id = {todo_id} and tag_id = {tag_id}''')
    conn.commit()

    return web.Response(status=204)


def get_one_tag(request):
    tag_id = int(request.match_info['id'])

    c = conn.cursor()
    c.execute(f'''select id,title from tags as t where t.id = {tag_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Tag not found'}, status=404)

    url = mk_one_tag_url(request, data[0])

    todos = get_todos_from_id(tag_id)

    r_tag = {
        'id': data[0],
        "title": data[1],
        "url": url,
        "todos": [
            {
                "id": todo[0],
                "title": todo[1],
                "completed": bool(todo[2]),
                "order": todo[3],
                "url": mk_one_todo_url(request, todo[0])
            }
            for todo in todos
        ]
    }

    return web.json_response({'id': tag_id, **r_tag})


def get_todos_from_tag(request):
    print("OK")
    tag_id = int(request.match_info['id'])
    c = conn.cursor()
    c.execute(f'''select * from tags as t where t.id = {tag_id}''')
    data = c.fetchone()

    if data is None:
        print("KO")
        return web.json_response({'error': 'Tag not found'}, status=404)

    todos = get_todos_from_id(tag_id)

    return web.json_response([
        {
            "id": todo[0],
            "title": todo[1],
            "completed": bool(todo[2]),
            "order": todo[3],
            "url": str(request.url.join(request.app.router['tag_2_todos'].url_for(id=str(id)))),
        }
        for todo in todos
    ])


def get_tags_one_todo(request):
    todo_id = int(request.match_info['id'])
    c = conn.cursor()
    c.execute(f'''select * from todos as t where t.id = {todo_id}''')
    data = c.fetchone()

    if data is None:
        return web.json_response({'error': 'Todo not found'}, status=404)

    tags = get_tags_from_id(todo_id)

    return web.json_response([
        {
            'id': tag[0],
            "title": tag[1],
            "url": mk_one_tag_url(request, tag[0]),
        }
        for tag in tags
    ])


async def associate_tag_to_todo(request):
    todo_id = int(request.match_info['id'])
    data = await request.json()

    if 'id' not in data:
        return web.json_response({'error': '"id" is a required field'})
    tag_id = data['id']

    c = conn.cursor()
    c.execute(f'''insert into assoc (tag_id, todo_id) VALUES ({tag_id},{todo_id})''')
    conn.commit()

    return web.json_response({
        'id': tag_id
    }, status=201)


def app_factory(args=()):
    app = web.Application()

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    todos_resource = cors.add(app.router.add_resource("/todos/", name='todos'))
    cors.add(todos_resource.add_route("GET", get_all_todos))
    cors.add(todos_resource.add_route("DELETE", remove_all_todos))
    cors.add(todos_resource.add_route("POST", create_todo))

    todo_resource = cors.add(app.router.add_resource("/todos/{id:\d+}", name='one_todo'))
    cors.add(todo_resource.add_route("GET", get_one_todo))
    cors.add(todo_resource.add_route("PATCH", update_todo))
    cors.add(todo_resource.add_route("DELETE", remove_todo))

    todo_resource = cors.add(app.router.add_resource("/todos/{id:\d+}/tags/{tag_id:\d+}", name='one_todo_one_tag'))
    cors.add(todo_resource.add_route("DELETE", delete_one_tag_from_todo))

    todo_resource = cors.add(app.router.add_resource("/tags/", name='tags'))
    cors.add(todo_resource.add_route("POST", create_tag))
    cors.add(todo_resource.add_route("DELETE", remove_tags))
    cors.add(todo_resource.add_route("GET", get_all_tags))

    todo_resource = cors.add(app.router.add_resource("/tags/{id:\d+}", name='one_tag'))
    cors.add(todo_resource.add_route("DELETE", remove_one_tag))
    cors.add(todo_resource.add_route("GET", get_one_tag))
    cors.add(todo_resource.add_route("PATCH", update_one_tag))

    todo_resource = cors.add(app.router.add_resource("/todos/{id:\d+}/tags/", name='one_todo_tags'))
    cors.add(todo_resource.add_route("DELETE", delete_all_tags_from_todo))
    cors.add(todo_resource.add_route("GET", get_tags_one_todo))
    cors.add(todo_resource.add_route("POST", associate_tag_to_todo))

    todo_resource = cors.add(app.router.add_resource("/tags/{id:\d+}/todos/", name='tag_2_todos'))
    cors.add(todo_resource.add_route("GET", get_todos_from_tag))

    return app
