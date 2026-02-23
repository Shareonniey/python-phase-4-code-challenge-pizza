#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
from flask import jsonify
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

#Get all restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([r.to_dict(only=("id", "name", "address")) for r in restaurants]), 200

#Get restaurant by id
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
       return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(
        restaurant.to_dict(
            rules=("-restaurant_pizzas.restaurant",)
        )
    ), 200

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
       return jsonify({"error": "Restaurant not found"}), 404
    db.session.delete(restaurant)
    db.session.commit()
    return {}, 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([
        p.to_dict(only=("id", "name", "ingredients"))
        for p in pizzas
    ]), 200

#Create a new restaurant
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    try:
       if not all(k in data for k in ('price', 'pizza_id', 'restaurant_id')):
            return jsonify({"errors": [f"Missing required fields"]}), 400
       price = data["price"]
       restaurant_id = data["restaurant_id"]
       pizza_id = data["pizza_id"]
       if not isinstance(price, int) or price < 1 or price > 30:
           return jsonify({"errors": ["validation errors"]}), 400
       pizza = Pizza.query.get(pizza_id)
       restaurant = Restaurant.query.get(restaurant_id)
       if not pizza or not restaurant:
           return jsonify({"errors": ["Pizza or Restaurant not found"]}), 404

       new_rp = RestaurantPizza(
           price=price,
           restaurant_id=restaurant_id,
           pizza_id=pizza_id
                         )

       db.session.add(new_rp)
       db.session.commit()
       return jsonify({
           "id": new_rp.id,
           "price": new_rp.price,
           "pizza_id": new_rp.pizza_id,
           "restaurant_id": new_rp.restaurant_id,
           "pizza":{
               "id": pizza.id,
               "name": pizza.name,
               "ingredients": pizza.ingredients         
               },
            "restaurant":{
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
                   
               }

       }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400
    except KeyError as e:
        db.session.rollback()
        return jsonify({"errors": [f"Missing field: {str(e)}"]}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400
    
if __name__ == "__main__":
    app.run(port=5555, debug=True)
