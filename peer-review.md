Hey, here is our peer review. Your project looks like you completed a big part of the requirements of the course, maybe a few things are missing here and there. But the frontend is working as intended and you have all the main functionality implemented. With "bare litt norsk" it was a bit hard to understand the norwegian comments in the code and the readme :D

# Review

### General Architecture

- it looks like you have a monolith architecture, since all logic (routing, database models, background tasks, and business logic) is in a single Python file (main.py)
- the central components seem to be Flask Web Server (for routing and saving user session), PostgreSQL(database), APScheduler(triggers background jobs) and Keycloak (authentication)
- Components interact via direct function calls and shared database access
- Communication with external services (MET.no and OpenStreetMap) via HTTP/REST

### Version Control / Workflow
Everything is in one single repo under version control. It seems to be trunkbased. Commits don't refer to bug tickets, but could be overall features (a bit hard to understand in norwegian). No tags or indicators used for stable versions.

**Is there a backlog or statement stating what features are working what is currently missing?**
Not inside the github repo at least.

### Continuous Integration and Deployment

**Are there test cases for the most central functionality?**
I couldn't find any tests.

**Are there CI-pipelines for each component or the whole application that run the automatically?**
No, the deploy-to-Nrec workflow that runs on push to main for the whole application is just pushing the code without any linting or testing happening. So there automated deployment but without any security.

**Are there Dockerfiles for each component or the whole application that create container images to package the application?**
There is a dockerfile for main.py

**Is the appliation reachable on the web? IP address?**
Yes it is reachable under http://158.39.75.130:8000/mainpage and I was able to authenticate myself as a user, so that worked.

### Functionality

**Does the system comprise a component to automatically fetch weather data from MET?**
Yes. The calculate_weather_data function fetches live data from MET.no.

**Does the system offer a REST API for retrieving the fire risk at a given location?**
Not fully, while it has JSON endpoints like /weather and /history_dates, it is not a "pure" REST API (it uses sessions instead of tokens for some parts and mixes in HTML rendering).

**Does the system comprise all call to the fire risk model `frcm`?**
Yes. It imports frcm and uses frcm.compute(weatherData) to calculate Time to Flashover (TTF).

**Is there functionality that automatically observes the fire risk at given location (i.e. fetches wather data in the background and updates the fire risk continuously)?**
Yes. The BackgroundScheduler is configured to run save_midday_weather and send_daily_notification on a cron-like schedule.

**Perform a system test of all components together: Does it work? What is missing?**
Overall, I was quickly able to start the project on my own computer using docker and it worked as expected or as seen on the live version. I could select a location and see the data for it. However, I thought I was not able to save it under my favorites even though I was logged in as a user. But then I realised that after saving under favorites, you need to refresh the page so it will be shown under favorites. That is not ideal maybe. But the historic data works and it is also nice to see the data for the next few hours. As this is mostly frontend related, everything else seemed to work fine.


### Non-functional requirements

**Does the system use messaging for the communication of two or more components?**
No the messaging seems to be internal mostly or through http.

**Does the system store some information (at least historical wather data) persistently?**
Yes, uses a relational database (PostgreSQL) hosted on AWS RDS

**Is information encrypted in-transfer and/or at-rest? How?**
I wasn't quite sure, it looks like it might be unencrypted. Maybe this is already handled by AWS RDS default encryption, but I couldn't find it in the code.

**Is authentication and authorization implemented for specific system functionality? How?**
Yes, it uses keycloak and authorization is needed to save locations under favorites (or so it seems).

### Notes regarding the project structure

I want to touch on the overall project structure and the fact that all the code was in a single `main.py` file. This is a very bad practice; in your future projects, you should structure the code into multiple files, each handling one specific problem. This, in turn, makes the code more reusable, and if someone wants to make changes to, for example, a database setup, or another team member wants to make changes to the API, there are no conflicts, as the code is separated. Also, separating into files makes them easier to read and understand. The same goes for folder structure: once you create multiple files, put them in the corresponding folders, for example, `db`, `api`, `components`, and so on, depending on the framework/programming language you choose. This will make the project easier to understand, move around, and work with. Since your solution isn't very complex, this might not be a big problem now, but once you start writing projects with thousands of lines of code, you will see the problem.
