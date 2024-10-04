# Aura Social Media

Aura Social Media is a Flask-based social networking platform that allows users to share posts, like content, and earn Aura points.

## Features

- User authentication (register, login, logout)
- Create and view posts
- Like posts and earn Aura points
- Comment on posts
- User profiles with customizable profile and banner photos
- Trending posts and discover page
- Search functionality for posts and users
- Shop to spend Aura points

## Technologies Used

- Python
- Flask
- SQLAlchemy
- PostgreSQL
- Tailwind CSS
- jQuery

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/aura-social-media.git
   cd aura-social-media
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   flask db upgrade
   ```

5. Run the application:
   ```
   flask run
   ```

6. Open your web browser and navigate to `http://localhost:5000`

## Docker

To run the application using Docker:

1. Build the Docker image:
   ```
   docker build -t aura-social-media .
   ```

2. Run the Docker container:
   ```
   docker run -p 5000:5000 aura-social-media
   ```

3. Open your web browser and navigate to `http://localhost:5000`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)# Aura-Social-Ecommerce
