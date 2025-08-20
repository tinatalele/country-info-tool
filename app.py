from flask import Flask, render_template, request, redirect, url_for, session
from services.api_integration import get_country_info, get_famous_places
import csv
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

users = {"testuser": "password123"}
FAV_CSV_FILE = "favorites.csv"



# ==============================
# Routes
# ==============================
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if username in users:
            return render_template("signup.html", error="Username already exists")
        else:
            users[username] = password
            return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/index", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.args.get("clear"):
        session.pop("last_query", None)
        session.pop("region_results", None)

    country_data = None
    is_region = False
    error = None
    page = int(request.args.get("page", 1))
    per_page = 10

    if request.method == "POST":
        query = request.form["query"].strip()
        session["last_query"] = query
        session.pop("region_results", None)
        return redirect(url_for("index", page=1))

    if "last_query" in session:
        query = session["last_query"]

        if "region_results" in session:
            result = session["region_results"]
        else:
            result = get_country_info(query)
            if isinstance(result, list):
                session["region_results"] = result

        if not result:
            error = f"No results found for '{query}'"
            total_pages = 1
        elif isinstance(result, list):
            is_region = True
            total = len(result)
            start = (page - 1) * per_page
            end = start + per_page
            country_data = result[start:end]
            total_pages = (total + per_page - 1) // per_page
        else:
            country_data = result
            total_pages = 1
    else:
        total_pages = 1
        page = 1

    return render_template(
        "index.html",
        country_data=country_data,
        is_region=is_region,
        error=error,
        page=page,
        total_pages=total_pages,
    )


@app.route("/country/<name>")
def getdetail(name):
    result = get_country_info(name)

    if not result:
        return render_template("index.html", error=f"No details found for {name}")

    if isinstance(result, list):
        return render_template("index.html", country_data=result, is_region=True)
    else:
        result["famous_places"] = get_famous_places(result["name"])
        return render_template("index.html", country_data=result, is_region=False)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])




# ==============================
# Favourites feature
# ==============================
@app.route("/add_favourite", methods=["POST"])
def add_favourite():
    if "user" not in session:
        return redirect(url_for("login"))

    country_name = request.form.get("country_name")
    if not country_name:
        return redirect(url_for("index"))

    user = session["user"]

    # Prevent duplicates
    existing = []
    if os.path.isfile(FAV_CSV_FILE):
        with open(FAV_CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user"] == user:
                    existing.append(row["country"])

    if country_name not in existing:
        with open(FAV_CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["user", "country"])
            if os.stat(FAV_CSV_FILE).st_size == 0:
                writer.writeheader()
            writer.writerow({"user": user, "country": country_name})

    return redirect(url_for("favourites"))


@app.route("/favourites")
def favourites():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    fav_countries = []

    if os.path.isfile(FAV_CSV_FILE):
        with open(FAV_CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user"] == user:
                    country_info = get_country_info(row["country"])
                    if not country_info:
                        continue
                    if isinstance(country_info, list):
                        country_info = country_info[0]
                    fav_countries.append(country_info)

    return render_template("favourites.html", favourites=fav_countries)


@app.route("/remove_favourite", methods=["POST"])
def remove_favourite():
    if "user" not in session:
        return redirect(url_for("login"))

    country_name = request.form.get("country_name")
    user = session["user"]
    updated_rows = []

    if os.path.isfile(FAV_CSV_FILE):
        with open(FAV_CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not (row["user"] == user and row["country"] == country_name):
                    updated_rows.append(row)

        with open(FAV_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["user", "country"])
            writer.writeheader()
            writer.writerows(updated_rows)

    return redirect(url_for("favourites"))


# ==============================
# Compare Two Countries
# ==============================
@app.route("/compare", methods=["GET", "POST"])
def compare():
    if "user" not in session:
        return redirect(url_for("login"))

    country1_info = None
    country2_info = None
    error = None

    if request.method == "POST":
        country1_name = request.form.get("country1", "").strip()
        country2_name = request.form.get("country2", "").strip()

        if not country1_name or not country2_name:
            error = "Please enter both country names."
        else:
            country1_info = get_country_info(country1_name)
            country2_info = get_country_info(country2_name)

            if not country1_info or not country2_info:
                error = "One or both countries not found!"
                country1_info = None
                country2_info = None

    return render_template(
        "compare.html",
        country1=country1_info,
        country2=country2_info,
        error=error
    )


# Optional redirects for .html URLs
@app.route("/signup.html")
def signup_html():
    return redirect(url_for("signup"))


@app.route("/login.html")
def login_html():
    return redirect(url_for("login"))


@app.route("/index.html")
def index_html():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)