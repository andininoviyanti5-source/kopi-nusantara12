CREATE DATABASE IF NOT EXISTS kopi_nusantara CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kopi_nusantara;

CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(120) NOT NULL,
 email VARCHAR(190) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
 role ENUM('customer','admin') NOT NULL DEFAULT 'customer',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS categories (
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE,
 slug VARCHAR(120) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS products (
 id INT AUTO_INCREMENT PRIMARY KEY, category_id INT NULL,
 name VARCHAR(180) NOT NULL, description TEXT, origin VARCHAR(100),
 roast_level VARCHAR(60), weight VARCHAR(40), price INT NOT NULL,
 stock INT NOT NULL DEFAULT 0, sold INT NOT NULL DEFAULT 0,
 image VARCHAR(255), is_featured TINYINT(1) DEFAULT 0,
 is_active TINYINT(1) DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS carts (
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL UNIQUE,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS cart_items (
 id INT AUTO_INCREMENT PRIMARY KEY, cart_id INT NOT NULL, product_id INT NOT NULL,
 quantity INT NOT NULL DEFAULT 1, UNIQUE KEY uq_cart_product(cart_id,product_id),
 FOREIGN KEY(cart_id) REFERENCES carts(id) ON DELETE CASCADE,
 FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS orders (
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL,
 recipient VARCHAR(120) NOT NULL, phone VARCHAR(30) NOT NULL,
 address TEXT NOT NULL, city VARCHAR(100) NOT NULL, courier VARCHAR(80) NOT NULL,
 shipping_cost INT NOT NULL DEFAULT 0, subtotal INT NOT NULL, total INT NOT NULL,
 payment_method VARCHAR(40) NOT NULL, note TEXT,
 status ENUM('pending','processing','shipped','delivered','cancelled') DEFAULT 'pending',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS order_items (
 id INT AUTO_INCREMENT PRIMARY KEY, order_id INT NOT NULL, product_id INT NULL,
 product_name VARCHAR(180) NOT NULL, price INT NOT NULL, quantity INT NOT NULL,
 FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
 FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS payments (
 id INT AUTO_INCREMENT PRIMARY KEY, order_id INT NOT NULL,
 method VARCHAR(40) NOT NULL, amount INT NOT NULL,
 status ENUM('waiting','paid','failed','refunded') DEFAULT 'waiting',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);

INSERT IGNORE INTO categories(name,slug) VALUES
('Arabika','arabika'),('Robusta','robusta'),('Kopi Siap Minum','kopi-siap-minum'),('Biji Kopi','biji-kopi');

INSERT INTO products(category_id,name,description,origin,roast_level,weight,price,stock,image,is_featured)
SELECT c.id,'Arabika Gayo Premium','Kopi arabika dengan aroma floral, acidity seimbang, dan aftertaste manis. Cocok untuk manual brew.','Aceh','Medium Roast','200 gram',85000,35,'https://images.unsplash.com/photo-1559525839-b184a4d698c7?w=900',1
FROM categories c WHERE c.slug='arabika'
AND NOT EXISTS(SELECT 1 FROM products WHERE name='Arabika Gayo Premium');
INSERT INTO products(category_id,name,description,origin,roast_level,weight,price,stock,image,is_featured)
SELECT c.id,'Robusta Lampung','Karakter bold, body tebal, dan rasa cokelat yang kuat. Cocok untuk espresso dan kopi susu.','Lampung','Dark Roast','200 gram',58000,42,'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=900',1
FROM categories c WHERE c.slug='robusta'
AND NOT EXISTS(SELECT 1 FROM products WHERE name='Robusta Lampung');
INSERT INTO products(category_id,name,description,origin,roast_level,weight,price,stock,image,is_featured)
SELECT c.id,'Toraja Kalosi','Kopi khas pegunungan Toraja dengan aroma rempah dan rasa kompleks.','Sulawesi Selatan','Medium Roast','200 gram',92000,20,'https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=900',1
FROM categories c WHERE c.slug='arabika'
AND NOT EXISTS(SELECT 1 FROM products WHERE name='Toraja Kalosi');
INSERT INTO products(category_id,name,description,origin,roast_level,weight,price,stock,image,is_featured)
SELECT c.id,'Kintamani Bali','Cita rasa segar dengan sentuhan citrus yang khas.','Bali','Light Roast','200 gram',88000,25,'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=900',0
FROM categories c WHERE c.slug='arabika'
AND NOT EXISTS(SELECT 1 FROM products WHERE name='Kintamani Bali');
