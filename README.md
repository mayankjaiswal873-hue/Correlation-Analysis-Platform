
# CorrelationLab
## Interactive Correlation Analysis Platform for Synthetic Data

### Project Overview
CorrelationLab is a Flask-based web application for generating synthetic
student datasets and exploring relationships between numeric variables.

### Features
- Synthetic dataset generation
- CSV upload and validation
- Pearson correlation matrix
- Interactive Plotly heatmap and scatter plot
- Rule-based correlation insights
- User registration, login and logout
- SQLite analysis history
- CSV dataset download
- Automated unit tests

### Technology Stack
- Python and Flask
- Pandas and NumPy
- Plotly and Statsmodels
- SQLite
- HTML, CSS and JavaScript

### Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Start the application:
   `python app.py`
4. Open `http://127.0.0.1:5000` in your browser.
5. Register an account and open the dashboard.

### Tests
Run:
`python -m unittest discover -s tests -v`

### Limitations
The datasets are synthetic unless a user uploads a CSV.
Automated interpretations are rule-based. Correlation does not establish
causation. This project is intended for local academic demonstration.
