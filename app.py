from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "foodsecret"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image = db.Column(db.String(100))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))
    total = db.Column(db.Integer)

# ---------------- USER ROUTES ----------------

@app.route('/')
def index():
    foods = Food.query.all()
    return render_template('index.html', foods=foods)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return render_template('register.html', error="User already exists")
        db.session.add(User(
            username=request.form['username'],
            password=request.form['password']
        ))
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()
        if user:
            session['user'] = user.username
            session['cart'] = []
            return redirect('/')
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- CART ----------------

@app.route('/add/<int:id>')
def add_to_cart(id):
    if 'user' not in session:
        return redirect('/login')

    session.setdefault('cart', []).append(id)
    session.modified = True

    # Get product name for the message
    food = Food.query.get(id)
    flash(f"✅ {food.name} added to cart successfully!")
    return redirect('/')

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect('/login')

    items, total = [], 0
    for i in session.get('cart', []):
        food = Food.query.get(i)
        if food:
            items.append(food)
            total += food.price

    return render_template('cart.html', items=items, total=total)

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        return redirect('/login')

    total = sum(Food.query.get(i).price for i in session.get('cart', []))
    return render_template('checkout.html', total=total)

@app.route('/place_order')
def place_order():
    if 'user' not in session:
        return redirect('/login')

    total = sum(Food.query.get(i).price for i in session.get('cart', []))
    db.session.add(Order(user=session['user'], total=total))
    db.session.commit()
    session.pop('cart', None)
    return redirect('/orders')

@app.route('/orders')
def orders():
    orders = Order.query.filter_by(user=session.get('user')).all()
    return render_template('orders.html', orders=orders)

# ---------------- ADMIN ----------------

@app.route('/admin')
def admin():
    foods = Food.query.all()
    return render_template('admin.html', foods=foods)

@app.route('/admin/add', methods=['POST'])
def add_food():
    db.session.add(Food(
        name=request.form['name'],
        price=request.form['price'],
        image=request.form['image']
    ))
    db.session.commit()
    return redirect('/admin')

@app.route('/admin/delete/<int:id>')
def delete_food(id):
    food = Food.query.get_or_404(id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('admin'))

# ---------------- RUN ----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Food.query.first():
            db.session.add(Food(name="Pizza", price=250, image="pizza.jpg"))
            db.session.add(Food(name="Burger", price=150, image="burger.jpg"))
            db.session.add(Food(name="Pasta", price=200, image="pasta.jpg"))
            db.session.add(Food(name="Cold Coffee", price=99, image="coldcoffee.jpg"))
            db.session.add(Food(name="Fries", price=120, image="fries.jpg"))
            db.session.commit()

    app.run(debug=True)