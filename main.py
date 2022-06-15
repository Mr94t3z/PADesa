import os
import secrets
from flask import Flask, flash, request, redirect, render_template, url_for, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_uploads import IMAGES, UploadSet, configure_uploads
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

# Add Database
# basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'padesa.db')

# basedir
basedir = os.path.abspath(os.path.dirname(__file__))

# Cerate a Flask Website
app = Flask(__name__)

# sqlalchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padesa.db'

# Secret Key
app.config['SECRET_KEY'] = 'mr.94t3z'

# upload barang image
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(
    basedir, 'static/backend/assets/images/barang')

configure_uploads(app, photos)


# Initialize The Database
db = SQLAlchemy(app)

# Migrate database
migrate = Migrate(app, db)

# login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "Kamu harus login dulu !"
login_manager.login_message_category = "warning"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Users.query.get(int(user_id))


# # Create Model Peminjamans
# peminjaman = db.Table('peminjamans',
#                       db.Column('id_peminjaman', db.Integer,
#                                 primary_key=True),
#                       db.Column('id_barang', db.Integer,
#                                 db.ForeignKey('barangs.id_barang')),
#                       db.Column('id_user', db.Integer,
#                                 db.ForeignKey('users.id')),
#                       db.Column(db.Integer, nullable=False),
#                       db.Column('tgl_pinjam', db.DateTime(timezone=True),
#                                 default=db.func.now()),
#                       db.Column('status', db.Boolean, default=False)
#                       )


# Create Model Users
class Users(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225), nullable=False)
    email = db.Column(db.String(225), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    barangs = relationship('Barangs', secondary='peminjamans')


# Create Model Barangs
class Barangs(db.Model):
    __tablename__ = 'barangs'

    id_barang = db.Column(db.Integer, primary_key=True)
    nama_barang = db.Column(db.String(225), nullable=False)
    jenis_barang = db.Column(db.String(225), nullable=False)
    stok_barang = db.Column(db.Integer, nullable=False)
    foto_barang = db.Column(db.String(), nullable=False)

    users = relationship('Users', secondary='peminjamans')


# Create Model Peminjamans
class Peminjamans(db.Model):
    __tablename__ = 'peminjamans'

    id_peminjaman = db.Column(db.Integer, primary_key=True)
    id_barang = db.Column(db.Integer, db.ForeignKey(
        'barangs.id_barang'),  nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey(
        'users.id'),  nullable=False)
    tgl_pinjam = db.Column(db.DateTime(timezone=True), default=db.func.now())
    qty = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Boolean, default=False)

    barang = db.relationship(Barangs, backref=backref(
        "peminjamans", cascade="all, delete-orphan"))
    user = db.relationship(Users, backref=backref(
        "peminjamans", cascade="all, delete-orphan"))


# # Create Model Pengembalians
# class Pengembalians(db.Model):
#     __tablename__ = 'pengembalians'

#     id_pengembalian = db.Column(db.Integer, primary_key=True)
#     # id_barang = db.Column(db.Integer, db.ForeignKey(
#     #     'barangs.id_barang'), nullable=False)
#     # id_user = db.Column(db.Integer, db.ForeignKey(
#     #     'users.id'), nullable=False)
#     id_peminjaman = db.Column(
#         db.Integer, db.ForeignKey('peminjamans.id_peminjaman'), nullable=False)
#     tgl_pengembalian = db.Column(db.DateTime(
#         timezone=True), default=db.func.now())

#     # __table_args__ = (db.UniqueConstraint(id_barang, id_user, id_peminjaman),)

#     # barangs = db.relationship(
#     #     "Barangs", back_populates="barangs_pengembalians")
#     # users = db.relationship("Users", back_populates="users_pengembalians")
#     Peminjamans = db.relationship(
#         "Peminjamans")


# 404 page not found
@app.errorhandler(404)
def error_404(e):
    return render_template('error-404.html'), 404


# 505 internal server error
@app.errorhandler(500)
def error_500(e):
    return render_template('error-500.html'), 500


# login page
@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = Users.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password,
        # hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Email atau password salah !', 'danger')
            # if the user doesn't exist or
            # password is wrong, reload the page
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('user_dashboard'))

    return render_template('login.html')


# register page
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # if this returns a user,
        # then the email already exists in database
        user = Users.query.filter_by(email=email).first()

        if user:  # if a user is found
            flash('Email sudah terdaftar !', 'danger')
            return redirect(url_for('register'))

        # create new user
        new_user = Users(name=name, email=email,
                         password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil !', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# dashboard page
@app.route('/dashboard', methods=["GET", "POST"])
@login_required
def user_dashboard():
    peminjamans = Peminjamans().query.all()
    barangs = Barangs().query.all()
    users = Users().query.all()

    if request.method == 'POST':
        id_barang = request.form.get('id_barang')
        id_user = request.form.get('id_user')
        qty = request.form.get('qty')

        new_peminjaman = Peminjamans(
            id_barang=id_barang, id_user=id_user, qty=qty)

        db.session.add(new_peminjaman)
        db.session.commit()
        return redirect(url_for('user_dashboard'))

    return render_template('user-dashboard.html', id_user=current_user.id, name=current_user.name, admin=current_user.is_admin, peminjamans=peminjamans, barangs=barangs, users=users)


# # peminjaman
# @app.route('/addcart/<int:id_barang>', methods=["GET", "POST"])
# @login_required
# def add_peminjaman(id_barang):
#     peminjaman = Peminjamans().query.get_or_404(id_barang)

#     if request.method == 'POST':
#         peminjaman.id_barang = request.form.get('id_barang')
#         peminjaman.id_user = request.form.get('id_user')
#         peminjaman.qty = request.form.get('qty')

#         db.session.add(peminjaman)
#         db.session.commit()
#         return redirect(url_for('show_peminjaman'))

#     return render_template('user-dashboard.html', id_user=current_user.id, name=current_user.name, admin=current_user.is_admin)


# # orders
# @app.route('/orders/<int:id>', methods=["GET", "POST"])
# @login_required
# def orders(id):
#     if current_user:
#         stok_barang = request.form.get('stok_barang')
#         id_user = current_user.id
#         users = Users.query.filter_by(id=id_user)
#         barangs = Barangs.query.filter_by(id_user=id_user)

#     return render_template('user-dashboard.html', name=current_user.name, admin=current_user.is_admin)


# show users page
@app.route('/user-management', methods=["GET", "POST"])
@login_required
def show_user():
    items = Users().query.all()
    return render_template('user-management.html', items=items, name=current_user.name, admin=current_user.is_admin)


# user edit page
@app.route('/edit-user/<int:id>', methods=["GET", "POST"])
@login_required
def edit_user(id):
    update = Users.query.get_or_404(id)

    if request.method == 'POST':
        update.name = request.form.get('name')
        update.email = request.form.get('email')
        password = request.form.get('password')
        update.password = generate_password_hash(password, method='sha256')
        update.is_admin = request.form.get('is_admin')

        # if True, then user is Administrator
        if update.is_admin == 'True':
            update.is_admin = True
        # if False, then user is Penduduk Desa
        elif update.is_admin == 'False':
            update.is_admin = False

        db.session.add(update)
        db.session.commit()
        return redirect(url_for('show_user'))

    return render_template('edit-user.html', name=current_user.name, admin=current_user.is_admin, update=update)


# delete user
@ app.route('/delete-user/<int:id>', methods=["GET", "POST"])
@ login_required
def delete_user(id):
    item = Users.query.get_or_404(id)

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('show_user'))


# show barangs page
@ app.route('/barang-management', methods=["GET", "POST"])
@ login_required
def show_barang():
    barangs = Barangs().query.all()
    return render_template('barang-management.html', barangs=barangs, name=current_user.name, admin=current_user.is_admin)


# add barang page
@ app.route('/add-barang', methods=["GET", "POST"])
@ login_required
def add_barang():
    if request.method == 'POST':
        nama_barang = request.form.get('nama_barang')
        jenis_barang = request.form.get('jenis_barang')
        stok_barang = request.form.get('stok_barang')
        foto_barang = photos.save(request.files.get(
            'foto_barang'), name=secrets.token_hex(10) + '.')

        # if this returns a barang,
        # then the nama barang already exists in database
        barang = Barangs.query.filter_by(nama_barang=nama_barang).first()

        if barang:  # if a barang is found
            flash('Barang sudah tersedia !', 'danger')
            return redirect(url_for('add_barang'))

        if not foto_barang:
            flash('Foto tidak di isi !', 'danger')
            return redirect(url_for('add_barang'))

        # create new barang
        new_barang = Barangs(nama_barang=nama_barang, jenis_barang=jenis_barang,
                             stok_barang=stok_barang, foto_barang=foto_barang)

        # add the new barang to the database
        db.session.add(new_barang)
        db.session.commit()
        #flash('Barang berhasil ditambahkan !', 'success')
        return redirect(url_for('show_barang'))

    return render_template('add-barang.html', name=current_user.name, admin=current_user.is_admin)


# barang edit page
@ app.route('/edit-barang/<int:id_barang>', methods=["GET", "POST"])
@ login_required
def edit_barang(id_barang):
    update = Barangs.query.get_or_404(id_barang)

    if request.method == 'POST':
        update.nama_barang = request.form.get('nama_barang')
        update.jenis_barang = request.form.get('jenis_barang')
        update.stok_barang = request.form.get('stok_barang')
        if request.files.get('foto_barang'):
            try:
                os.unlink(os.path.join(current_app.root_path,
                          'static/backend/assets/images/barang/' + update.foto_barang))
                update.foto_barang = photos.save(request.files.get(
                    'foto_barang'), name=secrets.token_hex(10) + '.')
            except:
                update.foto_barang = photos.save(request.files.get(
                    'foto_barang'), name=secrets.token_hex(10) + '.')

        if not update.foto_barang:
            flash('Foto tidak di isi !', 'danger')
            return redirect(url_for('edit_barang'))

        db.session.commit()
        return redirect(url_for('show_barang'))

    return render_template('edit-barang.html', name=current_user.name, admin=current_user.is_admin, update=update)


# delete barang
@ app.route('/delete-barang/<int:id_barang>', methods=["GET", "POST"])
@ login_required
def delete_barang(id_barang):
    delete = Barangs.query.get_or_404(id_barang)

    try:
        os.unlink(os.path.join(current_app.root_path,
                               'static/backend/assets/images/barang/' + delete.foto_barang))
        db.session.delete(delete)
    except:
        db.session.delete(delete)

    db.session.commit()

    return redirect(url_for('show_barang'))


# show peminjaman page
@ app.route('/peminjaman-management', methods=["GET", "POST"])
@ login_required
def show_peminjaman():
    peminjamans = Peminjamans().query.all()
    barangs = Barangs().query.all()
    users = Users().query.all()

    return render_template('peminjaman-management.html', peminjamans=peminjamans, name=current_user.name, admin=current_user.is_admin, barangs=barangs, users=users)


# show pengembalian page
@ app.route('/pengembalian-management', methods=["GET", "POST"])
@ login_required
def show_pengembalian():
    barangs = Barangs().query.all()
    return render_template('pengembalian-management.html', barangs=barangs, name=current_user.name, admin=current_user.is_admin)


# user page
@ app.route('/user', methods=["GET", "POST"])
@ login_required
def user():
    return render_template('user.html', name=current_user.name)


# logout
@ app.route('/logout')
@ login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# check data
# @ app.route('/check/<int:id>', methods=["GET", "POST"])
# def check():
#     items = Barangs.query.filter_by(id_barang=id).first()
#     return Response('check.html', items=items)


# main app
if __name__ == '__main__':
    app.run(debug=True)
