# Student Wellness and Counseling Support Database

This Flask project manages:
- Student wellness records
- Counseling appointments and session records
- Anonymous feedback
- Referrals and follow-up actions

## 1. Configure environment variables

Set these before running:

```powershell
$env:FLASK_SECRET_KEY="replace-with-a-long-random-value"
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your-password"
$env:MYSQL_DATABASE="Student_Wellness_DB"
$env:FEEDBACK_SALT="replace-with-a-random-salt"
```

## 2. Create database schema

Run `schema.sql` in MySQL:

```sql
SOURCE D:/student_wellness_system/schema.sql;
```

## 3. Start application

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.




## Contributing
Fork the repository

Create a feature branch

Commit your changes

Push to the branch

Create a Pull Request


## License
This project is licensed under the MIT License - see the LICENSE file for details.