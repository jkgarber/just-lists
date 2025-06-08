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
    db = get_db()
    lists = db.execute(
        'SELECT l.id, l.name, l.description, l.created'
        ' FROM lists l'
        ' WHERE l.creator_id = ?',
        (g.user['id'],)
    ).fetchall()
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
