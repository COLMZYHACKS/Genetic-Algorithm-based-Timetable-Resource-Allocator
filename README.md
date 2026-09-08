# Genetic Algorithm AI TIMETABLE RESOURCE ALLOCATOR

**Author:** Malcolm Nettey (D4RK-D43mon)
**Repository:** [COLMZYHACKS/Genetic-Algorithm-based-Timetable-Resource-Allocator](https://github.com/COLMZYHACKS/Genetic-Algorithm-based-Timetable-Resource-Allocator)

An intelligent AI-powered system for optimizing educational timetables through genetic algorithms. This application automatically allocates lecturers, rooms, and timeslots to create conflict-free, efficient schedules.

## 🚀 Features

- **AI-Powered Optimization**: Uses genetic algorithms for intelligent resource allocation
- **Dual Input Methods**: Upload CSV files or manually manage data through the web interface
- **Real-time Data Management**: Full CRUD operations for lecturers, rooms, timeslots, and courses
- **Interactive Dashboard**: Clean, modern UI for uploading data and generating timetables
- **Data Visualization**: Comprehensive overview of all timetable data
- **Export Functionality**: Export generated timetables to Excel format
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 🏗️ Architecture

### Backend (Python/Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (easily configurable for PostgreSQL/MySQL)
- **AI Engine**: Custom genetic algorithm implementation
- **API**: RESTful endpoints for data management and timetable generation

### Frontend (React/TypeScript)
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Custom CSS with responsive design
- **Routing**: React Router for SPA navigation
- **HTTP Client**: Axios for API communication

## 📋 Prerequisites

Before running this application, ensure you have the following installed:

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **npm**: 8.0 or higher (comes with Node.js)

### Python Dependencies
- Flask
- Flask-CORS
- Flask-SQLAlchemy
- pandas
- numpy
- openpyxl

### Node.js Dependencies
- React
- TypeScript
- Axios
- React Router DOM

## 🛠️ Installation & Setup

### Quick Setup (Recommended)

#### Windows Users
Double-click `setup.bat` or run:
```cmd
setup.bat
```

#### macOS/Linux Users
Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

#### 1. Clone or Download the Repository

```bash
# If cloning from git
git clone <repository-url>
cd timetable_ai

# Or if you received this as a folder, navigate to it
cd path/to/timetable_ai
```

### 2. Backend Setup

#### Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Environment Configuration
The `.env` file in the root directory contains:
```env
DATABASE_URL=sqlite:///timetable.db
SECRET_KEY=your_secret_key
DEBUG=True
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=csv,json
```

**Note**: For production, change `DEBUG=False` and use a strong `SECRET_KEY`.

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

## 🚀 Running the Application

### Development Mode

#### Start Backend Server
```bash
# From the backend directory (with virtual environment activated)
cd backend
python app.py
```
The backend will start on `http://localhost:5000`

#### Start Frontend Development Server
```bash
# From the frontend directory (in a new terminal)
cd frontend
npm run dev
```
The frontend will start on `http://localhost:5173`

### Production Build

#### Build Frontend
```bash
cd frontend
npm run build
```

#### Serve Frontend
```bash
npm run preview
```
The production build will be served on `http://localhost:4173`

## 📁 Project Structure

```
timetable_ai/
├── backend/                    # Python Flask Backend
│   ├── app.py                 # Main Flask application
│   ├── models.py              # SQLAlchemy database models
│   ├── config.py              # Application configuration
│   ├── requirements.txt       # Python dependencies
│   ├── controllers/           # Route controllers
│   │   ├── timetable_controller.py
│   │   ├── export_controller.py
│   │   └── upload_controller.py
│   ├── routes/                # API route definitions
│   │   ├── generate.py
│   │   ├── export.py
│   │   ├── upload.py
│   │   └── data.py
│   ├── services/              # Business logic
│   │   ├── ga_engine.py       # Genetic algorithm engine
│   │   ├── database_service.py
│   │   ├── constraint_service.py
│   │   └── fitness_service.py
│   ├── uploads/               # File upload directory
│   └── utils/                 # Utility functions
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Layout.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DataManagement.tsx
│   │   │   └── DataViewPage.tsx
│   │   ├── pages/             # Page components
│   │   ├── services/          # API service functions
│   │   └── App.tsx            # Main React app
│   ├── package.json
│   └── vite.config.ts
├── data/                      # Sample data files
│   ├── courses.json
│   ├── lecturers.json
│   ├── rooms.json
│   └── timeslots.json
├── tests/                     # Test files
├── OPTIMAL_DATA_GUIDE.md      # Data format guide
├── sample_optimal_timetable.csv
├── small_optimal_sample.csv
└── .env                       # Environment configuration
```

## 📊 API Documentation

### Base URL: `http://localhost:5000`

### Data Management Endpoints

#### Lecturers
- `GET /data/lecturers` - Get all lecturers
- `POST /data/lecturers` - Create new lecturer
- `PUT /data/lecturers/{id}` - Update lecturer
- `DELETE /data/lecturers/{id}` - Delete lecturer

#### Rooms
- `GET /data/rooms` - Get all rooms
- `POST /data/rooms` - Create new room
- `PUT /data/rooms/{id}` - Update room
- `DELETE /data/rooms/{id}` - Delete room

#### Timeslots
- `GET /data/timeslots` - Get all timeslots
- `POST /data/timeslots` - Create new timeslot
- `PUT /data/timeslots/{id}` - Update timeslot
- `DELETE /data/timeslots/{id}` - Delete timeslot

#### Courses
- `GET /data/courses` - Get all courses
- `POST /data/courses` - Create new course
- `PUT /data/courses/{id}` - Update course
- `DELETE /data/courses/{id}` - Delete course

### Timetable Generation
- `POST /timetable/generate` - Generate optimized timetable
  - Body: `{ "path": "file_path", "use_database": boolean }`

### File Upload
- `POST /upload` - Upload CSV file for processing

### Export
- `POST /export` - Export timetable to Excel
  - Body: `{ "timetable": [...] }`

## 🎯 Usage Guide

### 1. Data Preparation

#### Option A: CSV Upload
Prepare a CSV file with the following columns:
```csv
course,lecturer,group,students,capacity,room
CS101,Dr. Smith,CS200,45,50,Lab1
MATH201,Prof. Johnson,MATH300,30,40,HallA
```

See `OPTIMAL_DATA_GUIDE.md` for detailed data format requirements.

#### Option B: Manual Data Entry
Use the "Data Management" page to manually add:
- Lecturers with their unavailable time slots
- Rooms with capacity information
- Timeslots for scheduling
- Courses with enrollment details

### 2. Generate Timetable

1. Go to the Dashboard
2. Either upload a CSV file or select "Use database data"
3. Click "Generate Timetable"
4. Wait for the AI to optimize the schedule
5. View and export the results

### 3. View Data

Use the "Data View" page to see a comprehensive overview of all your data with summary statistics.

## 🔧 Configuration

### Database Configuration
The application uses SQLite by default. To use a different database:

1. Update `DATABASE_URL` in `.env`
2. Install appropriate database driver
3. Run database migrations if needed

### Genetic Algorithm Parameters
Modify parameters in `backend/services/ga_engine.py`:
- Population size
- Mutation rate
- Crossover rate
- Maximum generations

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest test_optimal_data.py -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 🚀 Deployment

### Backend Deployment
```bash
# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend Deployment
```bash
cd frontend
npm run build
# Serve the dist/ folder with any static file server
```

### Docker Deployment (Optional)
Create `Dockerfile` and `docker-compose.yml` for containerized deployment.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all React components
- Write tests for new features
- Update documentation for API changes

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

#### Backend won't start
- Ensure virtual environment is activated
- Check if port 5000 is available
- Verify all dependencies are installed

#### Frontend build fails
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version`

#### Database connection issues
- Ensure SQLite file permissions
- Check DATABASE_URL in .env file

#### CORS errors
- Backend must be running on port 5000
- Frontend development server on port 5173

### Getting Help
- Check the console for error messages
- Review the OPTIMAL_DATA_GUIDE.md for data format issues
- Ensure all prerequisites are installed

## 📈 Performance Tips

- Use smaller datasets for faster generation during development
- Increase GA population size for better optimization (but slower)
- Use database mode for large datasets instead of CSV uploads
- Consider PostgreSQL for production deployments

---

**AI TIMETABLE RESOURCE ALLOCATOR** - Intelligent scheduling for educational institutions.
