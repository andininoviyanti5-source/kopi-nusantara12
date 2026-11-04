import os, re, uuid
from functools import wraps
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.teardown_appcontext(db.close_db)

    @app.before_request
    def load_user():
        g.user = None
        if session.get("user_id"):
            g.user = db.query("SELECT id,name,email,role FROM users WHERE id=%s",
                              (session["user_id"],), one=True)

    @app.context_processor
    def globals():
        count = 0
        if g.get("user") and g.user["role"] == "customer":
            row = db.query("""SELECT COALESCE(SUM(ci.quantity),0) n FROM cart_items ci
                              JOIN carts c ON c.id=ci.cart_id WHERE c.user_id=%s""",
                           (g.user["id"],), one=True)
            count = row["n"] if row else 0
        return {"current_user": g.get("user"), "cart_count": count}

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                flash("Silakan login terlebih dahulu.", "warning")
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)
        return wrapped

    def admin_required(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user["role"] != "admin":
                abort(403)
            return fn(*args, **kwargs)
        return wrapped

    def cart_id():
        row = db.query("SELECT id FROM carts WHERE user_id=%s", (g.user["id"],), one=True)
        if row:
            return row["id"]
        return db.execute("INSERT INTO carts(user_id) VALUES(%s)", (g.user["id"],))

    def money(value):
        return "Rp " + f"{int(value):,}".replace(",", ".")
    app.jinja_env.filters["money"] = money

    @app.route("/")
    def home():
        products = db.query("""SELECT p.*, c.name category_name FROM products p
                               LEFT JOIN categories c ON c.id=p.category_id
                               WHERE p.is_active=1 ORDER BY p.is_featured DESC,p.created_at DESC LIMIT 8""")
        categories = db.query("SELECT * FROM categories ORDER BY name")
        return render_template("index.html", products=products, categories=categories)

    @app.route("/produk")
    def products():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "")
        sort = request.args.get("sort", "newest")
        sql = """SELECT p.*,c.name category_name FROM products p
                 LEFT JOIN categories c ON c.id=p.category_id WHERE p.is_active=1"""
        params = []
        if q:
            sql += " AND (p.name LIKE %s OR p.description LIKE %s)"
            params += [f"%{q}%", f"%{q}%"]
        if category.isdigit():
            sql += " AND p.category_id=%s"; params.append(int(category))
        order = {"price_asc":"p.price ASC","price_desc":"p.price DESC",
                 "popular":"p.sold DESC","newest":"p.created_at DESC"}.get(sort,"p.created_at DESC")
        sql += " ORDER BY " + order
        items = db.query(sql, tuple(params))
        categories = db.query("SELECT * FROM categories ORDER BY name")
        return render_template("products.html", products=items, categories=categories,
                               q=q, selected_category=category, sort=sort)

    @app.route("/produk/<int:product_id>")
    def product_detail(product_id):
        product = db.query("""SELECT p.*,c.name category_name FROM products p
                              LEFT JOIN categories c ON c.id=p.category_id
                              WHERE p.id=%s AND p.is_active=1""", (product_id,), one=True)
        if not product: abort(404)
        related = db.query("SELECT * FROM products WHERE is_active=1 AND id<>%s LIMIT 4", (product_id,))
        return render_template("product_detail.html", product=product, related=related)

    @app.route("/daftar", methods=["GET","POST"])
    def register():
        if request.method == "POST":
            name=request.form.get("name","").strip()
            email=request.form.get("email","").strip().lower()
            password=request.form.get("password","")
            if not name or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                flash("Nama dan email harus diisi dengan benar.", "danger")
            elif len(password)<8:
                flash("Password minimal 8 karakter.", "danger")
            elif db.query("SELECT id FROM users WHERE email=%s",(email,),one=True):
                flash("Email sudah terdaftar.", "danger")
            else:
                uid=db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'customer')",
                               (name,email,generate_password_hash(password)))
                db.execute("INSERT INTO carts(user_id) VALUES(%s)",(uid,))
                session["user_id"]=uid
                flash("Akun berhasil dibuat. Selamat datang!", "success")
                return redirect(url_for("home"))
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            email=request.form.get("email","").strip().lower()
            user=db.query("SELECT * FROM users WHERE email=%s",(email,),one=True)
            if user and check_password_hash(user["password_hash"],request.form.get("password","")):
                session.clear(); session["user_id"]=user["id"]
                flash("Berhasil login.", "success")
                return redirect(url_for("admin_dashboard") if user["role"]=="admin" else url_for("home"))
            flash("Email atau password salah.", "danger")
        return render_template("auth.html", mode="login")

    @app.route("/logout")
    @login_required
    def logout():
        session.clear(); flash("Anda telah logout.", "info")
        return redirect(url_for("home"))

    @app.route("/keranjang")
    @login_required
    def cart():
        cid=cart_id()
        items=db.query("""SELECT ci.id cart_item_id,ci.quantity,p.id product_id,p.name,p.price,
                          p.image,p.stock,(ci.quantity*p.price) subtotal
                          FROM cart_items ci JOIN products p ON p.id=ci.product_id
                          WHERE ci.cart_id=%s""",(cid,))
        total=sum(int(x["subtotal"]) for x in items)
        return render_template("cart.html",items=items,total=total)

    @app.route("/keranjang/tambah/<int:product_id>", methods=["POST"])
    @login_required
    def add_cart(product_id):
        p=db.query("SELECT id,stock FROM products WHERE id=%s AND is_active=1",(product_id,),one=True)
        if not p: abort(404)
        qty=max(1,int(request.form.get("quantity",1)))
        if qty>p["stock"]:
            flash("Jumlah melebihi stok tersedia.","warning")
        else:
            cid=cart_id()
            old=db.query("SELECT id,quantity FROM cart_items WHERE cart_id=%s AND product_id=%s",
                         (cid,product_id),one=True)
            if old:
                new_qty=old["quantity"]+qty
                if new_qty<=p["stock"]:
                    db.execute("UPDATE cart_items SET quantity=%s WHERE id=%s",(new_qty,old["id"]))
                else: flash("Stok tidak mencukupi.","warning")
            else:
                db.execute("INSERT INTO cart_items(cart_id,product_id,quantity) VALUES(%s,%s,%s)",
                           (cid,product_id,qty))
                flash("Produk ditambahkan ke keranjang.","success")
        return redirect(request.referrer or url_for("products"))

    @app.route("/keranjang/update/<int:item_id>", methods=["POST"])
    @login_required
    def update_cart(item_id):
        qty=max(1,int(request.form.get("quantity",1)))
        row=db.query("""SELECT ci.id,p.stock FROM cart_items ci JOIN carts c ON c.id=ci.cart_id
                        JOIN products p ON p.id=ci.product_id
                        WHERE ci.id=%s AND c.user_id=%s""",(item_id,g.user["id"]),one=True)
        if row:
            if qty<=row["stock"]: db.execute("UPDATE cart_items SET quantity=%s WHERE id=%s",(qty,item_id))
            else: flash("Jumlah melebihi stok.","warning")
        return redirect(url_for("cart"))

    @app.route("/keranjang/hapus/<int:item_id>", methods=["POST"])
    @login_required
    def remove_cart(item_id):
        db.execute("""DELETE ci FROM cart_items ci JOIN carts c ON c.id=ci.cart_id
                      WHERE ci.id=%s AND c.user_id=%s""",(item_id,g.user["id"]))
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["GET","POST"])
    @login_required
    def checkout():
        cid=cart_id()
        items=db.query("""SELECT ci.product_id,ci.quantity,p.name,p.price,p.stock
                          FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=%s""",(cid,))
        if not items:
            flash("Keranjang masih kosong.","info"); return redirect(url_for("products"))
        subtotal=sum(int(x["price"])*x["quantity"] for x in items)
        shipping=0 if subtotal>=500000 else 20000
        if request.method=="POST":
            required=["recipient","phone","address","city","courier","payment_method"]
            if any(not request.form.get(k,"").strip() for k in required):
                flash("Lengkapi data checkout.","danger")
            elif any(x["quantity"]>x["stock"] for x in items):
                flash("Stok produk berubah. Periksa keranjang kembali.","warning")
                return redirect(url_for("cart"))
            else:
                total=subtotal+shipping
                oid=db.execute("""INSERT INTO orders(user_id,recipient,phone,address,city,courier,
                                  shipping_cost,subtotal,total,payment_method,note,status)
                                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')""",
                               (g.user["id"],request.form["recipient"],request.form["phone"],
                                request.form["address"],request.form["city"],request.form["courier"],
                                shipping,subtotal,total,request.form["payment_method"],
                                request.form.get("note","")))
                for x in items:
                    db.execute("INSERT INTO order_items(order_id,product_id,product_name,price,quantity) VALUES(%s,%s,%s,%s,%s)",
                               (oid,x["product_id"],x["name"],x["price"],x["quantity"]))
                    db.execute("UPDATE products SET stock=stock-%s,sold=sold+%s WHERE id=%s",
                               (x["quantity"],x["quantity"],x["product_id"]))
                db.execute("INSERT INTO payments(order_id,method,amount,status) VALUES(%s,%s,%s,'waiting')",
                           (oid,request.form["payment_method"],total))
                db.execute("DELETE FROM cart_items WHERE cart_id=%s",(cid,))
                flash("Pesanan berhasil dibuat. Pembayaran masih berupa simulasi.","success")
                return redirect(url_for("orders"))
        return render_template("checkout.html",items=items,subtotal=subtotal,shipping=shipping,total=subtotal+shipping)

    @app.route("/pesanan")
    @login_required
    def orders():
        rows=db.query("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC",(g.user["id"],))
        return render_template("orders.html",orders=rows)

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        stats={
            "products":db.query("SELECT COUNT(*) n FROM products",one=True)["n"],
            "customers":db.query("SELECT COUNT(*) n FROM users WHERE role='customer'",one=True)["n"],
            "orders":db.query("SELECT COUNT(*) n FROM orders",one=True)["n"],
            "revenue":db.query("SELECT COALESCE(SUM(total),0) n FROM orders WHERE status<>'cancelled'",one=True)["n"]
        }
        recent=db.query("SELECT * FROM orders ORDER BY created_at DESC LIMIT 8")
        return render_template("admin.html",stats=stats,orders=recent)

    @app.route("/admin/pesanan/<int:order_id>", methods=["POST"])
    @admin_required
    def admin_order_status(order_id):
        status=request.form.get("status")
        if status not in ("pending","processing","shipped","delivered","cancelled"): abort(400)
        db.execute("UPDATE orders SET status=%s WHERE id=%s",(status,order_id))
        flash("Status pesanan diperbarui.","success")
        return redirect(url_for("admin_dashboard"))

    @app.errorhandler(404)
    def not_found(e): return render_template("error.html",code=404),404
    @app.errorhandler(403)
    def forbidden(e): return render_template("error.html",code=403),403
    @app.errorhandler(413)
    def too_large(e): return render_template("error.html",code=413),413

    return app

app=create_app()
if __name__=="__main__":
    app.run(debug=True)
