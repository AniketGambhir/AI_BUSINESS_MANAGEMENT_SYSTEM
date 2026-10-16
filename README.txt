AI BUSINESS MANAGEMENT SYSTEM - MID-SEMESTER VERSION
=====================================================

This is the private local version of the project.

It is NOT intended to be deployed publicly.

It uses:
- Flask
- MySQL
- HTML
- CSS
- JavaScript

It does NOT use:
- AI analysis
- scikit-learn
- NumPy
- ai_analysis.py


DATABASE
========

Existing database:

ai_business_management_system


Existing tables:

customer
employee
product
inventory
orders
invoice
project


The application does NOT create a new database.

The application connects to the existing database.


ADMIN
=====

Username:
admin

Password:
admin123


Admin permissions:

Customer       CRUD
Employee       CRUD
Product        CRUD
Inventory      CRUD
Orders         CRUD
Invoice        CRUD
Project        CRUD


USER
====

Username:
user

Password:
user123


User permissions:

Customer       View + Search
Product        View + Search
Orders         View + Search
Project        View + Search


User cannot access:

Employee
Inventory
Invoice


INSTALLATION
============

Create virtual environment:

python -m venv .venv


Activate:

.venv\Scripts\Activate.ps1


Install packages:

pip install -r requirements.txt


DATABASE ENVIRONMENT VARIABLES
=============================

For local MySQL:

$env:DB_HOST="localhost"

$env:DB_PORT="3306"

$env:DB_USER="root"

$env:DB_PASSWORD="YOUR_MYSQL_PASSWORD"

$env:DB_NAME="ai_business_management_system"


Replace YOUR_MYSQL_PASSWORD with your own MySQL password.


RUN
===

python app.py


Open:

http://127.0.0.1:5000


IMPORTANT
=========

Do NOT upload this folder to your public GitHub repository.

Do NOT deploy this folder to Render.

This version is only for your local college mid-semester demonstration.


PROJECT STRUCTURE
=================

AI_BUSINESS_MANAGEMENT_MIDSEM/

    app.py

    database.py

    requirements.txt

    README.txt

    templates/
        login.html
        admin.html
        user.html

    static/
        style.css
        app.js