from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from incontext.details import get_creator_details

bp = Blueprint('items', __name__, url_prefix='/items')

@bp.route('/')
@login_required
def index():
    db = get_db()
    items = db.execute(
        'SELECT i.id, i.name, i.created, u.username'
        ' FROM items i'
        ' JOIN users u ON i.creator_id = u.id'
        ' WHERE i.creator_id = ?'
        ' ORDER BY i.created',
        (g.user['id'],)
    ).fetchall()
    details = db.execute(
        'SELECT d.name, d.id'
        ' FROM details d'
        ' WHERE creator_id = ?',
        (g.user['id'],)
    ).fetchall()
    relations = db.execute(
        'SELECT r.item_id, r.detail_id, r.content'
        ' FROM item_detail_relations r'
        ' WHERE item_id IN (SELECT id FROM items WHERE creator_id = ?)',
        (g.user['id'],)
    ).fetchall()
    return render_template('items/index.html', items=items, details=details, relations=relations)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        detail_fields = []
        details = get_creator_details()
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
            relations = []
            for field in detail_fields:
                relations.append((item_id,) + field)
            cur.executemany(
                'INSERT INTO item_detail_relations (item_id, detail_id, content) VALUES(?, ?, ?)',
                relations
            )
            db.commit()
            return redirect(url_for('items.index'))

    details = get_creator_details()
    return render_template('items/create.html', details=details)

@bp.route('/<int:id>/view', methods=('GET',))
@login_required
def view(id):
    item = get_item(id)
    details = get_creator_details()
    relations = get_item_relations(id)
    details_with_contents = []
    for detail in details:
        detail_id = detail['id']
        detail_name = detail['name']
        detail_content = ''
        for relation in relations:
            if relation['detail_id'] == detail_id:
                detail_content = relation['content']
        details_with_contents.append(dict(id=detail_id, name=detail_name, content=detail_content))
    return render_template('items/view.html', item=item, details=details_with_contents)

def get_item(id, check_creator=True):
    item = get_db().execute(
        'SELECT i.id, name, created, creator_id, username'
        ' FROM items i'
        ' JOIN users u ON i.creator_id = u.id'
        ' WHERE i.id = ?',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, f"Item with id {id} doesn't exist.")

    if check_creator and item['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.
    
    return item

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    item = get_item(id)

    if request.method == 'POST':
        name = request.form['name']
        detail_fields = []
        details = get_creator_details()
        for detail in details:
            detail_id = detail['id']
            detail_content = request.form[str(detail_id)]
            detail_fields.append((detail_content, id, detail_id))
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'UPDATE items SET name = ?'
                ' WHERE id = ?',
                (name, id)
            )
            item_id = cur.lastrowid
            relations = []
            cur.executemany(
                'UPDATE item_detail_relations SET content = ? WHERE item_id = ? AND detail_id = ?',
                detail_fields
            )
            db.commit()
            return redirect(url_for('items.index'))
    
    details = get_creator_details()
    relations = get_item_relations(id)
    details_with_contents = []
    for detail in details:
        detail_id = detail['id']
        detail_name = detail['name']
        detail_content = ''
        for relation in relations:
            if relation['detail_id'] == detail_id:
                detail_content = relation['content']
        details_with_contents.append(dict(id=detail_id, name=detail_name, content=detail_content))
    return render_template('items/edit.html', item=item, details=details_with_contents)

def get_item_relations(item_id):
    relations = get_db().execute(
        'SELECT detail_id, content'
        ' FROM item_detail_relations'
        ' WHERE item_id = ?',
        (item_id,)
    ).fetchall()
    return relations

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_item(id)
    db = get_db()
    db.execute('DELETE FROM items WHERE id = ?', (id,))
    db.execute('DELETE FROM item_detail_relations WHERE item_id = ?', (id,))
    db.commit()
    return redirect(url_for('items.index'))
