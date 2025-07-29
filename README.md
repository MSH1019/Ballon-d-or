## 🏆 Ballon d'Or Project

This is a Django project that manages Ballon d'Or historical data, player profiles, clubs, national teams, and a public voting system.

## Todo: 
- [] TODO: make an if condition to the landing_page player, that if the candidate isn't there, we should use the player img.
- [ ] Search about postgresql
- [ ] Add Pagination to the Landing Page

### ⚠ Database note
The `db.sqlite3` file is **not tracked in Git** (on purpose — it's excluded via `.gitignore`).  

✅ If you clone this repo:
- You'll need to set up your own database by running migrations:
python manage.py migrate

- If you want the historical data:
- You'll need to import it from a CSV or request a copy of the prepared DB.
- (Optional) Contact me to get a `db-after-import-backup.sqlite3` file.

✅ If you're working locally:
- Keep a copy of your DB safe:
cp db.sqlite3 db-backup.sqlite3


### 🛠 How to run locally


---

### 🌟 Future features
- Player profiles with images, linked clubs, and national teams
- Club / NT pages with linked players
- Enhanced vote results views

