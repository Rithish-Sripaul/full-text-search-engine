
# File Management System with Full Text Search and User Management


This project is an advanced Document Management System (DMS) designed to streamline document organization, approval, and retrieval processes. It provides robust capabilities like semantic and full-text search, AI-driven summarization, and visual analytics to enhance productivity and document discoverability.

## Features
- #### Categorization of Uploaded Files
  - Efficiently sort and organize documents by attributes like **year**, **division**, **report type**, and more for easy navigation.

- #### Semantic and Full-Text Search
  - Perform both **semantic** and **keyword-based** searches to quickly retrieve information from **PDF** and **Excel** documents.
  
- #### Multi-Level Approval Workflow
  - Admins can **approve**, **deny with feedback**, or **edit** uploaded documents.
  - Ensures a structured and traceable approval process for all submissions.

- #### AI-Driven Summaries and Analytics
  - Automatically generate **summaries** and **abstracts** for PDF content using advanced **AI** and **NLP** tools.
  - Create **visual analytics** from tables and numerical data within documents.

- #### High Performance and Scalability
  - Optimized to handle **100+ real-time concurrent users** with reliability and efficiency.


## Tech Stack

**Frontend:** Bootstrap

**Backend:** Python, Flask, MongoDB, Gunicorn  

**Server:** Docker, Nginx

**AI / NLP:** Integrated tools for summarization and data visualization
## Deployment

To deploy this project locally on flask

```bash
  npm run deploy
```


## Installation and Deployment

- **Clone the Repository**  
  ```bash
  git clone <repository-url>
  cd <project-directory>
  ```

- **Install Dependencies**  
  Ensure you have Python installed, then install the required packages:  
  ```bash
  pip install -r requirements.txt
  ```

- **Set Up MongoDB**  
  - Install and configure MongoDB on your system.  
  - Update the database URI in the project configuration file (`config.py` or equivalent).  
  - You will need to have MONGOSH installed.
  - Once installed open MongoDB Compass and create a new connection, "documentSearchEngine"
  - Inside it, create a new database "testDB"
  - These are the collections you will have to manually create, before beginning the app:
    - users, documents, divisions, reportType, searchHistory
  - Then, you can run it by opening a new terminal with the following command
  ```bash
  mongosh
  ```

- **Run the Application**  
  Start the server locally by opening the directory in terminal:  
  ```bash
  cd app
  flask --app app run --debug
  ```

- **Access the Application**  
  Open your browser and navigate to `http://localhost:5000`.

## Usage/Examples
- **Upload Documents**: Add PDFs or Excel files for processing.
- **Categorize Documents**: Assign metadata for sorting and organization.
- **Search**: Use the search bar to perform semantic or keyword-based queries.
- **Approval Workflow**: Admins can manage document approval with built-in tools.
- **Summaries and Analytics**: View auto-generated summaries and visual insights.



## License

[MIT](https://choosealicense.com/licenses/mit/)

