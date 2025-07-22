# Blogside Story

a simple and elegant blog website built using Flask. This platform allows users to read and post blogs, offering a minimal and functional user experience.

## Features

- Create, edit and delete blog posts
- User authentication (login/register/logout)
- Mobile responsive frontend
- Moduler Flask stucture with Blueprint
- Jinja2 templating with clean using

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS (Bootstrap)
- **Database:** SQLite

## Project Stucture
```
blog website/
|
|---- app/
   |---- auth/
   |---- blog/
   |---- template/
   |---- static/
   |---- models.py
   |---- init.py
|---- config.py
|---- requirements.txt
|---- run.py
|---- README.md
 ```

 ## Setup Instructions

 **1. Clone the repository**
 ```bash
 git clone https://github.com/Yugbhuva/blog_website.git
 cd blog_website
 ```
**2. Create a virtual Environment**
```bash
python -m venv venv
venv\Scripts\activte   # On MacOS: source venv/bin/activate 
```
**3. Install Dependencies**
```bash
pip install -r requirements.txt
```
**4. Run the application**
**4. Start MongoDB**
- Make sure you have MongoDB installed and running locally (default: mongodb://localhost:27017/blog_db)
- Or set the `MONGO_URI` environment variable to your MongoDB connection string.

**5. Run the application**
```bash
python main.py
```
**5.** Visit ```http://127.0.0.1:5000``` in your browser.
**6.** Visit ```http://127.0.0.1:5000``` in your browser.
