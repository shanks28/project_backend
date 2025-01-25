# AI for Content Repurposing

This project is an AI-based solution designed to repurpose social media text posts for audiences on different platforms. By leveraging advanced machine learning models, the application transforms content to suit the unique preferences and formats of various social media platforms, thereby enhancing engagement and reach.

## Features

- **Text Repurposing**: Converts social media posts into tailored content optimized for other platforms.
- **FastAPI Backend**: Ensures fast, scalable, and efficient API handling.
- **Google T5 Model**: Utilizes the Google T5 model for state-of-the-art text generation and transformation.
- **OAuth 2.0 Authentication**: Provides secure authentication and authorization using Google OAuth.
- **PostgreSQL Database**: Stores user data and processed content.
- **Dockerized Deployment**: Enables seamless containerized deployment for consistency across environments.

## Technologies Used

- **FastAPI**: Backend API framework.
- **PostgreSQL**: Relational database for storing user data and content.
- **Docker**: Containerization for consistent and scalable deployment.
- **OAuth 2.0**: Secure authentication via Google.
- **Google T5**: Transformer-based model for text repurposing.

## Requirements

Ensure the following are installed:

- Python 3.8+
- Docker
- PostgreSQL
- Github for OAuth 2.0

To install Python dependencies, run:
```bash
pip install -r requirements.txt
```

## Usage

### Steps to Run the Application

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up Environment Variables**:
   Create a `.env` file with the following keys:
   ```env
   DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
   GITHUB_CLIENT_ID=<your-client-id>
   GITHUB_CLIENT_SECRET=<your-client-secret>
   ```

3. **Run the Application with Docker**:
   ```bash
   docker-compose up --build
   ```

4. **Access the API**:
   The application will be accessible at `http://localhost:8000`.

5. **Authenticate via OAuth**:
   Use Google OAuth to securely log in and access features.

6. **Repurpose Content**:
   Submit social media text posts to the API endpoint to receive tailored content for other platforms.


## Project Structure

- `app/`: Contains FastAPI app code.
- `models/`: Holds pre-trained Google T5 model weights and scripts.
- `database/`: PostgreSQL scripts and migrations.
- `docker-compose.yml`: Docker configuration for app and database.
- `requirements.txt`: Python dependencies.
- `README.md`: Project documentation.

## System Design

The system is designed to handle:

1. **User Authentication**:
   - Users authenticate via Github OAuth.
   - Secure tokens ensure access control.

2. **Content Submission**:
   - Users submit social media posts via the API.

3. **Content Processing**:
   - The FastAPI backend leverages the T5 model to repurpose text.

4. **Database Storage**:
   - Original and repurposed content is stored in PostgreSQL for auditing and future reference.

5. **Deployment**:
   - Docker ensures containerized, consistent deployment across environments.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---
