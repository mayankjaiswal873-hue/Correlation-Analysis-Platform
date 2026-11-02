
import io
import json
import os
import secrets
from pathlib import Path
from functools import wraps

import pandas as pd
import plotly
import plotly.express as px
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
)
from werkzeug.utils import secure_filename

from services.data_generator import generate_data
from services.analysis import analyze_data
from services.insights import generate_insights
from database.db import (
    init_db,
    create_user,
    verify_user,
    save_analysis,
    get_history,
)


# --------------------------------------------------
# 1. APPLICATION CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", secrets.token_hex(32)
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Store datasets on the server instead of in the session cookie.
DATA_DIR = Path(app.root_path) / "instance"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create database tables when the application starts.
init_db()


def current_data_path():
    """Return the current user's dataset file path."""
    return DATA_DIR / f"dataset_user_{session['user_id']}.csv"


# --------------------------------------------------
# 2. LOGIN PROTECTION
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access the dashboard.", "warning")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


# --------------------------------------------------
# 3. DASHBOARD AND ANALYSIS
# --------------------------------------------------

def build_dashboard(data, source):
    """Analyze data and render the interactive dashboard."""

    result = analyze_data(data)
    data = result["data"]
    correlation = result["correlation"]

    # Save the current dataset on the server.
    data.to_csv(current_data_path(), index=False)

    insights = generate_insights(correlation)

    # Choose variables for the scatter plot.
    preferred_columns = ("Study_Hours", "Marks")

    if all(column in data.columns for column in preferred_columns):
        x_column, y_column = preferred_columns
    else:
        x_column, y_column = list(data.columns[:2])

    # Correlation heatmap.
    heatmap = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title="Pearson Correlation Matrix",
    )

    heatmap.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # Scatter plot with a trendline when possible.
    scatter_options = {}

    if data[x_column].nunique() > 1:
        scatter_options["trendline"] = "ols"

    scatter = px.scatter(
        data,
        x=x_column,
        y=y_column,
        title=f"{x_column} vs {y_column}",
        template="plotly_white",
        **scatter_options,
    )

    scatter.update_layout(
        xaxis_title=x_column.replace("_", " "),
        yaxis_title=y_column.replace("_", " "),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # Save a summary of this analysis to SQLite.
    if insights:
        summary = insights[0]["description"]
    else:
        summary = "No reliable correlations could be calculated."

    save_analysis(
        session["user_id"],
        source,
        len(data),
        len(data.columns),
        summary,
    )

    return render_template(
        "index.html",
        username=session.get("username", ""),
        rows=len(data),
        columns=list(data.columns),
        source=source,
        data_table=data.head(10).round(3).to_html(
            index=False,
            classes="data-table",
            border=0,
        ),
        corr_table=correlation.round(2).to_html(
            classes="data-table",
            border=0,
        ),
        heatmap=json.dumps(
            heatmap,
            cls=plotly.utils.PlotlyJSONEncoder,
        ),
        scatter=json.dumps(
            scatter,
            cls=plotly.utils.PlotlyJSONEncoder,
        ),
        insights=insights[:5],
        history=get_history(session["user_id"]),
    )


# --------------------------------------------------
# 4. HOME DASHBOARD
# --------------------------------------------------

@app.route("/")
@login_required
def home():
    """Display the latest dataset or generate a default dataset."""

    saved_path = current_data_path()

    if saved_path.exists():
        try:
            data = pd.read_csv(saved_path)
            result = analyze_data(data)

            # Rebuild dashboard without saving a duplicate history entry.
            data = result["data"]
            correlation = result["correlation"]
            insights = generate_insights(correlation)

            preferred_columns = ("Study_Hours", "Marks")

            if all(column in data.columns for column in preferred_columns):
                x_column, y_column = preferred_columns
            else:
                x_column, y_column = list(data.columns[:2])

            heatmap = px.imshow(
                correlation,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto",
                title="Pearson Correlation Matrix",
            )

            scatter_options = {}

            if data[x_column].nunique() > 1:
                scatter_options["trendline"] = "ols"

            scatter = px.scatter(
                data,
                x=x_column,
                y=y_column,
                title=f"{x_column} vs {y_column}",
                template="plotly_white",
                **scatter_options,
            )

            return render_template(
                "index.html",
                username=session.get("username", ""),
                rows=len(data),
                columns=list(data.columns),
                source="Your saved dataset",
                data_table=data.head(10).round(3).to_html(
                    index=False,
                    classes="data-table",
                    border=0,
                ),
                corr_table=correlation.round(2).to_html(
                    classes="data-table",
                    border=0,
                ),
                heatmap=json.dumps(
                    heatmap,
                    cls=plotly.utils.PlotlyJSONEncoder,
                ),
                scatter=json.dumps(
                    scatter,
                    cls=plotly.utils.PlotlyJSONEncoder,
                ),
                insights=insights[:5],
                history=get_history(session["user_id"]),
            )

        except (
            ValueError,
            KeyError,
            TypeError,
            pd.errors.ParserError,
            UnicodeDecodeError,
        ):
            flash(
                "The saved dataset could not be read. "
                "Generate or upload a new dataset.",
                "warning",
            )

    return build_dashboard(
        generate_data(100, seed=42),
        "Synthetic dataset",
    )


# --------------------------------------------------
# 5. GENERATE SYNTHETIC DATA
# --------------------------------------------------

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    try:
        rows = int(request.form.get("rows", 100))

        if not 20 <= rows <= 1000:
            raise ValueError("Choose between 20 and 1000 rows.")

        data = generate_data(rows)

        return build_dashboard(data, "Synthetic dataset")

    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("home"))


# --------------------------------------------------
# 6. UPLOAD CSV DATASET
# --------------------------------------------------

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    uploaded_file = request.files.get("file")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please choose a CSV file first.", "warning")
        return redirect(url_for("home"))

    if not uploaded_file.filename.lower().endswith(".csv"):
        flash("Only CSV files are supported.", "danger")
        return redirect(url_for("home"))

    try:
        data = pd.read_csv(uploaded_file, nrows=5001)

        if len(data) > 5000:
            raise ValueError("CSV files are limited to 5000 rows.")

        if data.empty:
            raise ValueError("The CSV file has no data.")

        if len(data.columns) > 30:
            raise ValueError("CSV files are limited to 30 columns.")

        data.columns = [str(column).strip() for column in data.columns]

        if any(not column for column in data.columns):
            raise ValueError("Every column must have a name.")

        if data.columns.duplicated().any():
            raise ValueError("Column names must be unique.")

        # Validate that enough usable numeric data exists.
        result = analyze_data(data)

        return build_dashboard(
            result["data"],
            "Uploaded CSV",
        )

    except (
        ValueError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as error:
        flash(f"Could not analyze this file: {error}", "danger")
        return redirect(url_for("home"))


# --------------------------------------------------
# 7. DOWNLOAD CURRENT DATASET
# --------------------------------------------------

@app.route("/download")
@login_required
def download():
    saved_path = current_data_path()

    if not saved_path.exists():
        flash(
            "Generate or upload data before downloading.",
            "warning",
        )
        return redirect(url_for("home"))

    data = pd.read_csv(saved_path)

    output = io.BytesIO(
        data.to_csv(index=False).encode("utf-8")
    )
    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="correlation_dataset.csv",
    )


# --------------------------------------------------
# 8. USER REGISTRATION
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not 3 <= len(username) <= 30:
            flash(
                "Username must contain 3–30 characters.",
                "danger",
            )

        elif len(password) < 8:
            flash(
                "Password must be at least 8 characters.",
                "danger",
            )

        elif password != confirm_password:
            flash("Passwords do not match.", "danger")

        else:
            user_id = create_user(username, password)

            if user_id is None:
                flash(
                    "That username is already registered.",
                    "danger",
                )
            else:
                session.clear()
                session["user_id"] = user_id
                session["username"] = username

                flash(
                    "Account created successfully.",
                    "success",
                )

                return redirect(url_for("home"))

    return render_template("register.html")


# --------------------------------------------------
# 9. USER LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user(username, password)

        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash("Welcome back!", "success")

            return redirect(url_for("home"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# --------------------------------------------------
# 10. USER LOGOUT
# --------------------------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# --------------------------------------------------
# 11. UPLOAD SIZE ERROR HANDLER
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(_error):
    flash("Upload limit is 5 MB.", "danger")
    return redirect(url_for("home"))


# --------------------------------------------------
# 12. START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
