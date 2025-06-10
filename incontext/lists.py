from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('lists', __name__, url_prefix='/lists')

@bp.route('/')
@login_required
def index():
    lists = get_user_lists()
    return render_template('lists/index.html', lists=lists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO lists (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            db.commit()
            return redirect(url_for('lists.index'))

    return render_template('lists/create.html')


@bp.route('/<int:id>/view')
@login_required
def view(id):
    list = get_list(id)
    items = get_list_items_with_details(id, True)
    details = get_list_details(id)
    return render_template('lists/view.html', list=list, items=items, details=details)


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    list = get_list(id)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE lists SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('lists.index'))
    return render_template('lists/edit.html', list=list)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_list(id)
    db = get_db()
    # Delete list-related details
    db.execute(
        'DELETE FROM details'
        ' WHERE id IN'
        ' (SELECT detail_id FROM list_detail_relations WHERE list_id = ?)',
        (id,)
    )
    # Delete list-related items
    db.execute(
        'DELETE FROM items'
        ' WHERE id IN'
        ' (SELECT item_id FROM list_item_relations WHERE list_id = ?)',
        (id,)
    )
    # Delete item-detail relations
    db.execute(
        'DELETE FROM item_detail_relations'
        ' WHERE item_id IN'
        ' (SELECT item_id FROM list_item_relations WHERE list_id = ?)',
        (id,)
    )
    # Delete list-item relations
    db.execute('DELETE FROM list_item_relations WHERE list_id = ?',(id,))
    # Delete list-detail relations
    db.execute('DELETE FROM list_detail_relations WHERE list_id = ?', (id,))
    # Delete list
    db.execute('DELETE FROM lists WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('lists.index'))


@bp.route('/<int:id>/items/new', methods=('GET', 'POST'))
@login_required
def new_item(id):
    if request.method == 'POST':
        name = request.form['name']
        detail_fields = []
        details = get_list_details(id)
        for detail in details:
            detail_id = detail['id']
            detail_content = request.form[str(detail_id)]
            detail_fields.append((detail_id, detail_content))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO items (name, creator_id)'
                ' VALUES (?, ?)',
                (name, g.user['id'])
            )
            item_id = cur.lastrowid
            cur.execute(
                'INSERT INTO list_item_relations (list_id, item_id)'
                ' VALUES (?, ?)',
                (id, item_id)
            )
            relations = []
            for field in detail_fields:
                relations.append((item_id,) + field)
            cur.executemany(
                'INSERT INTO item_detail_relations (item_id, detail_id, content)'
                ' VALUES(?, ?, ?)',
                relations
            )
            db.commit()
            return redirect(url_for('lists.view', id=id))
    list = get_list(id)
    details = get_list_details(id)
    return render_template('lists/items/new.html', list=list, details=details)


@bp.route('/<int:id>/items/<int:item_id>/view')
@login_required
def view_item(id, item_id):
    list = get_list(id)
    item, details = get_list_item(id, item_id)
    return render_template('lists/items/view.html', list=list, item=item, details=details)


@bp.route('/<int:id>/items/<int:item_id>/edit', methods=('GET','POST'))
@login_required
def edit_item(id, item_id):
    list = get_list(id)
    item, details = get_list_item(id, item_id)
    if request.method == 'POST':
        name = request.form['name']
        detail_fields = []
        details = get_list_details(id)
        for detail in details:
            detail_id = detail['id']
            detail_content = request.form[str(detail_id)]
            detail_fields.append((detail_content, item_id, detail_id))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE items SET name = ?'
                ' WHERE id = ?',
                (name, item_id)
            )
            db.executemany(
                'UPDATE item_detail_relations'
                ' SET content = ?'
                ' WHERE item_id = ?'
                ' AND detail_id = ?',
                detail_fields
            )
            db.commit()
            return redirect(url_for('lists.view', id=id))
    return render_template('lists/items/edit.html', list=list, item=item, details=details)


@bp.route('<int:id>/items/<int:item_id>/delete', methods=('POST',))
@login_required
def delete_item(id, item_id):
    list = get_list(id)
    item, details = get_list_item(id, item_id)
    db = get_db()
    db.execute('DELETE FROM items WHERE id = ?', (item_id,))
    db.execute('DELETE FROM item_detail_relations WHERE item_id = ?', (item_id,))
    db.execute(
        'DELETE from list_item_relations'
        ' WHERE list_id = ? AND item_id = ?',
        (id, item_id)
    )
    db.commit()
    return redirect(url_for('lists.view', id=id))


@bp.route('/<int:id>/details/new', methods=('GET', 'POST'))
@login_required
def new_detail(id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO details (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            detail_id = cur.lastrowid
            cur.execute(
                'INSERT INTO list_detail_relations (list_id, detail_id)'
                ' VALUES (?, ?)',
                (id, detail_id)
            )
            list_items = get_list_items(id)
            data = [(item['id'], detail_id, '') for item in list_items]
            cur.executemany(
                'INSERT INTO item_detail_relations (item_id, detail_id, content)'
                'VALUES (?, ?, ?)',
                data
            )
            db.commit()
            return redirect(url_for('lists.view', id=id))
    list = get_list(id)
    return render_template('lists/details/new.html', list=list)


@bp.route('/<int:id>/details/<int:detail_id>/edit', methods=('GET','POST'))
@login_required
def edit_detail(id, detail_id):
    list = get_list(id)
    detail = get_list_detail(id, detail_id)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE details SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, detail_id)
            )
            db.commit()
            return redirect(url_for('lists.view', id=id))
    return render_template('lists/details/edit.html', list=list, detail=detail)


@bp.route('/<int:id>/details/<int:detail_id>/delete', methods=('POST',))
@login_required
def delete_detail(id, detail_id):
    list = get_list(id)
    detail = get_list_detail(id, detail_id)
    db = get_db()
    db.execute('DELETE FROM details WHERE id = ?', (detail_id,))
    db.execute('DELETE FROM item_detail_relations WHERE detail_id = ?', (detail_id,))
    db.execute('DELETE FROM list_detail_relations WHERE detail_id = ?', (detail_id,))
    db.commit()
    return redirect(url_for('lists.view', id=id))


def get_user_lists():
    db = get_db()
    user_lists = db.execute(
        'SELECT l.id, l.name, l.description, l.created'
        ' FROM lists l'
        ' WHERE l.creator_id = ?',
        (g.user['id'],)
    ).fetchall()
    return user_lists


def get_list(id, check_creator=True):
    if check_creator:
        list_creator_id = get_list_creator_id(id)
        if list_creator_id != g.user['id']:
            abort(403)
    list = get_db().execute(
        'SELECT l.id, l.name, l.description, l.creator_id'
        ' FROM lists l'
        ' WHERE l.id = ?',
        (id,)
    ).fetchone()
    if list is None:
        abort(404, f'List with id {id} does not exist.')
    return list
    

def get_list_items_with_details(id, check_creator=True):
    if check_creator:
        list_creator_id = get_list_creator_id(id)
        if list_creator_id != g.user['id']:
            abort(403)
    db = get_db()
    items = db.execute(
        'SELECT i.id, i.name, i.created'
        ' FROM items i'
        ' JOIN list_item_relations r ON r.item_id = i.id'
        ' WHERE r.list_id = ?',
        (id,)
    ).fetchall()
    details = db.execute(
        'SELECT d.id, d.name, d.description'
        ' FROM details d'
        ' JOIN list_detail_relations r ON r.detail_id = d.id'
        ' WHERE r.list_id = ?',
        (id,)
    ).fetchall()
    item_ids = [item['id'] for item in items]
    placeholders = f'{"?, " * len(item_ids)}'[:-2]
    relations = db.execute(
        'SELECT r.item_id, r.detail_id, r.content'
        ' FROM item_detail_relations r'
        f' WHERE r.item_id IN ({placeholders})',
        item_ids
    ).fetchall()
    list_items = []
    for item in items:
        this_item = {}
        this_item['id'] = item['id']
        this_item['name'] = item['name']
        this_item['created'] = item['created']
        this_item['details'] = []
        for detail in details:
            this_detail = {}
            this_detail['name'] = detail['name']
            for relation in relations:
                if relation['item_id'] == item['id'] and relation['detail_id'] == detail['id']:
                    this_detail['content'] = relation['content']
            this_item['details'].append(this_detail)
        list_items.append(this_item)
    return list_items


def get_list_items(id, check_creator=True):
    if check_creator:
        list_creator_id = get_list_creator_id(id)
        if list_creator_id != g.user['id']:
            abort(403)
    db = get_db()
    items = db.execute(
        'SELECT i.id, i.name, i.created'
        ' FROM items i'
        ' JOIN list_item_relations r ON r.item_id = i.id'
        ' WHERE r.list_id = ?',
        (id,)
    ).fetchall()
    return items



def get_list_item(id, item_id, check_relation=True):
    if check_relation:
        item_list_id = get_item_list_id(item_id)
        if item_list_id != id:
            abort(400)
    db = get_db()
    item = db.execute(
        'SELECT i.id, i.name, i.created, u.username'
        ' FROM items i'
        ' JOIN users u ON i.creator_id = u.id'
        ' WHERE i.id = ?',
        (item_id,)
    ).fetchone()
    details = db.execute(
        'SELECT d.id, r.content, d.name'
        ' FROM item_detail_relations r'
        ' JOIN details d ON r.detail_id = d.id'
        ' WHERE r.item_id = ?',
        (item_id,)
    ).fetchall()
    return item, details


def get_list_creator_id(list_id):
    creator_id = get_db().execute(
        'SELECT l.creator_id'
        ' FROM lists l'
        ' WHERE l.id = ?',
        (list_id,)
    ).fetchone()['creator_id']
    return creator_id


def get_item_list_id(item_id):
    list_id = get_db().execute(
        'SELECT r.list_id FROM list_item_relations r'
        ' WHERE r.item_id = ?',
        (item_id,)
    ).fetchone()['list_id']
    return list_id


def get_list_details(id, check_creator=True):
    if check_creator:
        list_creator_id = get_list_creator_id(id)
        if list_creator_id != g.user['id']:
            abort(403)
    db = get_db()
    list_details = db.execute(
        'SELECT d.id, d.name, d.description'
        ' FROM details d'
        ' JOIN list_detail_relations r ON r.detail_id = d.id'
        ' WHERE r.list_id = ?',
        (id,)
    ).fetchall()
    return list_details


def get_list_detail(id, detail_id, check_relation=True):
    if check_relation:
        detail_list_id = get_detail_list_id(detail_id)
        if detail_list_id != id:
            abort(400)
    db = get_db()
    list_detail = db.execute(
        'SELECT d.id, d.name, d.description'
        ' FROM details d'
        ' WHERE d.id = ?',
        (detail_id,)
    ).fetchone()
    return list_detail


def get_detail_list_id(detail_id):
    print(f'detail id: {detail_id}')
    list_id = get_db().execute(
        'SELECT r.list_id'
        ' FROM list_detail_relations r'
        ' WHERE r.detail_id = ?',
        (detail_id,)
    ).fetchone()['list_id']
    return list_id
