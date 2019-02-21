# Team Charizard NUber Project

For Mr. Diaz's CS 3398 Software Engineering class, we have created a RESTful API which will serve as the backend for our new, ingenius, never-before-thought-of business proposal...NUber

<hr>

### We implemented our backend with the Python3 programming language. This was our technology stack:
- The Flask Microframework
- Flask_RESTful
- Flask_SQLAlchemy
- Flask_Marshmallow
- Flask_Migrate
- Marshmallow_SQLAlchemy

<hr>

### How to run
1. Be sure to have Python3 and Pip installed on your computer
2. Install *virtualenv* with Pip <br>
```pip install virtualenv```
3. *cd* into the project folder and create a virtual environment <br>
```virtualenv -p python3 venv```
4. Activate virtual environment <br>
```source venv/bin/activate```
5. Install all dependencies listed in *requirements.txt* <br>
```pip install -r requirements.txt```
6. Create a binary executable of *create_database.sh* <br>
```chmod 755 create_database.sh```
7. Run *create_database.sh* to make a new instance of your database <br>
```./create_database.sh```
8. RUN DAT BOI:sunglasses:
```python main.py```

### When you spin up the server, you should see output like the following:
```
* Serving Flask app "app" (lazy loading)
* Environment: production
  WARNING: Do not use the development server in a production environment.
  Use a production WSGI server instead.
* Debug mode: on
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
* Restarting with stat
* Debugger is active!
* Debugger PIN: 295-600-791
```
<hr>

### Routes
Below are the available list of routes and their functionalities

#### Admin
- ```/admin/driver```
  - GET: Returns a list of all drivers in the database
    - Arguments: None
  - POST: Creates a new driver
    - Arguments: 
      - id: integer
      - name: string
  - DELETE: Deletes a driver from the database
    - Arguments:
      - id: integer
- blah
