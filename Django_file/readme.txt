set up a link to you database
in mysql create a database named - expensetracker
then settings- line 185-> your mysql username and password

python manage.py makemigrations
python manage.py migrate

python manage.py makemigrations budget
python manage.py migrate budget

python manage.py createsuperuser

fill username, email and password

after creating the superuser 
python manage.py runserver
go to                      http://127.0.0.1:8000/admin 
username = "your superuser username"
password = "your superuser password"

and then add expense category, budget duration, Budget Category, income sources..

then enjoy>>


email account
trackerexpense2@gmail.com

