# Zylos Backend

This is the backend for the Zylos project.

## Setup and Running

1.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the development server:**
    ```bash
    ./devserver.sh
    ```

## Project Structure

-   **app/**: Main application folder.
    -   **ai/**: AI-related modules.
    -   **api/**: API routes.
    -   **core/**: Core application settings and security.
    -   **database/**: Database models, schemas, and CRUD operations.
    -   **logs/**: Application logs.
    -   **services/**: Business logic and services.
    -   **tests/**: Application tests.
-   **scripts/**: Additional scripts for tasks like database initialization.
-   **requirements.txt**: Project dependencies.
-   **run.sh**: Script to run the application.

## Scripts

-   **scripts/build\_index.py**: Builds the FAISS index for the vector store.
-   **scripts/init\_db.py**: Initializes the database.
-   **scripts/migrate.py**: Handles database migrations.
-   **scripts/train\_lora.py**: Trains the LoRA model.

## API Endpoints

-   **/auth/**: Authentication routes.
-   **/chat/**: Chat and WebSocket routes.
-   **/devices/**: Device management routes.
-   **/memory/**: Memory management routes.
-   **/persona/**: Persona management routes.
