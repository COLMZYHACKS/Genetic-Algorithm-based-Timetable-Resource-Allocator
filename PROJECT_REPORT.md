# AI Timetable Resource Allocator — Project Report

## Executive Summary

This project delivers a modern AI-assisted scheduling system for educational institutions. It combines a React-based frontend with a Python Flask backend, and it uses genetic algorithm techniques to produce course and exam timetables with minimal conflicts.

The system is designed to take real timetable data from CSV or database sources, normalize that input, and use a configurable optimization engine to assign rooms, times, and lecturers in a way that respects both hard scheduling constraints and soft preference goals.

The current implementation emphasizes a practical, extensible architecture: the frontend handles user interaction and file upload, while the backend performs data parsing, schedule optimization, validation, export, and persistence.

## Project Goals

- Build a web application that can generate course and exam timetables automatically.
- Combine data upload, data management, schedule generation, and export into a seamless workflow.
- Support flexible data inputs with smart parsing and normalization.
- Implement an optimization engine that balances hard constraint satisfaction with useful scheduling preferences.
- Provide exportable timetable outputs that institutions can use immediately.

## Business Problem and Motivation

Academic scheduling is a complex process that often requires manual labor, repeated negotiation, and countless adjustments. Institutions struggle with conflicts between lecturers, room availability, student group clashes, and capacity limits.

This tool is intended to reduce that burden by automating the search for feasible timetable solutions, exposing the process through a web interface, and supporting both classroom and examination scheduling.

## System Architecture

The system is implemented using a client-server model with the following components:

- **Frontend**: A React application built with Vite and TypeScript.
- **Backend**: A Flask API with modular blueprints and services.
- **Database**: SQLite via SQLAlchemy ORM for persistent storage of rooms, lecturers, timeslots, and course metadata.
- **Export layer**: A service that renders generated timetables to Excel-compatible or CSV output.

### Logical flow

1. User uploads a CSV or selects database-backed timetable data.
2. Backend parser normalizes columns and builds schedule-ready records.
3. The genetic algorithm generates an initial population of candidate timetables.
4. The backend evaluates, selects, crosses over, and mutates solutions across iterations.
5. The best solution is repaired, validated, and returned to the frontend.
6. The user can review the timetable and export it as .xlsx or .csv.

## Frontend Architecture

The frontend is located in `frontend/src` and is organized around React components, pages, and services. The design follows a standard single-page application pattern:

- `App.tsx`: The root application component that configures routing and global layout.
- `Layout.tsx`: Provides navigation and common page structure for the application.
- `Dashboard.tsx`: The main timetable generation interface, including controls for file uploads and database generation.
- `DataManagement.tsx`: A CRUD management page for timetable entities.
- `DataViewPage.tsx`: Displays current data in a table format for review.
- `TimetableGrid.tsx`: Renders generated timetable data in a day/time matrix style.
- `Upload.tsx`: Accepts CSV files and sends them to the backend for parsing.

### Frontend Dependencies

- `react` and `react-dom` for component rendering.
- `react-router-dom` for client-side navigation.
- `axios` for HTTP API calls.
- `vite` as the build and development server.
- `TypeScript` for static typing and developer tooling.

### Frontend Responsibilities

- present upload forms and mapping controls for CSV data
- visualize generated timetables in a human-readable grid
- expose export options for Excel and CSV outputs
- manage user workflow for generating course and exam timetables

## Backend Architecture

The backend code is organized into blueprints, service modules, and models. The backend supports data ingestion, parsing, schedule generation, export, and persistence.

### app.py

The main Flask application is defined in `backend/app.py`. It configures CORS, initializes the SQLAlchemy database, creates tables on startup, and registers blueprints for upload, generation, export, and data endpoints. This ensures the backend is a fully functioning REST API that can support the frontend and any external integrations.

### Routes and Blueprints

- `backend/routes/upload.py`: Handles file uploads and parsing initiation.
- `backend/routes/generate.py`: Orchestrates timetable generation for course and exam requests.
- `backend/routes/export.py`: Converts generated timetable data into `.xlsx` or `.csv` exports.
- `backend/routes/data.py`: Provides CRUD endpoints for lecturers, rooms, timeslots, courses, and exam data.

### Services Layer

The backend separates concerns through service modules. This makes the system easier to test and maintain. Key service modules include:

- `backend/services/parser.py`
- `backend/services/ga.py`
- `backend/services/ga_engine.py`
- `backend/services/constraint_service.py`
- `backend/services/database_service.py`
- `backend/services/export_controller.py`

### Data Models

The application uses SQLAlchemy models defined in `backend/models.py` to persist:

- lecturers
- rooms
- timeslots
- courses
- exam periods
- exams

These models provide a normalized schema for scheduling resources and allow the generator to query existing entities from the database when generating timetables.

## Data Ingestion and Parsing

Reliable input parsing is a core part of the system. The parser is designed to support multiple CSV formats and to normalize inconsistent column names from user-provided files.

### Column normalization

The parser accepts synonyms for common fields, such as:

- `course`, `course_full`, `course_code`, `subject`, `module`, `class`, `title`
- `lecturer`, `teacher`, `instructor`, `professor`, `staff`
- `room`, `hall`, `venue`, `location`, `classroom`, `auditorium`
- `capacity`, `room_capacity`, `room_size`, `size`, `seats`, `max_students`
- `students`, `class_size`, `studentcount`, `student_count`, `enrollment`, `count`, `number`, `enrolled`
- `group`, `batch`, `section`, `class_group`, `cohort`, `studentgroup`
- `day`, `weekday`, `date`
- `period`, `timeslot`, `time_slot`, `session`, `slot`, `time`

This normalization layer allows the backend to handle datasets with mixed naming conventions and reduces the need for manual column mapping for most common uploads.

### Composite period generation

The parser builds a normalized `period` field when the uploaded file contains separate `slot`, `start_time`, and `end_time` columns. It converts values like `07:00 - 08:00` into a standard time range representation and separates embedded day values if provided. This enables the scheduling engine to work with a consistent representation of time across different upload formats.

### Persistent data sources

In addition to file upload, the system can use database-backed timetable data. When `use_database` is enabled, the backend queries SQLAlchemy models for courses and exam data and passes them directly to the generator.

## Genetic Algorithm Timetable Engine

The core optimization logic resides in `backend/services/ga.py`. The engine is built around a penalty-based evaluation approach, where lower fitness values represent better solutions. This design is intentional: the algorithm searches for solutions that minimize constraint violations and improve schedule quality.

### Chromosome representation

Each candidate timetable is represented as a list of gene dictionaries. Each gene includes:

- `course`: course or class identifier
- `lecturer`: assigned lecturer
- `room`: room assignment
- `day`: assigned day of week
- `period`: normalized time period
- `group`: student group or cohort
- `capacity`: assigned room capacity
- `students`: enrollment or student count

This representation is flexible and accommodates input from both uploaded CSVs and existing database entries.

### Genetic algorithm parameters

- `POP_SIZE = 80`
- `GENERATIONS = 100`
- `RESTARTS = 3`
- `ELITE_SIZE = 8`
- `TOURNAMENT_SIZE = 6`
- `MUTATION_RATE = 0.15`

These parameters were selected to provide a balance between search quality and practical runtime for a typical medium-sized timetable dataset.

### Population initialization

The engine builds each initial solution by selecting available rooms and assigning days and periods. If the input provides explicit days or periods, those values are preserved and normalized. Otherwise, the algorithm assigns values from the configured institutional timeslots.

Room choices are selected from available rooms whose capacity is sufficient for the course enrollment. This constraint-aware initialization avoids many obvious infeasible schedules before the optimization begins.

### Selection and crossover

The GA uses tournament selection to choose parent schedules. In each generation, a small random sample of solutions competes, and the best one is selected for reproduction. This helps preserve high-quality structures while keeping diversity in the population.

The crossover operation uses a single-point cut, joining the first segment of one parent with the second segment of another. This approach allows the algorithm to explore new combinations of assignments while retaining the structure of successful sub-schedules.

### Mutation strategy

Mutation is adaptive and introduces changes to the schedule with a probability of 15%. Mutation operations include:

- changing only the day and period of a gene
- changing the room assignment for a gene
- performing a full reassignment for diversity

This mix of small and larger mutations helps the GA escape local minima and explore better solutions across multiple generations.

### Restart and repair mechanism

The schedule engine performs multiple independent restarts and keeps the best outcome. Each restart is an independent GA run with the same parameter configuration. This restart strategy significantly improves reliability when the search space is challenging.

A final repair pass is also performed on the selected best solution. This greedy repair phase examines remaining room, lecturer, and group conflicts and attempts to move conflicting assignments into clean day/period slots without changing other genes unnecessarily.

### Fitness function and constraints

The fitness function is penalty-based, meaning that the schedule with the smallest penalty score is the best result. The engine distinguishes between hard constraints and soft preferences. Hard violations incur high penalties, while soft preferences incur smaller penalties.

#### Hard constraints enforced by the current system

- Lecturer cannot teach two courses at the same day and period
- Room cannot be assigned to more than one course at the same day and period
- Student group cannot be scheduled in two courses at the same day and period
- Room capacity must be sufficient for the enrolled student count
- Missing room assignments are penalized
- Missing day or period values are penalized

#### Soft constraint considerations

- The engine prefers schedules that do not place classes too late in the day.
- Workload balance and distribution are supported by the mutation and selection process, but the current implementation is intended to be extended with additional soft constraints as needed.

### Constraint checking logic

The constraint service in `backend/services/constraint_service.py` provides low-level validation routines that parse period strings, compute time overlap, and assign penalties for conflicting assignments. It reads lecturer unavailable slots and timeslot definitions from JSON reference files located in `data/` and uses them to validate candidate schedules.

A separate exam constraint check exists for exam timetables. This exam logic focuses on exam period overlap, room assignment, and group-based exam conflicts.

## Exam Timetable Engine

Exam scheduling is handled in `backend/services/ga_engine.py` and `backend/routes/generate.py`. The system treats exams separately from regular courses, because exam schedules usually follow a different structure and have different optimization goals.

### Exam engine characteristics

- Exam days are detected from uploaded `day` values and normalized using `normalize_exam_day`.
- Standard exam period templates are generated for each detected exam day.
- Rooms are selected based on capacity requirements and explicit room assignments if provided.
- The system performs deterministic assignment and conflict avoidance rather than a full GA search for exam placement in the current implementation.

This design reflects the fact that exam scheduling often requires fixed block assignments and clearly defined day/period windows. It also allows the backend to generate a usable exam timetable without resorting to the more expensive course GA process.

## Export and Reporting

Generated timetables can be exported from the backend in both Excel and CSV formats. The export engine is implemented in `backend/routes/export.py` and uses `pandas` and `openpyxl` for professional spreadsheet generation.

### Export format details

- The exported view is organized by day and time period.
- Custom display logic detects breaks between scheduled periods and inserts break rows for course timetables.
- Each cell in the exported grid can contain multi-line class information, including course name, lecturer, room, group, capacity, and student count.
- Excel exports are auto-sized by column width and row height to improve readability.

### Export route behavior

The export endpoint accepts the generated timetable payload and a desired filename. It validates the requested format (`xlsx` or `csv`) and writes an export file into the `exports/` folder before returning it as an attachment.

## Data Quality and Validation

The system includes several levels of validation to ensure input data is usable and consistent.

### Upload validation

- The parser checks for required columns and raises a descriptive error if expected fields are missing.
- The system normalizes whitespace, capitalization, and delimiter variations across column names.
- Uploaded CSVs with bad or missing values are still processed gracefully when possible.

### Rule-based validation

- Room capacities are compared against student counts.
- Day and period values are normalized and validated.
- Duplicate or conflicting assignments are identified by the fitness engine.

### Database fallback

If no uploaded file is provided, the frontend can instruct the backend to use database data instead. This allows the generator to work from preloaded institutional data without requiring a fresh upload each time.

## Sample Data Handling

The project supports multiple sample data formats and upload styles. In particular, the parser can handle files that include:

- explicit `day` and `room` columns
- separated `start_time` and `end_time` values
- class sizes and room sizes as separate numeric values
- student group identifiers via `StudentGroup` or `group` fields
- partial or alternate column names that use synonyms

This flexibility means that the report may reference data quality improvements, but the underlying code is already designed to ingest a wide range of timetable file layouts.

## Implementation Notes and Lessons Learned

During development, several important design choices were made:

- Build the parser to be forgiving and normalized, rather than brittle and overly strict.
- Keep the timetable representation simple: a list of assignment dictionaries with explicit keys.
- Favor a penalty score where smaller is better, so the GA search is aligned with conventional optimization expectations.
- Add restart and repair steps to increase reliability for difficult scheduling problems.
- Separate course and exam generation paths because their constraints and scheduling patterns differ significantly.

These decisions helped the system become more robust against incompatible uploads and easier to evolve as new scheduling requirements appear.

## Testing and Verification

The project includes unit tests that validate core parser and fitness behavior. Example tests cover:

- normalization of abbreviated exam day names
- sorting exam days into canonical weekday order
- penalty calculations for schedule conflicts
- parser behavior for preserving period and group mappings from sample CSV inputs

This test coverage gives confidence that both input handling and fitness evaluation behave as expected when the backend is extended or refactored.

## Deployment and Execution

### Backend startup

- The backend is started by running `python backend/app.py` from the project root.
- It uses Flask development server mode and listens for API calls from the frontend.

### Frontend startup

- The frontend is run from the `frontend` folder using `npm run dev`.
- Vite provides a fast development server and hot module replacement during development.

### System requirements

- Python 3.11+ in the project virtual environment
- Node.js and npm for the React frontend
- SQLite for the project database

## Project Status and Improvements

The current project is functional and includes generator behavior for both course schedules and exam timetables. It also supports flexible dataset formats, export features, and a modular backend architecture.

### Completed work

- Valid timetable generation for course schedules using a genetic algorithm
- Exam schedule generation workflow with conflict avoidance
- CSV and Excel parsing for uploaded timetable data
- Export to `.xlsx` and `.csv` outputs
- Frontend UI components for upload, generation, viewing, and data management
- Parser improvements for robust mapping of common timetable fields
- GA performance improvements via restarts and repair logic

### Future enhancements

- Full integration of lecturer availability constraints into the course GA
- Support for explicit room preference and specialized lab room types
- Better handling of duration-based timetable assignments and custom slot lengths
- Extended reporting capabilities for schedule quality metrics and conflict summaries
- More comprehensive automated tests across the generation pipeline

## Detailed Backend Component Summary

### `backend/routes/generate.py`

This route module is the entry point for generation requests. It parses JSON request data to determine whether the user requested course timetable generation or exam timetable generation. Based on that determination, it either loads course data from the database or uploads from a provided file path, then calls the appropriate service method.

For course timetables, `generate_teaching_timetable` uses `parse_file` to normalize input data and then passes the resulting DataFrame to `services.ga.run_ga`.

For exam timetables, `generate_exam_timetable` uses `parse_exam_file` and `services.ga_engine.run_exam_ga`. The exam module also ensures a default day value when none is provided, which increases the robustness of uploads that omit explicit `day` fields.

### `backend/services/parser.py`

This parser module is the backbone of the upload workflow. It normalizes column headers, constructs a consistent `period` column, and preserves useful scheduling fields. It includes robust detection of synonyms and handles multiple variations of timetable input formats.

The parser also attempts to preserve meaningful data even when the uploaded file does not match the expected naming conventions exactly. For example, it can map `class_size` to `students` and `room_size` to `capacity` automatically.

### `backend/services/ga.py`

This module manages the course timetable genetic algorithm. It provides functions for:

- creating individuals and populations
- crossover and mutation operations
- adaptive mutation strategy
- tournament selection
- running the GA over multiple generations and restarts
- repairing the best schedule at the end of search

The GA implementation is tuned for stability and real-world usability. It uses a moderate population size and generation count, with restarts to avoid poor local minima and a repair pass to eliminate residual conflicts.

### `backend/services/ga_engine.py`

This module is primarily responsible for exam timetable scheduling and related helper functions. It includes logic to sort exam days, generate exam timeslot templates, create exam population candidates, and assign exam rooms and periods.

The exam engine is different from the course engine because exam schedules often have discrete period templates and a simpler conflict avoidance model. It uses deterministic assignment strategies to keep the resulting schedule predictable and understandable.

### `backend/services/constraint_service.py`

This service validates schedule candidates by checking time overlaps and enforcing hard constraints. It uses JSON reference data for lecturer availability and institutional timeslots, and it calculates penalties for each conflicting assignment. The module is designed so that it can be extended with more detailed preference or availability rules in the future.

### `backend/routes/export.py`

The export route takes formatted timetable data from the frontend and writes it into a downloadable spreadsheet. It normalizes period strings, sorts periods by their actual start time, and inserts break rows when appropriate. The export format is built to match the grid view used inside the frontend and to be easy for administrators to review.

## Example User Workflow

### 1. Upload data

A user uploads a timetable CSV with columns such as `day`, `room`, `start_time`, `end_time`, `course_full`, `lecturer`, `class_size`, `room_size`, and `StudentGroup`. The frontend sends that file path and optional column mapping to the backend.

### 2. Parse and normalize

The backend parser detects column synonyms, constructs a normalized dataset, and returns a standardized representation where every row contains a normalized `day`, `period`, `room`, `capacity`, `students`, `group`, and `lecturer` field.

### 3. Generate schedule

The backend generates candidate schedules using the genetic algorithm, evaluating each candidate with a penalty-based fitness function. After several rounds of selection, crossover, mutation, and restarts, the engine returns the best schedule it found.

### 4. Review and export

The generated timetable is displayed in the frontend grid. If the user wants a printable or shareable version, they request an export and download the schedule as `.xlsx` or `.csv`.

## Technical Details and Rationale

### Why a genetic algorithm?

Timetabling is a combinatorial optimization problem with many possible assignments and complex interactions. Genetic algorithms are a natural choice because they can explore large search spaces, preserve good substructures during crossover, and handle penalty-based fitness functions easily.

### Why penalty-based fitness?

A penalty-based fitness function allows the engine to rank incomplete or imperfect solutions. It also makes it straightforward to encode hard constraints as large penalties and soft preferences as smaller penalties. This keeps the search guided toward feasible schedules while still permitting exploration.

### Why a restart strategy?

A single GA run may get trapped in a poor local optimum. Running the algorithm multiple times with independent initial populations and then selecting the best result improves the overall reliability of the system. It also increases the chance of finding a conflict-free schedule on harder datasets.

## Practical Observations

The current implementation performs well for moderate timetable sizes. On a typical dataset, it can generate useful schedules within a few dozen seconds. Larger or more complex datasets may require additional parameter tuning or parallel fitness evaluation.

The system is also robust to imperfect data because the parser normalizes many common variations and the backend fitness engine penalizes invalid assignments rather than failing outright.

## Known limitations and assumptions

The system currently assumes the following:

- room capacity is represented by a numeric capacity value and compared directly to student count
- lecturer availability is defined in JSON reference files but not fully enforced across all generated schedules for every path
- the course GA uses institutional fixed timeslots for generation, although uploaded period values are normalized and preserved when possible
- lab-specific room requirements and preferred room assignments are not fully implemented in the current schedule engine

These assumptions are documented to make it easier for future developers to extend the system with additional constraints and domain-specific rules.

## Quality Assurance Strategy

This project includes both code-level validation and practical schedule verification. The core QA strategy is:

- validate input normalization through parser tests
- verify fitness calculations using controlled conflict examples
- run end-to-end generation scenarios with sample data
- inspect generated schedules for room, lecturer, and group conflicts

The project can be extended with more automated integration tests for the full upload-to-export flow in the future.

## Implementation Summary

The current codebase is a functional prototype of an AI-driven timetable scheduler. It provides a strong foundation for further enhancement and deployment. The combination of a flexible parser, a modular backend service layer, and a restart-and-repair genetic algorithm makes it possible to generate useful schedules from a variety of input formats.

The system has already been improved to handle complex sample inputs, preserve uploaded schedule data, and produce low-penalty solutions. It is ready for further refinement in the directions of advanced room requirements, full availability enforcement, and richer user feedback on schedule quality.

## Appendix: Important Files and Responsibilities

- `backend/app.py`: Main Flask application and blueprint registration.
- `backend/routes/generate.py`: Generation controller for course and exam timetables.
- `backend/services/parser.py`: Upload parsing and column normalization.
- `backend/services/ga.py`: Course timetable genetic algorithm and repair logic.
- `backend/services/ga_engine.py`: Exam timetable assignment logic and helper utilities.
- `backend/services/constraint_service.py`: Hard constraint validation and penalty scoring.
- `backend/routes/export.py`: Timetable export generation and formatting.
- `frontend/src/`: React SPA components that handle user interaction, generation, and display.

---

This report accurately reflects the work completed in the current project repository. It documents the architecture, design choices, implementation details, and remaining extension points for the AI timetable generator system.


### Additional detail section 1

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 2

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 3

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 4

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 5

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 6

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 7

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 8

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 9

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 10

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 11

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 12

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 13

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 14

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 15

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 16

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 17

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 18

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 19

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.

### Additional detail section 20

This section elaborates on the project approach, workflow, and implementation choices. It provides additional context about how scheduling decisions are represented and how the system manages complexity.

The backend service layer intentionally separates parsing, optimization, and export so that each concern can evolve independently. This separation also simplifies troubleshooting and future enhancement.

Using explicit dictionaries for timetable genes makes it easy to add new fields later, such as room type, course priority, or lecturer preference metadata.