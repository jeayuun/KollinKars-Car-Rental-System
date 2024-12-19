# TaskZenith :tulip::purple_heart:
Final Project for COSC 203: DESIGN AND ANALYSIS OF ALGORITHMS - PUP BSCS 2-1N A.Y. 2023-2024

<!-- ABOUT THE PROJECT -->
## ABOUT THE PROJECT
### ***TaskZenith***
> TaskZenith is designed to provide a tool for organizing and prioritizing tasks by making use of the Selection Sort Algorithm, which is well known for its simplicity and effectiveness in handling smaller datasets. It allows users to manage tasks, goals, schedules, and projects effectively, all while ensuring a consistent and visually appealing design. TaskZenith's user interface was developed using HTML, CSS, and JavaScript as its main programming languages in order to provide a responsive and interactive user-friendly application. The back end was developed using Python Flask to handle server-side operations and manage data from the application. The development of TaskZenith highlights the importance of implementing computer science concepts to develop primary solutions that will improve everyday life.

### ***Dashboard***
![Dashboard](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/dashboard.png?raw=true)

## Table of Contents
- [Project Structure](#project-structure)
  - [app.py](#app.py)
  - [helpers.py](#helpers.py)
  - [taskzenith.db](#taskzenith.db)
  - [Templates](#templates)
    - [index.html](#index.html)
    - [dashboard.html](#dashboard.html)
    - [tasks.html](#tasks.html)
    - [goals.html](#goals.html)
    - [schedule.html](#schedule.html)
    - [projects.html](#projects.html)
    - [profile.html](#profile.html)
    - [about.html](#about.html)
- [Static Files](#static-files)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Routes](#routes)
  - [User Authentication](#user-authentication)
  - [Flash Messages](#flash-messages)
  - [Templates](#templates)
  - [Static Files](#static-files-1)
- [Contribution](#contribution)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Project Structure

### app.py
The main application script (back-end). It initializes the Flask application and configures session handling to use the filesystem. The app connects to a SQLite database (`taskzenith.db`) via the CS50 SQL library. It defines various routes for user authentication (register, login, logout) and pages (home, tasks, goals, schedule, projects, profile, about). The register route allows new users to create an account, the login route enables users to log in, and the logout route logs users out of their session. The app uses the `helpers.py` module for additional functionality, such as requiring login for certain routes and displaying error messages.

### helpers.py
Contains utility functions. It includes an `apology` function to render error messages and a `login_required` decorator to restrict access to certain routes unless the user is logged in. This module is imported and used in `app.py` to manage user sessions and handle errors consistently across the application.

### taskzenith.db
The SQLite database file for the application. It stores user data, including usernames and hashed passwords, as well as task, goal, schedule, and project information.

### Templates

#### index.html
Serves as the base template for all other HTML templates in the TaskZenith application. It includes common HTML structure and links to CSS files. This template uses Jinja2 templating to dynamically insert content from other templates, ensuring a consistent look and feel across the site. If the user is not logged in, it also serves as the template for the registration and login pages. It provides forms for users to input their username and password when registering or logging in. The form data is sent to the appropriate route in `app.py` for processing.

#### dashboard.html
The template for the home page, which users see after logging in. It serves as a central hub, displaying an overview of tasks, goals, schedule, and projects.
![Dashboard](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/dashboard.png?raw=true)

#### tasks.html
The template for the tasks management page. It allows users to view, add, and manage their tasks (sort tasks with the use of SELECTION SORT ALGORITHM) within the application.
![Tasks](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/Tasks.png?raw=true)

#### goals.html
The template for the goals management page. It provides an interface for users to set and track their personal or professional goals. Also sorts goals with the use of SELECTION SORT ALGORITHM.
![Goals](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/Goals.png?raw=true)

#### schedule.html
The template for the schedule management page. Users can view and manage their schedules, ensuring they stay on top of their appointments and deadlines. Daily events are scheduled automatically based on time schedule, it utilizes SELECTION SORT ALGORITHM in doing so.
![Schedule](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/Schedule.png?raw=true)

#### projects.html
The template for the projects management page. It allows users to organize and monitor the progress of their projects (sort projects with the use of SELECTION SORT ALGORITHM).
![Projects](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/Projects.png?raw=true)

#### profile.html
The template for the profile page. Users can view and edit their personal information and account settings.
![Profile](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/Profile.png?raw=true)

#### about.html
The template for the about page. It provides information about the people behind TaskZenith application.
![About](https://github.com/jeayuun/TaskZenith/blob/main/Screenshots/About.png?raw=true)

## Static Files

`style.css` and `styles.css` contain the CSS styles for the TaskZenith application. It ensures that all pages have a consistent and visually appealing design.

## Setup Instructions

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/TaskZenith.git
cd TaskZenith
   ```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Set up the database:

Ensure your `taskzenith.db` database file has the correct schema. For example:

```sql
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
hash TEXT NOT NULL
);
```

You can create this schema using a SQLite tool or via command line:

```bash
sqlite3 taskzenith.db < schema.sql  # Assuming you have the schema in a file called schema.sql
```

Run the Flask application:

```bash
flask run
```

The application should now be running on `http://127.0.0.1:1337/`.

## Usage

### Routes

- **Home Page:** `/` - Requires login. Displays the dashboard.
- **Tasks:** `/tasks` - Requires login. Manage your tasks.
- **Goals:** `/goals` - Requires login. Manage your goals.
- **Schedule:** `/schedule` - Requires login. Manage your schedule.
- **Projects:** `/projects` - Requires login. Manage your projects.
- **Profile:** `/profile` - Requires login. View and edit your profile.
- **About:** `/about` - Learn more about TaskZenith.
- **Register:** `/register` - Register a new user.
- **Login:** `/login` - Log in to your account.

### User Authentication

- **Register:** Users can register by providing a username, password, and password confirmation. Passwords must match.
- **Login:** Users can log in with their username and password.

### Flash Messages

Flash messages are used to provide feedback to users (e.g., successful registration, login errors).

### Templates

Templates are located in the `templates` directory and use Jinja2 for rendering dynamic content.

### Static Files

Static files (CSS, images) are located in the `static` directory.

## Contribution

If you'd like to contribute to TaskZenith, please fork the repository and use a feature branch. Pull requests are welcome.

## License

This project is open-source and available under the [MIT License](LICENSE).

## Acknowledgements

This project uses the following libraries:

- Flask
- CS50 Library for SQL
- Werkzeug
